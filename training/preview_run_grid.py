#!/usr/bin/env python
"""48-lens preview grid from the running Euclid-arm generation (shard 00),
asinh/sky-RMS stretch (same as the side-by-sides), sorted by theta_E,
labeled with theta_E and arc SNR."""
import numpy as np
import h5py
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

SRC = "/home/user/nurkyz/paltas_shards_euclid/hybrid_shard_00.h5"
N = 48

with h5py.File(SRC, "r") as f:
    n_all = f["lensed"].shape[0]
    rng = np.random.default_rng(20)
    idx = np.sort(rng.choice(n_all, N, replace=False))
    imgs = f["lensed"][idx]
    th = f["theta_E"][idx]
    snr = f["arc_snr"][idx]

order = np.argsort(th)
imgs, th, snr = imgs[order], th[order], snr[order]


def stretch(img):
    corners = np.concatenate([img[:16, :16].ravel(), img[-16:, -16:].ravel()])
    med = np.median(corners)
    mad = np.median(np.abs(corners - med)) * 1.4826
    return np.arcsinh((img - med) / max(mad, 1e-9))


rows, cols = 6, 8
fig, axes = plt.subplots(rows, cols, figsize=(2.3 * cols, 2.45 * rows))
for k, ax in enumerate(np.ravel(axes)):
    ax.axis("off")
    if k >= N:
        continue
    ax.imshow(stretch(imgs[k]), cmap="gray", origin="lower")
    ax.set_title("th=%.2f snr=%.1f" % (th[k], snr[k]), fontsize=8)
fig.suptitle("Euclid-arm FULL RUN, shard 00: 48 random selected lenses (sorted by theta_E) "
             "-- asinh/sky-RMS stretch", fontsize=13)
fig.tight_layout()
fig.savefig("/home/user/nurkyz/cosmos_acs/tiles/fullrun_preview_48.png", dpi=100)
print("wrote fullrun_preview_48.png")
