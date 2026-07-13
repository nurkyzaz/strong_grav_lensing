#!/usr/bin/env python
"""
make_simct_dataset.py  (calibrated)
===================================
SIMCT generator: clean lensed ARC (Brian's forward operator) painted onto a REAL
elliptical lens-light cutout, raw electrons, test RAW (no subtraction). Fork of
generate_lensed_images_hstempty.py.

Calibrated from diagnose_simct.py (don't change without re-checking):
  - geometry OK (arc radius / theta_E = 1.01), PSF OK (FWHM 0.10").
  - LENS LIGHT: harvested ellipticals are only ~39x sky; real SLACS lens cores are
    ~140x sky (range 93-197, from failure_features_slacs.csv core_snr). You can't fix
    this by scaling the cutout (peak/sky stays 39). So we SEPARATE signal from noise:
        smooth   = gaussian_filter(elliptical)        # galaxy shape, low grain
        noise    = elliptical - smooth                # real correlated noise (unrescaled)
        galaxy   = smooth * (R*sky / smooth_peak)      # rescale ONLY the signal, R~U[93,197]
        comp     = galaxy + noise + arc
    -> lens peak/sky = R (realistic), real noise preserved.
  - ARC THICKNESS: was 0.50" at src_fov 1.5 (real ~0.1-0.4"); thickness ~ src_fov, so
    default src_fov drops to 1.0-1.5 -> ~0.33-0.50". Lower further for thinner arcs.
  - CONTRAST: arc peak = snr*sky, snr~U[5,14] -> arc/lens ~ 0.04-0.10 (real ~0.01-0.1).

Preview first:  python make_simct_dataset.py --n 200 --preview
Then re-diagnose thickness if you change src_fov.
"""
import os, sys, argparse
import h5py, numpy as np, torch
from scipy.signal import fftconvolve
from scipy.ndimage import gaussian_filter


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
                           "source/galaxies_testset.h5",
                   help="use your TRAINING sources here for the real run")
    p.add_argument("--lens_file", default="elliptical_cutouts.h5")
    p.add_argument("--psf_file", default="acs_psf.npy")
    p.add_argument("--out_file", default="lensed_simct.h5")
    p.add_argument("--n", type=int, default=None)
    p.add_argument("--passes", type=int, default=2)
    p.add_argument("--batch_size", type=int, default=64)
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    p.add_argument("--pixels", type=int, default=128)
    p.add_argument("--fov", type=float, default=6.4)
    p.add_argument("--src_fov_list", default="1.0,1.5",
                   help="source size (smaller = thinner arc). 1.5 gave 0.50\"; 1.0 ~0.33\"")
    p.add_argument("--lens_R_lo", type=float, default=93.0, help="lens peak/sky lower (real SLACS)")
    p.add_argument("--lens_R_hi", type=float, default=197.0, help="lens peak/sky upper (real SLACS)")
    p.add_argument("--lens_smooth", type=float, default=2.0, help="px; smooths lens, lifts peak/sky")
    p.add_argument("--snr_min", type=float, default=5.0, help="arc peak/sky lower (detectability)")
    p.add_argument("--snr_max", type=float, default=14.0, help="arc peak/sky upper (arc/lens~0.1)")
    p.add_argument("--preview", action="store_true")
    return p.parse_args()


def build_model(PhysicalModel, pixels, fov, src_fov, device):
    m = PhysicalModel(pixels=pixels, src_pixels=pixels, kappa_pixels=pixels,
                      image_fov=fov, src_fov=src_fov, kappa_fov=fov, method="fft").to(device)
    m.eval()
    return m


def robust_std(a):
    med = np.median(a)
    return 1.4826 * np.median(np.abs(a - med)) + 1e-8


def make_lens(ell, smooth_px, R, rng):
    """Separate signal from noise, rescale ONLY the galaxy signal to peak = R*sky.
    Returns the composited (bright galaxy + real noise) lens image."""
    smooth = gaussian_filter(ell, smooth_px)
    noise = ell - smooth                       # real high-freq correlated noise (unrescaled)
    s_bg = robust_std(noise)
    smooth = np.clip(smooth, 0, None)
    gpeak = np.percentile(smooth, 99.9) + 1e-8
    galaxy = smooth * (R * s_bg / gpeak)        # peak/sky -> R
    return galaxy + noise, s_bg


