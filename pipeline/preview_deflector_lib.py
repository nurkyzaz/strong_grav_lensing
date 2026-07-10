#!/usr/bin/env python
"""Render the deflector library as an asinh-stretch grid for visual inspection."""
import argparse

import h5py
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ap = argparse.ArgumentParser()
ap.add_argument("--lib", default="deflector_stamps_lrg_v3.h5")
ap.add_argument("--out", default="deflector_lib_v3preview.png")
ap.add_argument("--ncol", type=int, default=8)
a = ap.parse_args()

with h5py.File(a.lib, "r") as f:
    st = f["stamps"][:]
    src = f["src_index"][:] if "src_index" in f else np.arange(len(st))

nrow = int(np.ceil(len(st) / a.ncol))
fig, axes = plt.subplots(nrow, a.ncol, figsize=(2 * a.ncol, 2 * nrow))
for k, ax in enumerate(np.ravel(axes)):
    ax.axis("off")
    if k >= len(st):
        continue
    im = st[k]
    sc = np.percentile(im[im > 0], 60) if (im > 0).any() else 1.0
    ax.imshow(np.arcsinh(im / max(sc, 1e-8)), cmap="gray", origin="lower")
    ax.set_title("#%d (src %d)" % (k, src[k]), fontsize=7)
fig.suptitle("deflector library %s (asinh)" % a.lib)
fig.tight_layout()
fig.savefig(a.out, dpi=110)
print("wrote", a.out, "n=", len(st))
