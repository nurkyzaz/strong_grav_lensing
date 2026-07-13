#!/usr/bin/env python
"""
harvest_ellipticals.py
======================
Carve cutouts CENTRED on real, bright, concentrated elliptical-like galaxies from the
COSMOS HST/ACS F814W tile(s) -- the lens-light + real-field base for SIMCT. The inverse
of harvest_empty_cutouts.py: instead of rejecting cutouts with a central source, KEEP
the ones whose centre holds a bright, centrally-concentrated, reasonably round galaxy.

Each kept cutout carries the galaxy AND its real surroundings (neighbours, sky, correlated
noise), median-subtracted and resampled to 0.05"/px / 128 px -- so painting a lensed arc on
top yields a realistic lens. Units: ELECTRONS (same as the tile / empty cutouts).

Cite: Koekemoer et al. 2007 (ApJS 172, 196); Massey et al. 2010 (MNRAS 401, 371).

Usage:
  python harvest_ellipticals.py --tiles_dir ~/cosmos_acs/tiles --n 1500 --out elliptical_cutouts.h5
"""
import argparse, glob, os
import numpy as np, h5py
from astropy.io import fits
from astropy.wcs import WCS
from astropy.stats import sigma_clipped_stats
from scipy.ndimage import zoom, gaussian_filter, maximum_filter


def first_2d(path):
    with fits.open(path, memmap=True) as hdul:
        for h in hdul:
            if h.data is not None and getattr(h.data, "ndim", 0) == 2:
                return np.asarray(h.data, dtype=np.float32), h.header
    raise ValueError(f"no 2D image HDU in {path}")


def concentration(stamp, c, r_in_px, r_out_px):
    """flux within r_in / flux within r_out -- high for centrally-concentrated ellipticals."""
    yy, xx = np.indices(stamp.shape)
    rr = np.hypot(yy - c, xx - c)
    f = np.clip(stamp, 0, None)
    fout = f[rr < r_out_px].sum() + 1e-9
    return float(f[rr < r_in_px].sum() / fout)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--tiles_dir", required=True)
    p.add_argument("--out", default="elliptical_cutouts.h5")
    p.add_argument("--n", type=int, default=1500)
    p.add_argument("--pixel_scale", type=float, default=0.05)
    p.add_argument("--box_arcsec", type=float, default=6.4)
    p.add_argument("--peak_nsigma", type=float, default=30.0,
                   help="central source must exceed sky by this many sigma (bright galaxies)")
    p.add_argument("--min_conc", type=float, default=0.35,
                   help="min flux(<0.45\")/flux(<1.5\") -- concentration => early-type-like")
    p.add_argument("--min_sep_arcsec", type=float, default=3.0,
                   help="min separation between kept galaxy centres (dedupe)")
    p.add_argument("--seed", type=int, default=0)
    a = p.parse_args()
    rng = np.random.default_rng(a.seed)
    target = int(round(a.box_arcsec / a.pixel_scale))   # 128

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
        box = int(round(a.box_arcsec / native)); c = box // 2
        r_in = 0.45 / native; r_out = 1.5 / native
        cov = wht > 0
        med, _, std = sigma_clipped_stats(sci[cov], sigma=3.0)

        # detect bright local maxima (galaxy centres)
        sm = gaussian_filter(sci, 2.0)
        peaks = (sm == maximum_filter(sm, size=int(0.6 / native))) & (sci > med + a.peak_nsigma * std)
        ys, xs = np.where(peaks)
        order = np.argsort(sci[ys, xs])[::-1]          # brightest first
        ys, xs = ys[order], xs[order]

        kept_centres = []
        kept_here = 0
        min_sep_px = a.min_sep_arcsec / native
        for yc, xc in zip(ys, xs):
            if len(out) >= a.n:
                break
            if yc - box // 2 < 0 or yc + box // 2 >= sci.shape[0] or \
               xc - box // 2 < 0 or xc + box // 2 >= sci.shape[1]:
                continue
            if any(np.hypot(yc - yy0, xc - xx0) < min_sep_px for yy0, xx0 in kept_centres):
                continue
            sc = sci[yc - c:yc - c + box, xc - c:xc - c + box]
            wc = wht[yc - c:yc - c + box, xc - c:xc - c + box]
            if sc.shape != (box, box) or not np.isfinite(sc).all():
                continue
            if (wc[c - int(r_out):c + int(r_out), c - int(r_out):c + int(r_out)] <= 0).mean() > 0.05:
                continue
            sc2 = sc - med
            if concentration(sc2, c, r_in, r_out) < a.min_conc:   # not centrally concentrated
                continue
            z = target / box
            cut = zoom(sc2, (z, z), order=1)[:target, :target]
            out.append(cut.astype(np.float32)); kept_centres.append((yc, xc)); kept_here += 1
        print(f"  {os.path.basename(sci_path)} (native {native:.3f}\"/px): +{kept_here}  total={len(out)}")
        del sci, wht

    if not out:
        raise SystemExit("no ellipticals kept -- lower --peak_nsigma or --min_conc")
    out = np.stack(out)
    out = out[rng.permutation(len(out))]
    with h5py.File(a.out, "w") as f:
        f.create_dataset("lens", data=out)
        f.attrs["pixel_scale"] = a.pixel_scale
        f.attrs["box_arcsec"] = a.box_arcsec
        f.attrs["note"] = "real COSMOS F814W elliptical-centred cutouts (electrons, median-subtracted) for SIMCT lens light"
    print(f"\nWROTE {len(out)} elliptical cutouts -> {a.out} (128x128 @ {a.pixel_scale}\"/px)")


if __name__ == "__main__":
    main()
