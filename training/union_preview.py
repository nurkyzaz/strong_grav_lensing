#!/usr/bin/env python
"""Union-dataset preview for the R1.2b full-run decision: Euclidised REAL
SLACS (top row) vs selected survivors from pilot v2 (normal sources, middle
rows) and pilot B (high-SB compact sources, bottom rows), same asinh stretch.
Panels sorted by theta_E within each source so the small-vs-large coverage of
the two populations is visible."""
import numpy as np
import h5py
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

REAL = "/home/user/nurkyz/einstein_cnn/euclid_slacs_images.h5"
V2 = "/home/user/nurkyz/einstein_cnn/euc_sel_pilot_selected_v2.h5"
B = "/home/user/nurkyz/einstein_cnn/euc_sel_pilot_selected_B.h5"


def stretch(img):
    corners = np.concatenate([img[:16, :16].ravel(), img[-16:, -16:].ravel()])
    med = np.median(corners)
    mad = np.median(np.abs(corners - med)) * 1.4826
    return np.arcsinh((img - med) / max(mad, 1e-9))


with h5py.File(REAL, "r") as f:
    real = f["images"][:]
    names = [n.decode() if isinstance(n, bytes) else str(n) for n in f["names"][:]] \
        if "names" in f else ["real %d" % i for i in range(len(f["images"]))]
if real.ndim == 4:
    real = real[:, 0]
rng = np.random.default_rng(11)
ridx = rng.choice(len(real), 8, replace=False)

rows = [("REAL (Euclidised)", real[ridx], [names[i] for i in ridx], "orange")]
for tag, path, color in (("v2: normal sources", V2, "tab:blue"),
                         ("B: high-SB compact sources", B, "tab:green")):
    with h5py.File(path, "r") as f:
        sim = f["lensed"][:]
        th = f["theta_E"][:]
        snr = f["arc_snr"][:]
    order = np.argsort(th)
    pick = order[np.linspace(0, len(order) - 1, 8).astype(int)]
    labels = ["th=%.2f snr=%.1f" % (th[i], snr[i]) for i in pick]
    rows.append((tag, sim[pick], labels, color))

fig, axes = plt.subplots(3, 8, figsize=(20, 8))
for r, (tag, imgs, labels, color) in enumerate(rows):
    for cidx in range(8):
        ax = axes[r, cidx]
        ax.imshow(stretch(imgs[cidx]), cmap="gray", origin="lower")
        ax.set_title(labels[cidx], fontsize=7, color=color)
        ax.axis("off")
    axes[r, 0].set_ylabel(tag)
    axes[r, 0].axis("on")
    axes[r, 0].set_xticks([])
    axes[r, 0].set_yticks([])
    for spine in axes[r, 0].spines.values():
        spine.set_visible(False)
    axes[r, 0].set_ylabel(tag, fontsize=9, color=color)
fig.suptitle("UNION full-run decision: Euclidised real vs the two selected source populations "
             "(each sorted by theta_E; the union trains on both)")
fig.tight_layout()
fig.savefig("/home/user/nurkyz/cosmos_acs/tiles/union_decision_preview.png", dpi=110)
print("wrote union_decision_preview.png")
