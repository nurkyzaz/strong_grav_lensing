#!/usr/bin/env python
"""Build a library of REAL compact-source postage stamps from the COSMOS ACS
F814W tile(s), for companion-light injection into training images (Nurkyz
2026-07-07: real lenses have ~10 field companions/img, our sims have ~0).

FAST rewrite (2026-07-08): the previous version called center_of_mass per
label on the FULL 400-Mpx tile (O(N) each -> hung for hours). Now: process
the tile in BLOCKS, label each block once, use find_objects for all bounding
boxes in a single pass, filter by size, extract stamps. Stops once --n reached.
Units = tile electrons/s = same as sim/backdrop (no rescale).
"""
import argparse
import glob
import os

import numpy as np
import h5py
from astropy.io import fits
from astropy.stats import sigma_clipped_stats
from scipy.ndimage import label, zoom


def first_2d(path):
    with fits.open(path, memmap=True) as hdul:
        for h in hdul:
            if h.data is not None and getattr(h.data, "ndim", 0) == 2:
                return h.data, h.header
    raise ValueError(f"no 2D HDU in {path}")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--tiles_dir", required=True)
    p.add_argument("--out", default="source_stamps.h5")
    p.add_argument("--n", type=int, default=6000)
    p.add_argument("--stamp_px", type=int, default=25, help="output stamp size @0.05\"/px")
    p.add_argument("--nsigma", type=float, default=5.0)
    p.add_argument("--min_pix", type=int, default=6, help="min source bbox area (native)")
    p.add_argument("--max_pix", type=int, default=600,
                   help="max source bbox area -> reject big foreground galaxies")
    p.add_argument("--max_aspect", type=float, default=2.2,
                   help="reject bbox elongation > this (cosmic rays / trails)")
    p.add_argument("--min_fill", type=float, default=0.35,
                   help="reject sources filling < this fraction of bbox (streaks)")
    p.add_argument("--block", type=int, default=2048, help="processing block size (px)")
    p.add_argument("--seed", type=int, default=0)
    a = p.parse_args()
    rng = np.random.default_rng(a.seed)

    # flat-top (Tukey) window: 1.0 in the centre (keep the source intact),
    # cosine roll-off only in the outer ~20% so pasting leaves no box seam
    def tukey(n, alpha=0.4):
        w = np.ones(n)
        e = int(alpha * (n - 1) / 2)
        for i in range(e):
            w[i] = w[n - 1 - i] = 0.5 * (1 + np.cos(np.pi * (i / e - 1)))
        return w
    _w = tukey(a.stamp_px)
    taper = np.outer(_w, _w).astype(np.float32)

    sci_tiles = sorted(glob.glob(os.path.join(os.path.expanduser(a.tiles_dir),
                                              "acs_I_030mas_*_sci.fits")))
    if not sci_tiles:
        raise SystemExit("no acs_I_030mas_*_sci.fits tiles found")
    stamps = []
    for sci_path in sci_tiles:
        if len(stamps) >= a.n:
            break
        data, hdr = first_2d(sci_path)
        try:
            from astropy.wcs import WCS
            native = abs(WCS(hdr).proj_plane_pixel_scales()[0].to("arcsec").value)
        except Exception:
            native = 0.03
        half = int(round((a.stamp_px * 0.05 / native) / 2))  # native half-size
        H, W = data.shape
        blk = a.block
        # iterate blocks in randomized order for source diversity
        starts = [(y, x) for y in range(half, H - half - blk, blk)
                  for x in range(half, W - half - blk, blk)]
        rng.shuffle(starts)
        for (y0, x0) in starts:
            if len(stamps) >= a.n:
                break
            sub = np.asarray(data[y0:y0 + blk, x0:x0 + blk], dtype=np.float32)
            if not np.isfinite(sub).all():
                sub = np.nan_to_num(sub)
            med, _, std = sigma_clipped_stats(sub, sigma=3.0, maxiters=2)
            if std <= 0:
                continue
            mask = (sub - med) > a.nsigma * std
            if not mask.any():
                continue
            lab, nlab = label(mask)
            objs = __import__("scipy.ndimage", fromlist=["find_objects"]).find_objects(lab)
            for li, sl in enumerate(objs, start=1):
                if sl is None:
                    continue
                ph = sl[0].stop - sl[0].start
                pw = sl[1].stop - sl[1].start
                area = ph * pw
                if area < a.min_pix or area > a.max_pix:
                    continue
                # --- reject linear artifacts (cosmic rays, satellite trails) ---
                aspect = max(ph, pw) / max(1, min(ph, pw))
                if aspect > a.max_aspect:
                    continue
                npix = int((lab[sl] == li).sum())
                if npix / area < a.min_fill:       # sparse/streaky -> reject
                    continue
                cy = y0 + (sl[0].start + sl[0].stop) // 2
                cx = x0 + (sl[1].start + sl[1].stop) // 2
                if (cy - half < 0 or cy + half + 1 > H or
                        cx - half < 0 or cx + half + 1 > W):
                    continue
                st = np.asarray(data[cy - half:cy + half + 1,
                                     cx - half:cx + half + 1], dtype=np.float32)
                if not np.isfinite(st).all():
                    continue
                st = st - np.median(st)
                st[st < 0] = 0.0
                z = a.stamp_px / st.shape[0]
                st = zoom(st, z, order=1)[:a.stamp_px, :a.stamp_px]
                if st.sum() <= 0:
                    continue
                st *= taper                        # apodize edges -> no box seam
                stamps.append(st.astype(np.float32))
                if len(stamps) >= a.n:
                    break
        print(f"  {os.path.basename(sci_path)} (native {native:.3f}): "
              f"total stamps={len(stamps)}", flush=True)
        del data

    stamps = np.stack(stamps[:a.n])
    stamps = stamps[rng.permutation(len(stamps))]
    with h5py.File(a.out, "w") as f:
        f.create_dataset("stamps", data=stamps)
    tot = stamps.reshape(len(stamps), -1).sum(1)
    print(f"\nWROTE {len(stamps)} source stamps -> {a.out} "
          f"({a.stamp_px}x{a.stamp_px}); total-flux median {np.median(tot):.3f}",
          flush=True)


if __name__ == "__main__":
    main()
