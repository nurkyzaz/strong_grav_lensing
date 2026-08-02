#!/usr/bin/env python
"""GEN5 C37 — light-smooth the cleaned Q1 delensed sources to soften the
PyAutoLens Voronoi-mesh faceting + fill small internal holes, without washing
out the compact star-forming knots. Gaussian sigma ~0.8 px + a 1-px grey
closing on the support. Writes q1_sources_smooth.h5 (same keys as clean)."""
import sys

import h5py
import numpy as np
from scipy.ndimage import gaussian_filter, grey_closing

INP = sys.argv[1] if len(sys.argv) > 1 else "q1_sources_clean.h5"
OUT = sys.argv[2] if len(sys.argv) > 2 else "q1_sources_smooth.h5"
SIGMA = float(sys.argv[3]) if len(sys.argv) > 3 else 0.8

f = h5py.File(INP, "r")
src = f["sources"][:]
out = np.empty_like(src)
for i, im in enumerate(src):
    im = np.nan_to_num(im.astype(np.float32))
    filled = grey_closing(im, size=2)        # fill 1-px mesh holes
    sm = gaussian_filter(filled, SIGMA)       # soften facets
    # preserve total flux
    s0, s1 = im.sum(), sm.sum()
    if s1 > 0:
        sm *= s0 / s1
    out[i] = sm.astype(np.float32)

with h5py.File(OUT, "w") as g:
    g["sources"] = out
    for k in ("names", "flux", "re_px", "peak_snr"):
        if k in f:
            g[k] = f[k][:]
    for k, v in f.attrs.items():
        g.attrs[k] = v
    g.attrs["smoothed_sigma_px"] = SIGMA
print("smoothed %d sources (sigma %.1f px) -> %s" % (len(out), SIGMA, OUT))
