#!/usr/bin/env python
"""
generate_lensed_images_hstempty.py  (Phase 1c)
Arc (forward op, NO lens light) -> ACS PSF -> composited onto a REAL empty COSMOS
F814W cutout (real noise/PSF/neighbours). FOV fixed 6.4" (0.05"/px) to match SLACS.

Now stores per-image MAGNIFICATION mu = (lensed flux)/(source flux) so the
"blob, not arc" cases (source away from caustic -> single image; mu~1-2) can be
filtered out from real arcs/rings (mu>~3) with filter_arcs.py. (Brian: these need a
magnification/multiplicity cut; not caught by brightness or theta_E cuts.)

Output keys (train_cnn_m3.py-compatible): lensed, kappa_index, source_index,
image_fov(=6.4), snr, mag.
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
    p.add_argument("--repo_root", default="/home/user/ckwan1/ml_project/strong-lensing-sampling")
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
    p.add_argument("--snr_min", type=float, default=5.0)
    p.add_argument("--snr_max", type=float, default=40.0)
    p.add_argument("--preview", action="store_true")
    return p.parse_args()


def build_model(PhysicalModel, pixels, fov, src_fov, device):
    m = PhysicalModel(
        pixels=pixels, src_pixels=pixels, kappa_pixels=pixels,
        image_fov=fov, src_fov=src_fov, kappa_fov=fov, lens_light_fov=fov,
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
    img_scale = args.fov / (args.pixels - 1)

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
    d_mag = fout.create_dataset("mag", (N,), dtype="float32")
    if has_subid: d_subid = fout.create_dataset("subhalo_id", (N,), dtype="int64")
    if has_camera: d_cam = fout.create_dataset("camera", (N,), dtype=h5py.string_dtype())
    for k, v in vars(args).items():
        fout.attrs[k] = v if isinstance(v, (int, float, str)) else str(v)
    fout.attrs["note"] = ("HSTempty Phase1c: ACS-PSF arc (no lens light) on real empty "
                          "COSMOS F814W cutouts; FOV 6.4\"; mag=(lensed flux)/(source flux)")

    write = 0
    preview_imgs = None
    preview_mag = None
    with torch.no_grad():
        for pp in range(args.passes):
            for start in range(0, Nmaps, args.batch_size):
                end = min(start + args.batch_size, Nmaps); b = end - start
                src_fov = float(np.random.choice(src_fov_choices))
                src_scale = src_fov / (args.pixels - 1)
                model = build_model(PhysicalModel, args.pixels, args.fov, src_fov, device)

                kap = torch.from_numpy(kappa_ds[start:end].astype("float32")).unsqueeze(1).to(device)
                sidx = np.random.randint(0, Ns, size=b)
                src = torch.from_numpy(src_all[sidx]).unsqueeze(1).to(device)

                arc_t = model.lens_source(src, kap)          # [b,1,128,128] bare arc
                arc = arc_t.squeeze(1).cpu().numpy()         # [b,128,128]
                src_flux = src.squeeze(1).sum(dim=(1, 2)).cpu().numpy()  # [b]
                arc_flux = arc.reshape(b, -1).sum(axis=1)               # [b]
                mag = (arc_flux * img_scale**2) / (src_flux * src_scale**2 + 1e-12)  # [b]

                snr = rng.uniform(args.snr_min, args.snr_max, size=b).astype("float32")
                eidx = rng.integers(0, len(empty), size=b)
                comp = np.empty_like(arc)
                for i in range(b):
                    a_psf = fftconvolve(arc[i], psf, mode="same")
                    a_psf = np.clip(a_psf, 0, None)
                    bg = empty[eidx[i]]
                    s_bg = robust_std(bg)
                    peak = a_psf.max() + 1e-8
                    comp[i] = bg + a_psf * (snr[i] * s_bg / peak)

                sl = slice(write, write + b)
                d_img[sl] = comp
                d_kidx[sl] = np.arange(start, end)
                d_sidx[sl] = sidx
                d_fov[sl] = args.fov
                d_snr[sl] = snr
                d_mag[sl] = mag.astype("float32")
                if has_subid: d_subid[sl] = fk["subhalo_id"][start:end]
                if has_camera: d_cam[sl] = fk["camera"][start:end]
                write += b

                if args.preview and preview_imgs is None:
                    preview_imgs = comp[:8].copy()
                    preview_mag = mag[:8].copy()
                if (start // args.batch_size) % 20 == 0:
                    print(f"  pass {pp+1}/{args.passes}  {end}/{Nmaps}  (src_fov={src_fov})")

    fout.close(); fk.close(); fs.close()
    print(f"[hstempty] done -> {args.out_file}  ({write} images)")

    if args.preview and preview_imgs is not None:
        import matplotlib; matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots(2, 4, figsize=(12, 6))
        for j, im in enumerate(preview_imgs):
            v = np.arcsinh(im / (robust_std(im) + 1e-8))
            ax.flat[j].imshow(v, origin="lower", cmap="gray")
            ax.flat[j].set_title(f"mu={preview_mag[j]:.1f}", fontsize=10)
            ax.flat[j].set_xticks([]); ax.flat[j].set_yticks([])
        fig.suptitle("HSTempty composites -- mu=(lensed/source) flux; blobs ~1-2, arcs >~3")
        fig.savefig("hstempty_preview.png", dpi=110, bbox_inches="tight")
        print("wrote hstempty_preview.png (annotated with magnification mu)")


if __name__ == "__main__":
    main()
