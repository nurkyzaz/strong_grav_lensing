#!/usr/bin/env python
"""Path B (2026-07-08): build a library of REAL elliptical-galaxy cutouts from
the COSMOS ACS F814W tiles, to use as foreground DEFLECTOR LIGHT (replacing the
parametric Sersic). Same instrument/band as the benchmark -> real HST PSF,
morphology, colour gradients, isophote twists that a Sersic cannot reproduce.

Selection: big, bright, SMOOTH, CONCENTRATED single galaxies (early-type-like):
  - bbox extent in a SLACS-deflector size range,
  - high central concentration (flux within Re/2 vs total),
  - low 180-deg rotational asymmetry (rejects spirals/mergers/pairs),
  - single dominant central peak.
Each stamp: 128x128 @ 0.05"/px, local-background-subtracted, Tukey-tapered so
far neighbours fade (companions are injected separately) and pasting is seamless.
Units = tile electrons/s (rescaled to a target magnitude at inject time).
"""
import argparse
import glob
import os

import numpy as np
import h5py
from astropy.io import fits
from astropy.stats import sigma_clipped_stats
from scipy.ndimage import label, find_objects, zoom, gaussian_filter


def first_2d(path):
    with fits.open(path, memmap=True) as hdul:
        for h in hdul:
            if h.data is not None and getattr(h.data, "ndim", 0) == 2:
                return h.data, h.header
    raise ValueError(f"no 2D HDU in {path}")


