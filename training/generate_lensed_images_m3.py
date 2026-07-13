#!/usr/bin/env python
"""MODEL 3 generator: REALISTIC training data = varied FOV + lens light (varied
brightness) + varied noise. Builds on the model-2 generator.

Per image: lens_light x amp (amp ~ U[ll_amp_min, ll_amp_max]; 0 = no lens light, so the
range spans clean->bright), then Gaussian noise with sigma ~ U[sigma_n_min, sigma_n_max].
FOV and src_fov are per BATCH (one PhysicalModel per FOV); amp and sigma are per IMAGE.
Reads the 'lens_light' key from the kappa file (load_lens_light=together).
forward_with_lens_light applies NO amplitude itself, so we scale lens_light here
(LensFusion's source amp = 1.0, lens-light amp ~ 20).

theta_E label is NOT stored here (depends only on the kappa map -> join by kappa_index).
Per-image sigma_n and ll_amp ARE stored, for later error-vs-noise diagnostics."""
import os, sys, argparse
import h5py, numpy as np, torch

def load_physical_model_class(repo_root):
    fwd_dir = os.path.join(repo_root, "forward_operator")
    if fwd_dir not in sys.path:
        sys.path.insert(0, fwd_dir)
    from physical_model import PhysicalModel
    return PhysicalModel

def parse_args():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--repo_root",
                   default="/home/user/ckwan1/ml_project/strong-lensing-sampling")
    p.add_argument("--kappa_file",
                   default="/home/user/ckwan1/ml_project/strong_lensing_dataset/"
                           "kappa_light/train_camera_complete.h5")
    p.add_argument("--source_file",
                   default="/home/user/ckwan1/ml_project/strong_lensing_dataset/"
                           "source/galaxies_testset.h5")
    p.add_argument("--out_file", default="lensed_train_m3.h5")
    p.add_argument("--n", type=int, default=None)
    p.add_argument("--passes", type=int, default=2)
    p.add_argument("--batch_size", type=int, default=64)
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    p.add_argument("--pixels", type=int, default=128)
    p.add_argument("--fov_min", type=float, default=4.0)
    p.add_argument("--fov_max", type=float, default=10.0)
    p.add_argument("--src_fov_list", default="1.5,2.0")
    p.add_argument("--psf_fwhm", type=float, default=0.09)
    p.add_argument("--psf_cutout", type=int, default=19)
    p.add_argument("--ll_amp_min", type=float, default=0.0,
                   help="0 -> some images have ~no lens light (handles subtracted/clean too)")
    p.add_argument("--ll_amp_max", type=float, default=30.0,
                   help="LensFusion fixed value is 20; a range hardens the model")
    p.add_argument("--sigma_n_min", type=float, default=0.01)
    p.add_argument("--sigma_n_max", type=float, default=0.10)
    p.add_argument("--ll_band", type=int, default=0)
    return p.parse_args()

def build_model(PhysicalModel, pixels, fov, src_fov, device):
    model = PhysicalModel(
        pixels=pixels, src_pixels=pixels, kappa_pixels=pixels,
        image_fov=fov, src_fov=src_fov, kappa_fov=fov,
        method="fft", kappa_interp_mode="deflection",
    ).to(device)
    model.eval()
    return model

