#!/usr/bin/env python
"""Probe the Q1 PyAutoLens modeling dirs for the delensed source-plane galaxy,
report which FITS product holds it, and build an eyeball montage."""
import glob
import os

import numpy as np
from astropy.io import fits
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = "/home/user/nurkyz/cosmos_acs/q1_slde/lens/lens"
dirs = sorted(glob.glob(os.path.join(ROOT, "*/result")))
print("lens result dirs:", len(dirs))

CANDS = ["source_reconstruction.fits", "source_light.fits",
         "mge_source_light.fits", "mge_source_reconstruction.fits"]


def load(path):
    try:
        d = fits.getdata(path)
        return np.asarray(d, float) if d is not None else None
    except Exception:
        return None


# how many have content in each product
stats = {c: 0 for c in CANDS}
shapes = {c: None for c in CANDS}
for d in dirs:
    for c in CANDS:
        arr = load(os.path.join(d, c))
        if arr is not None and np.nansum(np.abs(arr)) > 0:
            stats[c] += 1
            shapes[c] = arr.shape
print("nonzero counts / shape:")
for c in CANDS:
    print("  %-32s %4d/%d  shape=%s" % (c, stats[c], len(dirs), shapes[c]))

# pick the best-populated product for the montage
best = max(CANDS, key=lambda c: stats[c])
print("BEST source product:", best)


def asinh(im):
    im = np.nan_to_num(im)
    p = np.percentile(im, 99.7)
    a = np.arcsinh(np.clip(im, 0, None) / max(p / 20, 1e-9))
    return a / max(a.max(), 1e-9)


picks = []
for d in dirs:
    arr = load(os.path.join(d, best))
    if arr is not None and np.nansum(np.abs(arr)) > 0:
        name = os.path.basename(os.path.dirname(d))
        picks.append((name, arr))
    if len(picks) >= 16:
        break
fig, ax = plt.subplots(4, 4, figsize=(12, 12))
for k, a in enumerate(ax.ravel()):
    if k < len(picks):
        nm, im = picks[k]
        a.imshow(asinh(im), cmap="magma", origin="lower")
        a.set_title("%s\n%dx%d" % (nm[:22], im.shape[0], im.shape[1]), fontsize=7)
    a.axis("off")
fig.suptitle("Q1 PyAutoLens delensed SOURCE-plane reconstructions (%s)" % best, fontsize=12)
fig.tight_layout()
out = "/home/user/nurkyz/cosmos_acs/q1_slde/q1_source_montage.png"
fig.savefig(out, dpi=90)
print("wrote", out)
