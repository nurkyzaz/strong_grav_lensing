#!/usr/bin/env python
"""Q5 step 2: gradient-screen the NEW tile-066/074 harvest (same real-95%
threshold 2.85 as screen_empty_pool.py) and concatenate with the existing
screened pool into empty_cutouts_expanded_screened.h5."""
import numpy as np
import h5py

NEW = "/home/user/nurkyz/cosmos_acs/tiles/empty_cutouts_new066074.h5"
OLD = "/home/user/nurkyz/cosmos_acs/tiles/empty_cutouts_4k_screened.h5"
OUT = "/home/user/nurkyz/cosmos_acs/tiles/empty_cutouts_expanded_screened.h5"
THR = 2.85  # real-benchmark 95th percentile (screen_empty_pool.py, 2026-07-09)

yy, xx = np.mgrid[0:128, 0:128]
A = np.c_[xx.ravel(), yy.ravel(), np.ones(128 * 128)]


def grad_over_noise(img):
    coef, *_ = np.linalg.lstsq(A, img.ravel(), rcond=None)
    plane = (A @ coef).reshape(128, 128)
    resid = img - plane
    mad = np.median(np.abs(resid - np.median(resid))) * 1.4826
    return (plane.max() - plane.min()) / mad if mad > 0 else np.inf


def load(path):
    with h5py.File(path, "r") as f:
        key = "empty" if "empty" in f else list(f.keys())[0]
        return f[key][:]


new = load(NEW)
g = np.array([grad_over_noise(x) for x in new])
keep = g <= THR
print("new harvest: %d cutouts; gradient screen keeps %d (%.0f%%)"
      % (len(new), keep.sum(), 100 * keep.mean()))
old = load(OLD)
pool = np.concatenate([old, new[keep]]).astype("float32")
with h5py.File(OUT, "w") as f:
    f.create_dataset("empty", data=pool)
print("wrote %s: %d cutouts (old screened %d + new screened %d)"
      % (OUT, len(pool), len(old), keep.sum()))
