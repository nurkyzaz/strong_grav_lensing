#!/usr/bin/env python
"""P5: arc-visibility metric, v2.

v1 flaw (measured: median SNR 0.43 while arcs are plainly visible by eye in
the same images): the denominator was the MAD over an annulus spanning a
radial range, so the deflector's own RADIAL gradient dominated the
'fluctuation' and drowned the arc. What the eye does is compare the arc to
the azimuthal scatter of the scene at the SAME radius.

v2: for the composed image minus arc ('rest', = deflector+backdrop+noise),
subtract the per-radius azimuthal median profile (centre = image centre =
deflector centre), then measure the MAD of the residual over the arc's own
footprint radii. arc SNR := max smoothed arc flux in footprint / that MAD.
Reports fraction with SNR > 3 and > 5.

Sanity hook: --h5_index prints per-image SNR for cross-checking against the
side-by-side panels by eye.
"""
import argparse
import glob
import os
import h5py
import numpy as np
from scipy.ndimage import gaussian_filter

ap = argparse.ArgumentParser()
ap.add_argument("--run", required=True, help="paltas run folder with image_*.npy (noiseless arcs)")
ap.add_argument("--sim", required=True, help="composed pilot h5 (same order as npys)")
ap.add_argument("--fp_frac", type=float, default=0.5,
                help="arc footprint = smoothed arc > fp_frac * its own peak")
ap.add_argument("--h5_index", type=int, nargs="*", default=[],
                help="print per-image SNR for these h5 indices")
args = ap.parse_args()

files = sorted(glob.glob(os.path.join(os.path.expanduser(args.run), "image_*.npy")))
with h5py.File(os.path.expanduser(args.sim), "r") as f:
    sim = f["lensed"][:]
assert len(files) == len(sim), "npy count %d != h5 count %d" % (len(files), len(sim))

n = sim.shape[1]
c = n // 2
yy, xx = np.mgrid[0:n, 0:n]
rr = np.hypot(yy - c, xx - c)
rbin = rr.astype(int)

snrs = []
for fn, comp in zip(files, sim):
    arc = np.load(fn).astype("float64")
    arc_s = gaussian_filter(arc, 1.5)
    pk = arc_s.max()
    if pk <= 0:
        snrs.append(0.0)
        continue
    fp = arc_s > args.fp_frac * pk
    rest = comp.astype("float64") - arc
    rest_s = gaussian_filter(rest, 1.5)
    # subtract the azimuthal median profile (kills the smooth halo gradient)
    prof = np.zeros(rbin.max() + 1)
    for k in range(rbin.max() + 1):
        m = rbin == k
        if m.any():
            prof[k] = np.median(rest_s[m])
    resid = rest_s - prof[rbin]
    # fluctuation at the arc's own radii (annulus covering the footprint)
    r_lo, r_hi = rr[fp].min() - 3, rr[fp].max() + 3
    ann = (rr >= r_lo) & (rr <= r_hi) & (~fp)
    loc = resid[ann]
    mad = np.median(np.abs(loc - np.median(loc))) * 1.4826
    if mad <= 0:
        snrs.append(0.0)
        continue
    snrs.append(float(arc_s[fp].max() / mad))

snrs = np.array(snrs)
print("arc SNR (v2, azimuthal-residual denominator):")
print("  median %.2f  16-84%% [%.2f, %.2f]" %
      (np.median(snrs), np.percentile(snrs, 16), np.percentile(snrs, 84)))
for t in (3.0, 5.0):
    print("  fraction with arc SNR > %.0f: %.2f" % (t, (snrs > t).mean()))
for i in args.h5_index:
    print("  h5 index %d: arc SNR %.2f" % (i, snrs[i]))
