#!/usr/bin/env python
"""Path B: deflector-light library from the 84 real non-lens LRG cutouts.

v4 (2026-07-08, fixes the 'circle frame'): the frame came from the radial
TAPER CUTTING the (bright) deflector to zero mid/late-frame -> a hard circular
edge. Real deflector light fills the frame and fades smoothly with no cut.
Fix: (1) robust background subtraction, (2) NEIGHBOUR-CLEAN -- replace detected
off-centre sources (companions/blended galaxies) with the azimuthal-median
smooth model so only the smooth central elliptical remains, (3) NO taper (the
smooth galaxy fades naturally to the edge). Injected companions re-add the
field under control. Keep light selection (faint / edge-on / axis-ratio).
"""
import argparse
import os

import h5py
import numpy as np
from scipy.ndimage import gaussian_filter, shift as ndi_shift, label


def azim_model(g, c):
    yy, xx = np.mgrid[0:g.shape[0], 0:g.shape[1]]
    ri = np.hypot(yy - c, xx - c).astype(int)
    rmax = ri.max() + 1
    prof = np.array([np.median(g[ri == k]) if (ri == k).any() else 0.0
                     for k in range(rmax)])
    return prof[np.clip(ri, 0, rmax - 1)], prof


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--inp", default=os.path.expanduser("~/einstein_cnn/real_lrgdefl_images.h5"))
    ap.add_argument("--out", default="deflector_stamps_lrg.h5")
    ap.add_argument("--min_q", type=float, default=0.5)
    ap.add_argument("--min_peak_snr", type=float, default=15.0)
    ap.add_argument("--nbr_nsigma", type=float, default=4.0,
                    help="residual > this*sigma beyond r=12 -> neighbour, cleaned")
    a = ap.parse_args()

    with h5py.File(a.inp, "r") as f:
        imgs = f["images"][:].astype("float32")
    if imgs.ndim == 4:
        imgs = imgs[:, 0]
    n = imgs.shape[1]
    c = n // 2
    yy, xx = np.mgrid[0:n, 0:n]
    r = np.hypot(yy - c, xx - c)

    kept = []
    reasons = {"faint": 0, "q": 0, "empty": 0}
    for im in imgs:
        s = n // 8
        corners = np.concatenate([im[:s, :s].ravel(), im[:s, -s:].ravel(),
                                  im[-s:, :s].ravel(), im[-s:, -s:].ravel()])
        bg, sig = np.median(corners), corners.std() + 1e-9
        g = im - bg
        g[g < 0] = 0.0
        gsm = gaussian_filter(g, 2.0)
        win = r < n * 0.18
        if (gsm * win).max() < a.min_peak_snr * sig:
            reasons["faint"] += 1
            continue
        by, bx = np.unravel_index((gsm * win).argmax(), gsm.shape)
        g = ndi_shift(g, (c - by, c - bx), order=1, mode="constant")
        g[g < 0] = 0.0

        # --- neighbour-clean: replace off-centre sources with the smooth model ---
        model, _ = azim_model(gaussian_filter(g, 2.0), c)
        resid = g - model
        nbr = (resid > a.nbr_nsigma * sig) & (r > 12)
        lab, nl = label(nbr)
        # dilate each neighbour footprint a little and replace with model
        clean = g.copy()
        if nl:
            from scipy.ndimage import binary_dilation
            mask = binary_dilation(nbr, iterations=2) & (r > 10)
            clean[mask] = model[mask]
        clean[clean < 0] = 0.0

        # moment axis ratio (drop edge-on disks)
        gal = r < n * 0.42
        w = clean * gal
        sw = w.sum()
        if sw <= 0:
            reasons["empty"] += 1
            continue
        mmx = (w * xx).sum() / sw
        mmy = (w * yy).sum() / sw
        Ixx = (w * (xx - mmx) ** 2).sum() / sw
        Iyy = (w * (yy - mmy) ** 2).sum() / sw
        Ixy = (w * (xx - mmx) * (yy - mmy)).sum() / sw
        tr = Ixx + Iyy
        disc = max(tr * tr / 4 - (Ixx * Iyy - Ixy ** 2), 0.0)
        l1, l2 = tr / 2 + np.sqrt(disc), tr / 2 - np.sqrt(disc)
        q = np.sqrt(max(l2, 0) / (l1 + 1e-9))
        if q < a.min_q:
            reasons["q"] += 1
            continue

        kept.append(clean.astype("float32"))

    kept = np.stack(kept)
    with h5py.File(a.out, "w") as f:
        f.create_dataset("stamps", data=kept)
    print(f"WROTE {len(kept)} neighbour-cleaned deflector stamps (NO taper) -> "
          f"{a.out} (of {len(imgs)}); rejected {reasons}")


if __name__ == "__main__":
    main()
