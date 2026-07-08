#!/usr/bin/env python
"""Verify the companion-injection smoke: count field companions in the injected
sim vs real SLACS, and render a real-vs-injected side-by-side (same asinh
stretch). Writes to ~/cosmos_acs/tiles/ for Nurkyz to inspect."""
import os

import h5py
import numpy as np
from scipy.ndimage import label, gaussian_filter
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

EIN = os.path.expanduser("~/einstein_cnn")
TIL = os.path.expanduser("~/cosmos_acs/tiles")


def robust_sky(img, s=16):
    v = np.concatenate([img[:s, :s].ravel(), img[:s, -s:].ravel(),
                        img[-s:, :s].ravel(), img[-s:, -s:].ravel()])
    for _ in range(3):
        m, sd = v.mean(), v.std()
        v = v[np.abs(v - m) < 3 * sd]
        if len(v) < 10:
            break
    return v.mean(), v.std() + 1e-9


def count_companions(img):
    n = img.shape[0]; c = n // 2
    lvl, sky = robust_sky(img)
    sm = gaussian_filter(img - lvl, 1.0)
    mask = sm > 5 * sky
    yy, xx = np.mgrid[0:n, 0:n]
    mask &= np.hypot(yy - c, xx - c) >= 15
    lab, _ = label(mask)
    sizes = np.bincount(lab.ravel())[1:]
    return int((sizes >= 4).sum())


def load(path):
    with h5py.File(path, "r") as f:
        k = "images" if "images" in f else "lensed"
        imgs = f[k][:].astype("float32")
    return imgs[:, 0] if imgs.ndim == 4 else imgs


smoke_path = os.environ.get("SMOKE_H5", os.path.join(EIN, "smoke_companions.h5"))
smoke = load(smoke_path)
real = load(os.path.join(EIN, "real_slacs_images.h5"))
import re
m = re.search(r"companions(\d*)", os.path.basename(smoke_path))
tag = m.group(1) if m else ""
sc = np.array([count_companions(im) for im in smoke])
rc = np.array([count_companions(im) for im in real])
print(f"INJECTED sim companions/img: median {np.median(sc):.0f} mean {sc.mean():.1f} "
      f">=3: {np.mean(sc>=3):.2f}")
print(f"REAL SLACS companions/img:   median {np.median(rc):.0f} mean {rc.mean():.1f} "
      f">=3: {np.mean(rc>=3):.2f}")

fig, ax = plt.subplots(4, 8, figsize=(16, 8))
rng = np.random.default_rng(1)
for j in range(8):
    for row, imgs, lab_ in [(0, real, "REAL"), (1, real, "REAL"),
                            (2, smoke, "SIM+comp"), (3, smoke, "SIM+comp")]:
        im = imgs[rng.integers(len(imgs))]
        _, sky = robust_sky(im)
        ax[row, j].imshow(np.arcsinh(im / sky), cmap="gray", origin="lower")
        ax[row, j].set_title(lab_, fontsize=6); ax[row, j].axis("off")
fig.suptitle("Real SLACS (rows 1-2) vs injected-companion sim (rows 3-4), asinh")
fig.tight_layout()
out = os.path.join(TIL, f"smoke_companions{tag}_compare.png")
fig.savefig(out, dpi=110)
print("wrote", out)
