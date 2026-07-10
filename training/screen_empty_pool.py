#!/usr/bin/env python
"""Screen the empty-cutout backdrop pool for large-scale gradient outliers
(found via SIM #11: cutout 1211 has plane-gradient 10.6x noise -> visible
'abrupt edge' in Euclidised images). Reference = the gradient distribution of
the REAL benchmark cutouts (sims should not have stronger gradients than real
data). Writes a screened pool."""
import numpy as np
import h5py

POOL = "/home/user/nurkyz/cosmos_acs/tiles/empty_cutouts_4k.h5"
REAL = "/home/user/nurkyz/einstein_cnn/real_slacs_images.h5"
OUT = "/home/user/nurkyz/cosmos_acs/tiles/empty_cutouts_4k_screened.h5"

yy, xx = np.mgrid[0:128, 0:128]
A = np.c_[xx.ravel(), yy.ravel(), np.ones(128 * 128)]


def grad_over_noise(img):
    coef, *_ = np.linalg.lstsq(A, img.ravel(), rcond=None)
    plane = (A @ coef).reshape(128, 128)
    resid = img - plane
    mad = np.median(np.abs(resid - np.median(resid))) * 1.4826
    return (plane.max() - plane.min()) / mad if mad > 0 else np.inf


with h5py.File(REAL, "r") as f:
    real = f["images"][:]
if real.ndim == 4:
    real = real[:, 0]
rg = np.array([grad_over_noise(x) for x in real])
print("REAL benchmark gradient/noise: median %.2f  84%% %.2f  95%% %.2f  max %.2f"
      % (np.median(rg), np.percentile(rg, 84), np.percentile(rg, 95), rg.max()))

with h5py.File(POOL, "r") as f:
    key = "empty" if "empty" in f else list(f.keys())[0]
    pool = f[key][:]
    others = {k: (f[k][()] if f[k].shape == () else f[k][:])
              for k in f.keys() if k != key}
pg = np.array([grad_over_noise(x) for x in pool])
print("POOL gradient/noise: median %.2f  84%% %.2f  95%% %.2f  max %.2f"
      % (np.median(pg), np.percentile(pg, 84), np.percentile(pg, 95), pg.max()))

# screen at the real distribution's 95th percentile (sims no worse than real)
thr = float(np.percentile(rg, 95))
keep = pg <= thr
print("screen threshold (real 95%%): %.2f -> keep %d/%d (%.0f%%)"
      % (thr, keep.sum(), len(pool), 100 * keep.mean()))
with h5py.File(OUT, "w") as f:
    f.create_dataset(key, data=pool[keep])
    for k, v in others.items():
        v = np.asarray(v)
        f.create_dataset(k, data=v[keep] if v.shape[:1] == (len(pool),) else v)
print("wrote", OUT)