def tukey2d(n, alpha=0.35):
    w = np.ones(n)
    e = int(alpha * (n - 1) / 2)
    for i in range(e):
        w[i] = w[n - 1 - i] = 0.5 * (1 + np.cos(np.pi * (i / e - 1)))
    return np.outer(w, w).astype(np.float32)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--tiles_dir", required=True)
    p.add_argument("--out", default="deflector_stamps.h5")
    p.add_argument("--n", type=int, default=3000)
    p.add_argument("--stamp_px", type=int, default=128)
    p.add_argument("--nsigma", type=float, default=3.0)
    p.add_argument("--min_extent_native", type=int, default=45,
                   help="min bbox max-dim (native px ~0.03\"/px): SLACS-sized")
    p.add_argument("--max_extent_native", type=int, default=280)
    p.add_argument("--max_aspect", type=float, default=2.0, help="reject elongated")
    p.add_argument("--min_concentration", type=float, default=0.42,
                   help="min flux fraction within quarter-box radius (ellipticals concentrated)")
    p.add_argument("--max_asymmetry", type=float, default=0.22,
                   help="max 180-deg rotational asymmetry")
    p.add_argument("--min_q", type=float, default=0.6,
                   help="min moment-based axis ratio over the whole galaxy (kills edge-on disks)")
    p.add_argument("--min_peak_snr", type=float, default=25.0,
                   help="min central peak / background sigma (bright massive galaxy)")
    p.add_argument("--max_clump", type=float, default=0.12,
                   help="max clumpiness = |I - smooth(I)|/I over the galaxy (rejects spiral/irregular)")
    p.add_argument("--block", type=int, default=3000)
    p.add_argument("--seed", type=int, default=0)
    a = p.parse_args()
    rng = np.random.default_rng(a.seed)
    taper = tukey2d(a.stamp_px)

    tiles = sorted(glob.glob(os.path.join(os.path.expanduser(a.tiles_dir),
                                          "acs_I_030mas_*_sci.fits")))
    if not tiles:
        raise SystemExit("no tiles")
    stamps, fluxes = [], []
    for sci_path in tiles:
        if len(stamps) >= a.n:
            break
        data, hdr = first_2d(sci_path)
        try:
            from astropy.wcs import WCS
            native = abs(WCS(hdr).proj_plane_pixel_scales()[0].to("arcsec").value)
        except Exception:
            native = 0.03
        half = int(round((a.stamp_px * 0.05 / native) / 2))  # native half-box
        H, W = data.shape
        blk = a.block
        starts = [(y, x) for y in range(half, H - half - blk, blk)
                  for x in range(half, W - half - blk, blk)]
        rng.shuffle(starts)
        for (y0, x0) in starts:
            if len(stamps) >= a.n:
                break
            sub = np.asarray(data[y0:y0 + blk, x0:x0 + blk], dtype=np.float32)
            sub = np.nan_to_num(sub)
            med, _, std = sigma_clipped_stats(sub, sigma=3.0, maxiters=2)
            if std <= 0:
                continue
            mask = (sub - med) > a.nsigma * std
            if not mask.any():
                continue
            lab, nlab = label(mask)
            for li, sl in enumerate(find_objects(lab), start=1):
                if sl is None or len(stamps) >= a.n:
                    continue
                ph, pw = sl[0].stop - sl[0].start, sl[1].stop - sl[1].start
                ext = max(ph, pw)
                if ext < a.min_extent_native or ext > a.max_extent_native:
                    continue
                if max(ph, pw) / max(1, min(ph, pw)) > a.max_aspect:
                    continue
                cy = y0 + (sl[0].start + sl[0].stop) // 2
                cx = x0 + (sl[1].start + sl[1].stop) // 2
                if (cy - half < 0 or cy + half + 1 > H or
                        cx - half < 0 or cx + half + 1 > W):
                    continue
                box = np.asarray(data[cy - half:cy + half + 1,
                                      cx - half:cx + half + 1], dtype=np.float32)
                if not np.isfinite(box).all():
                    continue
                # local background level + sigma from the box corners
                s = box.shape[0] // 8
                corners = np.concatenate([box[:s, :s].ravel(), box[:s, -s:].ravel(),
                                          box[-s:, :s].ravel(), box[-s:, -s:].ravel()])
                bg = np.median(corners); bg_sig = corners.std() + 1e-9
                g = box - bg
                g[g < 0] = 0.0
                nb = g.shape[0]; c = nb // 2
                yy, xx = np.mgrid[0:nb, 0:nb]
                r = np.hypot(yy - c, xx - c)
                tot = g.sum()
                if tot <= 0:
                    continue
                gsm = gaussian_filter(g, 2.0)
                # (1) bright, massive galaxy -> high central peak S/N
                if gsm.max() < a.min_peak_snr * bg_sig:
                    continue
                # (2) brightest pixel near centre (single central galaxy)
                by, bx = np.unravel_index(np.argmax(gsm), gsm.shape)
                if np.hypot(by - c, bx - c) > nb * 0.10:
                    continue
                # (3) concentration (ellipticals are centrally concentrated)
                if g[r < nb / 4].sum() / tot < a.min_concentration:
                    continue
                # (4) 180-deg rotational asymmetry (rejects mergers/pairs)
                if np.abs(gsm - gsm[::-1, ::-1]).sum() / (2 * gsm.sum() + 1e-9) > a.max_asymmetry:
                    continue
                # (5) moment-based axis ratio over the WHOLE galaxy (r<nb/2):
                #     catches edge-on disks whose central bulge alone looks round
                gal = (r < nb / 2)
                w = g * gal
                sw = w.sum()
                if sw <= 0:
                    continue
                mx = (w * xx).sum() / sw; my = (w * yy).sum() / sw
                Ixx = (w * (xx - mx) ** 2).sum() / sw
                Iyy = (w * (yy - my) ** 2).sum() / sw
                Ixy = (w * (xx - mx) * (yy - my)).sum() / sw
                tr, det = Ixx + Iyy, Ixx * Iyy - Ixy ** 2
                disc = max(tr * tr / 4 - det, 0.0)
                l1, l2 = tr / 2 + np.sqrt(disc), tr / 2 - np.sqrt(disc)
                q = np.sqrt(max(l2, 0) / (l1 + 1e-9))
                if q < a.min_q:
                    continue
                # (6) clumpiness over the whole galaxy (rejects spiral/irregular):
                #     high-frequency residual relative to a heavily-smoothed profile
                heavy = gaussian_filter(g, 6.0)
                clump = np.abs(g[gal] - heavy[gal]).sum() / (g[gal].sum() + 1e-9)
                if clump > a.max_clump:
                    continue
                z = a.stamp_px / g.shape[0]
                st = zoom(g, z, order=1)[:a.stamp_px, :a.stamp_px]
                st[st < 0] = 0.0
                st *= taper
                if st.sum() <= 0:
                    continue
                stamps.append(st.astype(np.float32))
                fluxes.append(float(st.sum()))
        print(f"  {os.path.basename(sci_path)}: total deflectors={len(stamps)}", flush=True)
        del data

    stamps = np.stack(stamps[:a.n])
    order = rng.permutation(len(stamps))
    stamps = stamps[order]
    with h5py.File(a.out, "w") as f:
        f.create_dataset("stamps", data=stamps)
    print(f"\nWROTE {len(stamps)} real elliptical deflector stamps -> {a.out} "
          f"({a.stamp_px}px @0.05\"/px)", flush=True)


if __name__ == "__main__":
    main()
