#!/usr/bin/env python
"""
generate_lensed_images_hstempty.py
==================================
HSTempty generator (Phase 1c). Derived from generate_lensed_images_m3.py.

CHANGE vs m3:
  m3:        arc + (lens_light * amp)  -> Gaussian-PSF (0.09")  -> + white Gaussian noise
  HSTempty:  arc                       -> ACS-PSF (real)        -> painted onto a REAL
                                                                   empty COSMOS cutout
                                                                   (real noise/PSF/neighbours)

NO synthetic lens light (HSTempty images look like a GOOD lens subtraction; at test time
you feed the v2-subtracted SLACS residuals). NO white Gaussian noise (the empty cutout
carries real correlated noise). FOV is FIXED at 6.4" to match the SLACS cutouts and the
empty cutouts (0.05"/px). image_fov=6.4 is stamped on every image, so your existing
labels_train_singleband.h5 + train_cnn_m3.py reconstruct the right arcsec theta_E.

Output format is IDENTICAL to the m3 generator's (keys train_cnn_m3.py reads): 'lensed',
'kappa_index', 'source_index', 'image_fov'. Plus 'snr' for diagnostics.

Run a quick preview first:
  python generate_lensed_images_hstempty.py --n 200 --preview
"""
import os, sys, argparse
import h5py, numpy as np, torch
from scipy.signal import fftconvolve


def load_physical_model_class(repo_root):
    fwd_dir = os.path.join(repo_root, "forward_operator")
    if fwd_dir not in sys.path:
        sys.path.insert(0, fwd_dir)
    from physical_model import PhysicalModel
    return PhysicalModel


def parse_args():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--repo_root", default="/home/user/nurkyz/lensfusion")
    p.add_argument("--kappa_file",
                   default="/home/user/ckwan1/ml_project/strong_lensing_dataset/"
                           "kappa_light/train_camera_complete.h5")
    p.add_argument("--source_file",
                   default="/home/user/ckwan1/ml_project/strong_lensing_dataset/"
                           "source/galaxies_testset.h5")
    p.add_argument("--empty_file", default="empty_cutouts.h5")
    p.add_argument("--psf_file", default="acs_psf.npy")
    p.add_argument("--out_file", default="lensed_hstempty.h5")
    p.add_argument("--n", type=int, default=None)
    p.add_argument("--passes", type=int, default=2)
    p.add_argument("--batch_size", type=int, default=64)
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    p.add_argument("--pixels", type=int, default=128)
    p.add_argument("--fov", type=float, default=6.4, help="FIXED, matches SLACS 6.4\"/128")
    p.add_argument("--src_fov_list", default="1.5,2.0")
    # arc brightness relative to the real background noise of each empty cutout
    p.add_argument("--snr_min", type=float, default=5.0)
    p.add_argument("--snr_max", type=float, default=40.0)
    p.add_argument("--preview", action="store_true", help="save preview PNG of first batch and continue")
    return p.parse_args()


def build_model(PhysicalModel, pixels, fov, src_fov, device):
    m = PhysicalModel(
        pixels=pixels, src_pixels=pixels, kappa_pixels=pixels,
        image_fov=fov, src_fov=src_fov, kappa_fov=fov,
        method="fft", kappa_interp_mode="deflection",
    ).to(device)
    m.eval()
    return m


def robust_std(a):
    med = np.median(a)
    return 1.4826 * np.median(np.abs(a - med)) + 1e-8