def main():
    args = parse_args()
    torch.manual_seed(args.seed); np.random.seed(args.seed)
    device = torch.device(args.device)
    PhysicalModel = load_physical_model_class(args.repo_root)
    src_fov_choices = [float(x) for x in args.src_fov_list.split(",")]

    fk = h5py.File(args.kappa_file, "r")
    fs = h5py.File(args.source_file, "r")
    kappa_ds = fk["kappa"]
    if "lens_light" not in fk:
        raise SystemExit(f"ERROR: no 'lens_light' key in {args.kappa_file}. "
                         f"Keys present: {list(fk.keys())}")
    ll_ds = fk["lens_light"]
    print(f"[ll] lens_light shape={ll_ds.shape} dtype={ll_ds.dtype} | "
          f"amp~U[{args.ll_amp_min},{args.ll_amp_max}] sigma~U[{args.sigma_n_min},{args.sigma_n_max}]")

    Nk = kappa_ds.shape[0]
    Nmaps = Nk if args.n is None else min(args.n, Nk)
    src_all = fs["galaxies"][:].astype("float32")
    Ns = src_all.shape[0]
    has_subid = "subhalo_id" in fk
    has_camera = "camera" in fk

    N = Nmaps * args.passes
    fout = h5py.File(args.out_file, "w")
    d_img   = fout.create_dataset("lensed", (N, args.pixels, args.pixels), dtype="float32")
    d_kidx  = fout.create_dataset("kappa_index", (N,), dtype="int64")
    d_sidx  = fout.create_dataset("source_index", (N,), dtype="int64")
    d_fov   = fout.create_dataset("image_fov", (N,), dtype="float32")
    d_sig   = fout.create_dataset("sigma_n", (N,), dtype="float32")
    d_amp   = fout.create_dataset("ll_amp", (N,), dtype="float32")
    if has_subid:
        d_subid = fout.create_dataset("subhalo_id", (N,), dtype="int64")
    if has_camera:
        d_cam = fout.create_dataset("camera", (N,), dtype=h5py.string_dtype())
    for k, v in vars(args).items():
        fout.attrs[k] = v if isinstance(v, (int, float, str)) else str(v)
    fout.attrs["note"] = ("MODEL 3 realistic: varied FOV + lens light (varied amp) + "
                          "varied noise; label = theta_E_pixels[kappa_index]*image_fov/(pixels-1)")

    print(f"[generate-m3] {N} images ({Nmaps} maps x {args.passes} passes) | device={device} | "
          f"fov in [{args.fov_min},{args.fov_max}] | src_fov in {src_fov_choices} | psf={args.psf_fwhm}")

    write = 0
    with torch.no_grad():
        for pp in range(args.passes):
            for start in range(0, Nmaps, args.batch_size):
                end = min(start + args.batch_size, Nmaps)
                b = end - start
                fov = float(np.random.uniform(args.fov_min, args.fov_max))
                src_fov = float(np.random.choice(src_fov_choices))
                model = build_model(PhysicalModel, args.pixels, fov, src_fov, device)
                psf = model.psf_models(args.psf_fwhm, cutout_size=args.psf_cutout).to(device)

                kap = torch.from_numpy(kappa_ds[start:end].astype("float32")).unsqueeze(1).to(device)
                sidx = np.random.randint(0, Ns, size=b)
                src = torch.from_numpy(src_all[sidx]).unsqueeze(1).to(device)

                ll = np.asarray(ll_ds[start:end], dtype="float32")
                if ll.ndim == 4:
                    ll = ll[:, args.ll_band]
                amp = np.random.uniform(args.ll_amp_min, args.ll_amp_max, size=b).astype("float32")
                sig = np.random.uniform(args.sigma_n_min, args.sigma_n_max, size=b).astype("float32")
                amp_t = torch.from_numpy(amp).to(device).view(b, 1, 1, 1)
                sig_t = torch.from_numpy(sig).to(device).view(b, 1, 1, 1)
                ll_t = torch.from_numpy(ll).unsqueeze(1).to(device) * amp_t

                clean = model.forward_with_lens_light(src, kap, ll_t, psf)
                noisy = clean + torch.randn_like(clean) * sig_t

                sl = slice(write, write + b)
                d_img[sl]  = noisy.squeeze(1).cpu().numpy()
                d_kidx[sl] = np.arange(start, end)
                d_sidx[sl] = sidx
                d_fov[sl]  = fov
                d_sig[sl]  = sig
                d_amp[sl]  = amp
                if has_subid:
                    d_subid[sl] = fk["subhalo_id"][start:end]
                if has_camera:
                    d_cam[sl] = fk["camera"][start:end]
                write += b
                if (start // args.batch_size) % 20 == 0:
                    print(f"  pass {pp+1}/{args.passes}  {end}/{Nmaps}  (fov={fov:.2f}, src_fov={src_fov})")

    fout.close(); fk.close(); fs.close()
    print(f"[generate-m3] done -> {args.out_file}  ({write} images)")

if __name__ == "__main__":
    main()
