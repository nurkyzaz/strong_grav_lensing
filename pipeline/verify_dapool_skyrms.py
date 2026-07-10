#!/usr/bin/env python
"""P4 pre-check: does the benchmark-disjoint DA pool's robust sky-RMS
distribution cover the benchmark SLACS AND S4TM distributions? If yes, drawing
generation noise targets from the pool (a) removes the last calibration use of
the frozen test file and (b) subsumes the pending 'S4TM noise union' fix.
Same estimator on all three samples."""
import h5py
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def robust_sky_rms(img):
    n = img.shape[0]
    m = n // 8
    corners = np.concatenate([img[:m, :m].ravel(), img[:m, -m:].ravel(),
                              img[-m:, :m].ravel(), img[-m:, -m:].ravel()])
    med = np.median(corners)
    return np.median(np.abs(corners - med)) * 1.4826


def load(path):
    with h5py.File(path, "r") as f:
        key = "images" if "images" in f else list(f.keys())[0]
        im = f[key][:]
    if im.ndim == 4:
        im = im[:, 0]
    return np.array([robust_sky_rms(x) for x in im])


sets = {
    "DA pool (104, disjoint)": "/home/user/nurkyz/einstein_cnn/real_dapool_images.h5",
    "benchmark SLACS (62+1)": "/home/user/nurkyz/einstein_cnn/real_slacs_images.h5",
    "benchmark S4TM (40)": "/home/user/nurkyz/einstein_cnn/real_s4tm_images.h5",
}
vals = {}
for name, path in sets.items():
    v = load(path)
    vals[name] = v
    print("%-26s N=%3d  median=%.5f  16-84%%=[%.5f, %.5f]  min/max=[%.5f, %.5f]"
          % (name, len(v), np.median(v), np.percentile(v, 16), np.percentile(v, 84),
             v.min(), v.max()))

fig, ax = plt.subplots(figsize=(9, 5))
bins = np.linspace(0, max(v.max() for v in vals.values()) * 1.05, 40)
for (name, v), color in zip(vals.items(), ["tab:green", "k", "tab:blue"]):
    ax.hist(v, bins=bins, histtype="step", lw=2, density=True, label=name, color=color)
    ax.axvline(np.median(v), color=color, ls=":", lw=1)
ax.set_xlabel("robust sky RMS [e-/s] (corner MAD estimator)")
ax.set_ylabel("density")
ax.set_title("P4 check: DA-pool sky-RMS must cover benchmark SLACS + S4TM")
ax.legend()
fig.tight_layout()
fig.savefig("/home/user/nurkyz/cosmos_acs/tiles/dapool_skyrms_check.png", dpi=110)
print("wrote dapool_skyrms_check.png")
