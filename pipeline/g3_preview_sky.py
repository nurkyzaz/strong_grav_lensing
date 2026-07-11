#!/usr/bin/env python
"""Preview grid of harvested Q1 empty-sky cutouts (asinh stretch)."""
import h5py
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

with h5py.File("/home/user/nurkyz/g3_scratch/euclid_sky_edff_1.h5", "r") as f:
    imgs = f["images"][:]
rng = np.random.default_rng(2)
idx = rng.choice(len(imgs), 16, replace=False)
fig, axes = plt.subplots(4, 4, figsize=(10, 10))
for ax, i in zip(axes.ravel(), idx):
    d = imgs[i]
    lo, hi = np.percentile(d, [16, 84])
    sig = (hi - lo) / 2
    ax.imshow(np.arcsinh(d / max(sig, 1e-6)), cmap="gray", origin="lower")
    ax.set_title("#%d" % i, fontsize=8)
    ax.axis("off")
fig.suptitle("Q1 VIS empty-sky cutouts (12.8\", asinh/sky-sigma stretch)")
fig.tight_layout()
fig.savefig("/home/user/nurkyz/g3_scratch/g3_sky_preview.png", dpi=110)
print("wrote g3_sky_preview.png; pool sigma stats:",
      np.median([np.std(im) for im in imgs[:200]]))
