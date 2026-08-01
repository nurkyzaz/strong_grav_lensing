#!/usr/bin/env python
"""Path B: deflector-light library from the real non-lens LRG cutouts.

v5 (2026-07-09, root-cause fix for the 'frame' artifact family):
The v2 radial taper cut light to zero mid-frame -> circular edge. The v4
"NO taper" version still multiplied by a linear opacity ramp reaching 0 at
r=64 px -> (a) a softer but still visible circular boundary against the noisy
backdrop, (b) photometric distortion everywhere (light at r=32 px halved).

v5 principle: NO opacity ramp of any kind inside the frame. Real deflector
light fills the whole cutout and fades below sky naturally; after corner-based
background subtraction the stamp is ~0 at the corners BY CONSTRUCTION, so the
paste has no seam anywhere and the profile is untouched.

Cleaning (the only processing):
1. reject cutouts with blank/chip-edge regions (zero/NaN fraction);
2. background-subtract (corner boxes) + recentre (mode='nearest');
3. neighbour removal: base = 15px median filter of the galaxy (preserves
   ellipticity; erases compact sources); detect compact positives in
   (g - base), replace ONLY those pixels with base;
4. reject stamps where a detected component is long+thin (satellite trail /
   diffraction spike crossing the galaxy - not fixable by replacement);
5. noise suppression in the sky-dominated outskirts: cross-fade real pixels ->
   (median+gaussian)-smoothed version between r=0.12n and 0.35n (smoothstep).
   This changes NOISE, not the mean profile -> no visible transition;
6. keep the faint / axis-ratio selections; optional --drop for visual pruning.
"""
import argparse
import os

import h5py
import numpy as np
from scipy.ndimage import (gaussian_filter, median_filter, shift as ndi_shift,
                           label, find_objects, binary_dilation)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--inp", default=os.path.expanduser("~/einstein_cnn/real_lrgdefl_images.h5"))
    ap.add_argument("--out", default="deflector_stamps_lrg_v3.h5")
    ap.add_argument("--min_q", type=float, default=0.5)
    ap.add_argument("--min_peak_snr", type=float, default=15.0)
    ap.add_argument("--max_blank_frac", type=float, default=0.02,
                    help="reject cutouts with more zero/NaN pixels than this (chip edges)")
    ap.add_argument("--det_sig", type=float, default=1.0,
                    help="neighbour detection threshold on the 1.5px-smoothed residual, "
                         "in units of the raw per-pixel sky sigma (~5 sigma smoothed)")
    ap.add_argument("--trail_aspect", type=float, default=4.0,
                    help="reject stamp if a detected component's bbox aspect exceeds this "
                         "and its long side exceeds 0.4n (satellite trail / spike)")
    ap.add_argument("--xfade_in", type=float, default=0.12,
                    help="fraction of n where the real->smooth noise cross-fade begins")
    ap.add_argument("--xfade_out", type=float, default=0.35,
                    help="fraction of n where pixels are fully the smoothed version")
    ap.add_argument("--drop", type=int, nargs="*", default=[],
                    help="input indices to drop after visual inspection")
    ap.add_argument("--keep_csv", default=None,
                    help="prune-decision CSV: only input names with "
                         "<keep_col>=1 pass (C29: g1b consumes keep_final)")
    ap.add_argument("--keep_col", default="keep_final")
    ap.add_argument("--keep_id_col", default="stamp_id")
    a = ap.parse_args()

    with h5py.File(a.inp, "r") as f:
        imgs = f["images"][:].astype("float32")
        names = None
        if "names" in f:
            names = [x.decode() if hasattr(x, "decode") else str(x)
                     for x in f["names"][:]]

    keep_names = None
    if a.keep_csv:
        import csv as _csv
        if names is None:
            raise SystemExit("--keep_csv needs a 'names' dataset in --inp")
        keep_names = {r[a.keep_id_col] for r in _csv.DictReader(open(a.keep_csv))
                      if r[a.keep_col].strip() == "1"}
        print(f"keep_csv {a.keep_csv}: {len(keep_names)} names with "
              f"{a.keep_col}=1 (input h5 has {len(names)})")
    if imgs.ndim == 4:
        imgs = imgs[:, 0]
    n = imgs.shape[1]
    c = n // 2
    yy, xx = np.mgrid[0:n, 0:n]
    r = np.hypot(yy - c, xx - c)

    kept, kept_src = [], []
    reasons = {"faint": 0, "q": 0, "blank_edge": 0, "trail": 0, "dropped": 0,
               "empty": 0, "pruned": 0}
    for idx, im in enumerate(imgs):
        if idx in a.drop:
            reasons["dropped"] += 1
            continue
        if keep_names is not None and names[idx] not in keep_names:
            reasons["pruned"] += 1
            continue
        bad = ~np.isfinite(im) | (im == 0.0)
        if bad.mean() > a.max_blank_frac:
            reasons["blank_edge"] += 1
            continue
        im = np.where(np.isfinite(im), im, 0.0)

        s = n // 8
        corners = np.concatenate([im[:s, :s].ravel(), im[:s, -s:].ravel(),
                                  im[-s:, :s].ravel(), im[-s:, -s:].ravel()])
        bg, sig = np.median(corners), corners.std() + 1e-9
        g = im - bg

        gsm = gaussian_filter(np.clip(g, 0, None), 2.0)
        win = r < n * 0.18
        if (gsm * win).max() < a.min_peak_snr * sig:
            reasons["faint"] += 1
            continue
        by, bx = np.unravel_index((gsm * win).argmax(), gsm.shape)
        g = ndi_shift(g, (c - by, c - bx), order=1, mode="nearest")

        # --- neighbour removal (ellipticity-preserving) ---
        base = median_filter(g, size=15)
        resid_sm = gaussian_filter(g - base, 1.5)
        det = (resid_sm > a.det_sig * sig) & (r > 0.06 * n)
        # satellite-trail / spike rejection BEFORE dilation (shape test)
        lab, nl = label(det)
        trail = False
        for sl in find_objects(lab):
            if sl is None:
                continue
            h_, w_ = sl[0].stop - sl[0].start, sl[1].stop - sl[1].start
            long_, short_ = max(h_, w_), min(h_, w_)
            if long_ > 0.4 * n and long_ / max(short_, 1) > a.trail_aspect:
                trail = True
                break
        if trail:
            reasons["trail"] += 1
            continue
        det = binary_dilation(det, iterations=2)
        gc = np.where(det, base, g)

        # --- outskirt noise suppression (no profile change, no opacity ramp) ---
        smooth = gaussian_filter(median_filter(gc, size=7), 1.5)
        t = np.clip((r / n - a.xfade_in) / (a.xfade_out - a.xfade_in), 0.0, 1.0)
        beta = t * t * (3 - 2 * t)                       # smoothstep
        clean = (1 - beta) * gc + beta * smooth
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
        kept_src.append(idx)

    kept = np.stack(kept)
    with h5py.File(a.out, "w") as f:
        f.create_dataset("stamps", data=kept)
        f.create_dataset("src_index", data=np.array(kept_src, dtype="int64"))
    print(f"WROTE {len(kept)} neighbour-cleaned deflector stamps "
          f"(v5: no opacity ramp, natural wings) -> {a.out} (of {len(imgs)}); "
          f"rejected {reasons}")


if __name__ == "__main__":
    main()
