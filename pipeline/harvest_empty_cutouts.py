#!/usr/bin/env python
"""
harvest_empty_cutouts.py  (v2 -- high yield)
============================================
Carve EMPTY 128x128 cutouts (6.4" -> 0.05"/px, matching the SLACS test cutouts)
from COSMOS HST/ACS v2.0 F814W tiles.

v2 fixes the near-zero yield of v1:
  - GRID scan (deterministic stride) instead of random sampling.
  - Only the small ARC REGION (central_radius_arcsec, where the arc actually lands)
    must be (a) free of any source and (b) fully covered by the weight map.
  - The rest of the box may contain real neighbours and a few scattered masked
    pixels (up to --max_gap_frac); masked pixels are filled with background noise
    so they look like real sky, not hard zeros.

Each kept cutout is median-subtracted and resampled to 0.05"/px.
Cite when used: Koekemoer et al. 2007 (ApJS 172, 196); Massey et al. 2010 (MNRAS 401, 371).

Usage:
  python harvest_empty_cutouts.py --tiles_dir ~/cosmos_acs/tiles --n 4000 --out empty_cutouts.h5
"""
import argparse, glob, os
import numpy as np, h5py
from astropy.io import fits
from astropy.wcs import WCS
from astropy.stats import sigma_clipped_stats
from scipy.ndimage import zoom


def first_2d(path):
    with fits.open(path, memmap=True) as hdul:
        for h in hdul:
            if h.data is not None and getattr(h.data, "ndim", 0) == 2:
                return np.asarray(h.data, dtype=np.float32), h.header
    raise ValueError(f"no 2D image HDU in {path}")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--tiles_dir", required=True)
    p.add_argument("--out", default="empty_cutouts.h5")
    p.add_argument("--n", type=int, default=4000)
    p.add_argument("--pixel_scale", type=float, default=0.05, help="target arcsec/px")
    p.add_argument("--box_arcsec", type=float, default=6.4)
    p.add_argument("--central_radius_arcsec", type=float, default=1.6,
                   help="arc region that must be source-free AND fully covered")
    p.add_argument("--nsigma", type=float, default=4.0)
    p.add_argument("--max_gap_frac", type=float, default=0.05,
                   help="max fraction of zero-weight pixels allowed OUTSIDE the arc region")
    p.add_argument("--stride_frac", type=float, default=0.5,
                   help="grid stride as fraction of box (0.5 = 2x overlap, more cutouts)")
    p.add_argument("--seed", type=int, default=0)
    a = p.parse_args()
    rng = np.random.default_rng(a.seed)
    target = int(round(a.box_arcsec / a.pixel_scale))  # 128

    sci_tiles = sorted(glob.glob(os.path.join(os.path.expanduser(a.tiles_dir), "*_sci.fits")))
    if not sci_tiles:
        raise SystemExit(f"no *_sci.fits in {a.tiles_dir}")

    out = []
    for sci_path in sci_tiles:
        if len(out) >= a.n:
            break
        wht_path = sci_path.replace("_sci.fits", "_wht.fits")
        sci, hdr = first_2d(sci_path)
        wht = first_2d(wht_path)[0] if os.path.exists(wht_path) else np.ones_like(sci)
        try:
            native = abs(WCS(hdr).proj_plane_pixel_scales()[0].to("arcsec").value)
        except Exception:
            native = 0.03
        box = int(round(a.box_arcsec / native))
        cen = a.central_radius_arcsec / native
        stride = max(1, int(box * a.stride_frac))
        H, W = sci.shape
        c = box // 2
        yy, xx = np.mgrid[:box, :box]
        ap = ((yy - c) ** 2 + (xx - c) ** 2) <= cen ** 2  # arc region mask
        kept_here = 0
        for y in range(0, H - box + 1, stride):
            if len(out) >= a.n:
                break
            for x in range(0, W - box + 1, stride):
                if len(out) >= a.n:
                    break
                sc = sci[y:y + box, x:x + box]
                wc = wht[y:y + box, x:x + box]
                if not np.isfinite(sc).all():
                    continue
                cov = wc > 0
                if not cov[ap].all():               # arc region must sit on real data
                    continue
                if (~cov).mean() > a.max_gap_frac:   # too many gaps elsewhere
                    continue
                vals = sc[cov]
                med, _, std = sigma_clipped_stats(vals, sigma=3.0)
                if std == 0:
                    continue
                if sc[ap].max() > med + a.nsigma * std:  # source in arc region -> not empty
                    continue
                sc2 = (sc - med).copy()
                if (~cov).any():                    # fill scattered gaps with background noise
                    sc2[~cov] = rng.standard_normal(int((~cov).sum())).astype(np.float32) * std
                z = target / box
                cut = zoom(sc2, (z, z), order=1)[:target, :target]
                out.append(cut.astype(np.float32)); kept_here += 1
        print(f"  {os.path.basename(sci_path)} (native {native:.3f}\"/px, stride {stride}px): "
              f"+{kept_here}  total={len(out)}")
        del sci, wht

    if not out:
        raise SystemExit("still no cutouts -- relax --nsigma or --max_gap_frac, or add tiles")
    out = np.stack(out)
    out = out[rng.permutation(len(out))]   # de-correlate the grid order
    with h5py.File(a.out, "w") as f:
        f.create_dataset("empty", data=out)
        f.attrs["pixel_scale"] = a.pixel_scale
        f.attrs["box_arcsec"] = a.box_arcsec
    print(f"\nWROTE {len(out)} empty cutouts -> {a.out} (128x128 @ {a.pixel_scale}\"/px)")


if __name__ == "__main__":
    main()
