#!/usr/bin/env python
"""Render ALL stamps of an h5 library in pages of 64 for visual pruning."""
import sys
import numpy as np
import h5py
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

fn, prefix = sys.argv[1], sys.argv[2]
with h5py.File(fn, "r") as f:
    st = f["stamps"][:]
    src = f["src_index"][:]
for page in range(int(np.ceil(len(st) / 64))):
    lo, hi = page * 64, min((page + 1) * 64, len(st))
    fig, axes = plt.subplots(8, 8, figsize=(17, 17))
    for axi, i in zip(axes.ravel(), range(lo, hi)):
        s = st[i]
        sky = np.median(np.abs(s - np.median(s))) * 1.4826
        axi.imshow(np.arcsinh(s / max(sky, 1e-9)), cmap="gray", origin="lower")
        axi.set_title("id%d src%d" % (i, src[i]), fontsize=7)
        axi.axis("off")
    for axi in axes.ravel()[hi - lo:]:
        axi.axis("off")
    fig.tight_layout()
    out = "%s_p%d.png" % (prefix, page)
    fig.savefig(out, dpi=110)
    print("wrote", out)