def main():
    args = parse_args()
    torch.manual_seed(args.seed); np.random.seed(args.seed)
    rng = np.random.default_rng(args.seed)
    device = torch.device(args.device)
    PhysicalModel = load_physical_model_class(args.repo_root)
    src_fov_choices = [float(x) for x in args.src_fov_list.split(",")]

    psf = np.load(args.psf_file).astype(np.float32); psf /= psf.sum()
    with h5py.File(args.empty_file, "r") as fe:
        empty = fe["empty"][:].astype(np.float32)
    print(f"[hstempty] psf{psf.shape} | {len(empty)} empty cutouts | fov={args.fov} "
          f"(0.05\"/px) | snr~U[{args.snr_min},{args.snr_max}]")

    fk = h5py.File(args.kappa_file, "r")
    fs = h5py.File(args.source_file, "r")
    kappa_ds = fk["kappa"]
    src_all = fs["galaxies"][:].astype("float32"); Ns = src_all.shape[0]
    Nk = kappa_ds.shape[0]
    Nmaps = Nk if args.n is None else min(args.n, Nk)
    has_subid = "subhalo_id" in fk; has_camera = "camera" in fk

    N = Nmaps * args.passes
    fout = h5py.File(args.out_file, "w")
    d_img = fout.create_dataset("lensed", (N, args.pixels, args.pixels), dtype="float32")
    d_kidx = fout.create_dataset("kappa_index", (N,), dtype="int64")
    d_sidx = fout.create_dataset("source_index", (N,), dtype="int64")
    d_fov = fout.create_dataset("image_fov", (N,), dtype="float32")
    d_snr = fout.create_dataset("snr", (N,), dtype="float32")
    if has_subid: d_subid = fout.create_dataset("subhalo_id", (N,), dtype="int64")
    if has_camera: d_cam = fout.create_dataset("camera", (N,), dtype=h5py.string_dtype())
    for k, v in vars(args).items():
        fout.attrs[k] = v if isinstance(v, (int, float, str)) else str(v)
    fout.attrs["note"] = ("HSTempty Phase1c: ACS-PSF arc (no lens light) painted onto real "
                          "empty COSMOS F814W cutouts; FOV fixed 6.4\"; real noise from cutout")

    write = 0
    preview_imgs = []
    with torch.no_grad():
        for pp in range(args.passes):
            for start in range(0, Nmaps, args.batch_size):
                end = min(start + args.batch_size, Nmaps); b = end - start
                src_fov = float(np.random.choice(src_fov_choices))
                model = build_model(PhysicalModel, args.pixels, args.fov, src_fov, device)

                kap = torch.from_numpy(kappa_ds[start:end].astype("float32")).unsqueeze(1).to(device)
                sidx = np.random.randint(0, Ns, size=b)
                src = torch.from_numpy(src_all[sidx]).unsqueeze(1).to(device)

                arc = model.lens_source(src, kap)            # bare arc, no PSF/noise
                arc = arc.squeeze(1).cpu().numpy()           # [b,128,128]

                snr = rng.uniform(args.snr_min, args.snr_max, size=b).astype("float32")
                eidx = rng.integers(0, len(empty), size=b)
                comp = np.empty_like(arc)
                for i in range(b):
                    a_psf = fftconvolve(arc[i], psf, mode="same")
                    a_psf = np.clip(a_psf, 0, None)
                    bg = empty[eidx[i]]
                    s_bg = robust_std(bg)
                    peak = a_psf.max() + 1e-8
                    a_scaled = a_psf * (snr[i] * s_bg / peak)
                    comp[i] = bg + a_scaled

                sl = slice(write, write + b)
                d_img[sl] = comp
                d_kidx[sl] = np.arange(start, end)
                d_sidx[sl] = sidx
                d_fov[sl] = args.fov
                d_snr[sl] = snr
                if has_subid: d_subid[sl] = fk["subhalo_id"][start:end]
                if has_camera: d_cam[sl] = fk["camera"][start:end]
                write += b

                if args.preview and not preview_imgs:
                    preview_imgs = comp[:8].copy()
                if (start // args.batch_size) % 20 == 0:
                    print(f"  pass {pp+1}/{args.passes}  {end}/{Nmaps}  (src_fov={src_fov})")

    fout.close(); fk.close(); fs.close()
    print(f"[hstempty] done -> {args.out_file}  ({write} images)")

    if args.preview and len(preview_imgs):
        import matplotlib; matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots(2, 4, figsize=(12, 6))
        for j, im in enumerate(preview_imgs):
            v = np.arcsinh(im / (robust_std(im) + 1e-8))
            ax.flat[j].imshow(v, origin="lower", cmap="gray")
            ax.flat[j].set_xticks([]); ax.flat[j].set_yticks([])
        fig.suptitle("HSTempty composites (arc on real COSMOS sky) -- eyeball arc visibility")
        fig.savefig("hstempty_preview.png", dpi=110, bbox_inches="tight")
        print("wrote hstempty_preview.png")


if __name__ == "__main__":
    main()
