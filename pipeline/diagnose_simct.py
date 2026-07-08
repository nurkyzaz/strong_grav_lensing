#!/usr/bin/env python
"""
diagnose_simct.py
Inspect the SIMCT ingredients end-to-end and catch the real bugs:
  1. lens-light brightness (peak/sky) vs what real SLACS needs
  2. arc GEOMETRY: rendered arc radius vs theta_E (catches a wrong interpolation default)
  3. arc THICKNESS (radial FWHM) vs real arcs
  4. PSF FWHM in px (catches a PSF sampled at the wrong pixel scale -> over-blur)
  5. resulting arc-to-lens contrast at the current snr settings

Run from ~/cosmos_acs/tiles:
  python diagnose_simct.py
"""
import os, sys
import numpy as np, h5py
from scipy.ndimage import gaussian_filter
from scipy.signal import fftconvolve

REPO = "/home/user/nurkyz/lensfusion"
KAPPA = "/home/user/ckwan1/ml_project/strong_lensing_dataset/kappa_light/train_camera_complete.h5"
SOURCE = "/home/user/ckwan1/ml_project/strong_lensing_dataset/source/galaxies_testset.h5"
PIX, FOV = 128, 6.4
PX = FOV / 127.0


def theta_E_inline(kappa, px):
    """kappa_bar(<r)=1, centred on the (smoothed) kappa peak. Cross-check / fallback."""
    n = kappa.shape[-1]
    pk = np.unravel_index(np.argmax(gaussian_filter(kappa, 1.0)), kappa.shape)
    yy, xx = np.indices(kappa.shape)
    rr = np.hypot(yy - pk[0], xx - pk[1])
    for r in np.arange(1.0, n // 2):
        if kappa[rr < r].mean() < 1.0:
            return r * px, pk, rr
    return np.nan, pk, rr


def radial_profile(img, center):
    yy, xx = np.indices(img.shape)
    rr = np.hypot(yy - center[0], xx - center[1]).astype(int)
    nb = np.bincount(rr.ravel(), img.ravel())
    cnt = np.bincount(rr.ravel())
    return nb / np.maximum(cnt, 1)


def fwhm_px(profile, peak_idx):
    half = profile[peak_idx] / 2.0
    lo = peak_idx
    while lo > 0 and profile[lo] > half:
        lo -= 1
    hi = peak_idx
    while hi < len(profile) - 1 and profile[hi] > half:
        hi += 1
    return hi - lo


def main():
    # ---- 1. lens light ----
    L = h5py.File("elliptical_cutouts.h5", "r")["lens"][:]
    pk = np.percentile(L.reshape(len(L), -1), 99.9, axis=1)
    edge = np.concatenate([L[:, :16].reshape(len(L), -1), L[:, -16:].reshape(len(L), -1)], axis=1)
    sky = 1.4826 * np.median(np.abs(edge - np.median(edge, axis=1, keepdims=True)), axis=1)
    print("1) LENS LIGHT (harvested ellipticals)")
    print(f"   peak/sky: median {np.median(pk/sky):.0f}  (real SLACS lens core ~ hundreds-thousands)")
    print(f"   -> {'TOO FAINT: need rescaling' if np.median(pk/sky) < 100 else 'ok'}")

    # ---- real SLACS reference (if the failure-analysis csv is around) ----
    for ref in ("failure_features_slacs.csv", "~/einstein_cnn/failure_features_slacs.csv"):
        ref = os.path.expanduser(ref)
        if os.path.exists(ref):
            import csv
            rows = list(csv.DictReader(open(ref)))
            cs = np.array([float(r["core_snr"]) for r in rows if r.get("core_snr")])
            print(f"   real SLACS core_snr (peak/sky): median {np.median(cs):.0f}  "
                  f"16-84% [{np.percentile(cs,16):.0f},{np.percentile(cs,84):.0f}]  <- rescale target R")
            break

    # ---- 2-3. arc geometry + thickness ----
    sys.path.insert(0, os.path.join(REPO, "forward_operator"))
    sys.path.insert(0, REPO)
    from physical_model import PhysicalModel
    import torch
    kap_np = h5py.File(KAPPA, "r")["kappa"][0].astype("float32")
    src_np = h5py.File(SOURCE, "r")["galaxies"][0].astype("float32")
    m = PhysicalModel(pixels=PIX, src_pixels=PIX, kappa_pixels=PIX,
                      image_fov=FOV, src_fov=1.5, kappa_fov=FOV, method="fft").eval()
    with torch.no_grad():
        arc = m.lens_source(torch.from_numpy(src_np)[None, None],
                            torch.from_numpy(kap_np)[None, None]).squeeze().cpu().numpy()

    tE, pk_kap, rr = theta_E_inline(kap_np, PX)
    bright = arc > 0.3 * arc.max()
    r_arc = float((rr[bright]).mean() * PX) if bright.any() else float("nan")
    prof = radial_profile(arc, pk_kap)
    ppk = int(np.argmax(prof[2:]) + 2)
    thick_px = fwhm_px(prof, ppk)
    print("\n2) ARC GEOMETRY")
    print(f"   theta_E (kappa_bar=1)   = {tE:.2f}\"")
    print(f"   rendered arc mean radius = {r_arc:.2f}\"")
    ratio = r_arc / tE if tE else float("nan")
    print(f"   ratio arc_radius/theta_E = {ratio:.2f}  "
          f"-> {'OK (geometry sound)' if 0.7 < ratio < 1.4 else 'BAD: arc not tracking theta_E (interp default?)'}")
    print("\n3) ARC THICKNESS")
    print(f"   radial FWHM of arc = {thick_px} px = {thick_px*PX:.2f}\"  "
          f"(real arcs ~0.1-0.4\"; >0.6\" = too thick -> smaller src_fov or PSF issue)")

    # ---- 4. PSF ----
    psf = np.load("acs_psf.npy").astype(np.float32)
    pc = np.unravel_index(psf.argmax(), psf.shape)
    pfw = fwhm_px(psf[pc[0]], pc[1])
    print("\n4) PSF")
    print(f"   shape {psf.shape}, FWHM ~ {pfw} px = {pfw*PX:.2f}\" at 0.05\"/px")
    ok = "ok (~0.1 arcsec)" if pfw <= 3 else "TOO WIDE: PSF sampled at a finer scale -> over-blurs the arc"
    print("   ->", ok)

    # ---- 5. current contrast ----
    print("\n5) CURRENT CONTRAST (why the preview looks wrong)")
    print(f"   arc snr 5-40 vs lens peak/sky ~{np.median(pk/sky):.0f}  ->  arc/lens ~ "
          f"{5/np.median(pk/sky):.2f}-{40/np.median(pk/sky):.2f}  (real ~0.01-0.1)")
    print("   => arc currently rivals the lens; real lenses are far brighter than these field galaxies.")


if __name__ == "__main__":
    main()
