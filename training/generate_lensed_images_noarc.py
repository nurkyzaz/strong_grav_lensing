#!/usr/bin/env python
"""Lens-light-ONLY ablation. Lens light present; the source is scaled by --src_amp
(default 0.0 = NO ARC). Same seed/FOV/source RNG order as generate_lensed_images_m2_ll.py
and the SAME fixed lens-light amp + noise, so with --seed 42 --n 500 it is paired
image-for-image with test_lenslight_amp20.h5 -- the ONLY difference is the arc.

Run Model 3 on the output: if it STILL predicts theta_E well, the model is reading the
lens GALAXY LIGHT (mass-light correlation), not the lensing arc (the HSC-paper warning)."""
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
                           "kappa_light/test_camera_complete.h5")
    p.add_argument("--source_file",
                   default="/home/user/ckwan1/ml_project/strong_lensing_dataset/"
                           "source/galaxies_testset.h5")
    p.add_argument("--out_file", default="test_noarc_ll20.h5")
    p.add_argument("--n", type=int, default=None)
    p.add_argument("--passes", type=int, default=1)
    p.add_argument("--batch_size", type=int, default=64)
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    p.add_argument("--pixels", type=int, default=128)
    p.add_argument("--fov_min", type=float, default=4.0)
    p.add_argument("--fov_max", type=float, default=10.0)
    p.add_argument("--src_fov_list", default="1.5,2.0")
    p.add_argument("--psf_fwhm", type=float, default=0.09)
    p.add_argument("--psf_cutout", type=int, default=19)
    p.add_argument("--sigma_n", type=float, default=0.01)
    p.add_argument("--lens_light_amp", type=float, default=20.0)
    p.add_argument("--src_amp", type=float, default=0.0,
                   help="0.0 = NO arc (lens light only); 1.0 = normal arc (control)")
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
        raise SystemExit(f"ERROR: no 'lens_light' key in {args.kappa_file}.")
    ll_ds = fk["lens_light"]

    Nk = kappa_ds.shape[0]
    Nmaps = Nk if args.n is None else min(args.n, Nk)
    src_all = fs["galaxies"][:].astype("float32")
    Ns = src_all.shape[0]
    has_subid = "subhalo_id" in fk
    has_camera = "camera" in fk

    N = Nmaps * args.passes
    fout = h5py.File(args.out_file, "w")
    d_img  = fout.create_dataset("lensed", (N, args.pixels, args.pixels), dtype="float32")
    d_kidx = fout.create_dataset("kappa_index", (N,), dtype="int64")
    d_sidx = fout.create_dataset("source_index", (N,), dtype="int64")
    d_fov  = fout.create_dataset("image_fov", (N,), dtype="float32")
    if has_subid:
        d_subid = fout.create_dataset("subhalo_id", (N,), dtype="int64")
    if has_camera:
        d_cam = fout.create_dataset("camera", (N,), dtype=h5py.string_dtype())
    for k, v in vars(args).items():
        fout.attrs[k] = v if isinstance(v, (int, float, str)) else str(v)
    fout.attrs["note"] = (f"ablation: src_amp={args.src_amp} (0=no arc), lens_light_amp="
                          f"{args.lens_light_amp}; label=theta_E_pixels[kappa_index]*fov/(pixels-1)")

    print(f"[noarc] {N} images | src_amp={args.src_amp} | lens_light_amp={args.lens_light_amp} | "
          f"sigma_n={args.sigma_n} | fov[{args.fov_min},{args.fov_max}]")

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
                src = torch.from_numpy(src_all[sidx]).unsqueeze(1).to(device) * args.src_amp

                ll = np.asarray(ll_ds[start:end], dtype="float32")
                if ll.ndim == 4:
                    ll = ll[:, args.ll_band]
                ll_t = torch.from_numpy(ll).unsqueeze(1).to(device) * args.lens_light_amp

                clean = model.forward_with_lens_light(src, kap, ll_t, psf)
                noisy = clean + torch.randn_like(clean) * args.sigma_n

                sl = slice(write, write + b)
                d_img[sl]  = noisy.squeeze(1).cpu().numpy()
                d_kidx[sl] = np.arange(start, end)
                d_sidx[sl] = sidx
                d_fov[sl]  = fov
                if has_subid:
                    d_subid[sl] = fk["subhalo_id"][start:end]
                if has_camera:
                    d_cam[sl] = fk["camera"][start:end]
                write += b

    fout.close(); fk.close(); fs.close()
    print(f"[noarc] done -> {args.out_file}  ({write} images)")

if __name__ == "__main__":
    main()
