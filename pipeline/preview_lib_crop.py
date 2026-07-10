#!/usr/bin/env python
"""Preview a deflector library's CENTRAL 128px crop (= exactly the pasted
region in hybrid_combine.py) for visual pruning of a >128px library."""
import argparse
import h5py
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ap = argparse.ArgumentParser()
ap.add_argument("--lib", required=True)
ap.add_argument("--out", required=True)
ap.add_argument("--ncol", type=int, default=8)
a = ap.parse_args()

with h5py.File(a.lib, "r") as f:
    st = f["stamps"][:]
    src = f["src_index"][:] if "src_index" in f else np.arange(len(st))
if st.shape[1] > 128:
    c0 = (st.shape[1] - 128) // 2
    st = st[:, c0:c0 + 128, c0:c0 + 128]

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
fig.suptitle("library %s CENTRAL 128px crop = the pasted region" % a.lib)
fig.tight_layout()
fig.savefig(a.out, dpi=110)
print("wrote", a.out, "n=", len(st))