def main():
    args = parse_args()
    torch.manual_seed(args.seed); np.random.seed(args.seed)
    rng = np.random.default_rng(args.seed)
    device = torch.device(args.device)
    PhysicalModel = load_physical_model_class(args.repo_root)
    src_fov_choices = [float(x) for x in args.src_fov_list.split(",")]

    psf = np.load(args.psf_file).astype(np.float32); psf /= psf.sum()
    with h5py.File(args.lens_file, "r") as fl:
        lens_all = fl["lens"][:].astype(np.float32)
    print(f"[simct] psf{psf.shape} | {len(lens_all)} ellipticals | fov={args.fov} | "
          f"lens peak/sky~U[{args.lens_R_lo:.0f},{args.lens_R_hi:.0f}] | "
          f"arc snr~U[{args.snr_min:.0f},{args.snr_max:.0f}] | src_fov {src_fov_choices}")

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
    d_lidx = fout.create_dataset("lens_index", (N,), dtype="int64")
    d_fov = fout.create_dataset("image_fov", (N,), dtype="float32")
    d_snr = fout.create_dataset("snr", (N,), dtype="float32")
    if has_subid: d_subid = fout.create_dataset("subhalo_id", (N,), dtype="int64")
    if has_camera: d_cam = fout.create_dataset("camera", (N,), dtype=h5py.string_dtype())
    for k, v in vars(args).items():
        fout.attrs[k] = v if isinstance(v, (int, float, str)) else str(v)
    fout.attrs["note"] = ("SIMCT calibrated: ACS-PSF arc on real elliptical (signal/noise "
                          "separated, lens peak/sky~U[93,197]); arc snr~U[5,14]; test RAW")

    write = 0
    preview_imgs = None
    with torch.no_grad():
        for pp in range(args.passes):
            for start in range(0, Nmaps, args.batch_size):
                end = min(start + args.batch_size, Nmaps); b = end - start
                src_fov = float(np.random.choice(src_fov_choices))
                model = build_model(PhysicalModel, args.pixels, args.fov, src_fov, device)

                kap = torch.from_numpy(kappa_ds[start:end].astype("float32")).unsqueeze(1).to(device)
                sidx = np.random.randint(0, Ns, size=b)
                src = torch.from_numpy(src_all[sidx]).unsqueeze(1).to(device)
                arc = model.lens_source(src, kap).squeeze(1).cpu().numpy()

                snr = rng.uniform(args.snr_min, args.snr_max, size=b).astype("float32")
                lidx = rng.integers(0, len(lens_all), size=b)
                comp = np.empty_like(arc)
                for i in range(b):
                    R = rng.uniform(args.lens_R_lo, args.lens_R_hi)
                    lens, s_bg = make_lens(lens_all[lidx[i]], args.lens_smooth, R, rng)
                    a_psf = np.clip(fftconvolve(arc[i], psf, mode="same"), 0, None)
                    a_scaled = a_psf * (snr[i] * s_bg / (a_psf.max() + 1e-8))
                    comp[i] = lens + a_scaled

                sl = slice(write, write + b)
                d_img[sl] = comp
                d_kidx[sl] = np.arange(start, end); d_sidx[sl] = sidx; d_lidx[sl] = lidx
                d_fov[sl] = args.fov; d_snr[sl] = snr
                if has_subid: d_subid[sl] = fk["subhalo_id"][start:end]
                if has_camera: d_cam[sl] = fk["camera"][start:end]
                write += b
                if args.preview and preview_imgs is None:
                    preview_imgs = comp[:8].copy()
                if (start // args.batch_size) % 20 == 0:
                    print(f"  pass {pp+1}/{args.passes}  {end}/{Nmaps}  (src_fov={src_fov})")

    fout.close(); fk.close(); fs.close()
    print(f"[simct] done -> {args.out_file}  ({write} images)")

    if args.preview and preview_imgs is not None:
        import matplotlib; matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots(2, 4, figsize=(12, 6))
        for j, im in enumerate(preview_imgs):
            v = np.arcsinh(im / (robust_std(im) + 1e-8))
            ax.flat[j].imshow(v, origin="lower", cmap="gray")
            ax.flat[j].set_xticks([]); ax.flat[j].set_yticks([])
        fig.suptitle("SIMCT (calibrated): bright elliptical + faint thin arc -- compare to previews/slacs")
        fig.savefig("simct_preview.png", dpi=110, bbox_inches="tight")
        print("wrote simct_preview.png")


if __name__ == "__main__":
    main()
