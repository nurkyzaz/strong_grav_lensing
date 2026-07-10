#!/usr/bin/env python
"""P3: split the deflector library into TRAIN and VAL stamp sets (mirrors the
PSF-kernel pattern: val kernels are train-disjoint). Val stamps are chosen at
evenly spaced quantiles of the stamp half-light radius so they span the
morphology/size range rather than clustering."""
import argparse
import h5py
import numpy as np

ap = argparse.ArgumentParser()
ap.add_argument("--lib", required=True)
ap.add_argument("--n_val", type=int, default=8)
ap.add_argument("--train_out", required=True)
ap.add_argument("--val_out", required=True)
a = ap.parse_args()

with h5py.File(a.lib, "r") as f:
    st = f["stamps"][:]
    src = f["src_index"][:]


def half_light_radius_px(s):
    n = s.shape[0]
    c = n // 2
    yy, xx = np.mgrid[0:n, 0:n]
    r = np.hypot(yy - c, xx - c).ravel()
    fl = np.clip(s.ravel(), 0, None)
    order = np.argsort(r)
    cum = np.cumsum(fl[order])
    if cum[-1] <= 0:
        return np.nan
    k = min(int(np.searchsorted(cum, 0.5 * cum[-1])), len(order) - 1)
    return float(r[order][k])


re_px = np.array([half_light_radius_px(s) for s in st])
order = np.argsort(re_px)
# evenly spaced quantile positions, offset from the extremes
q = (np.arange(a.n_val) + 0.5) / a.n_val
val_idx = sorted(set(order[(q * (len(st) - 1)).astype(int)]))
# if quantile collisions reduced the count, pad with unused neighbours
pool = [i for i in order if i not in val_idx]
while len(val_idx) < a.n_val:
    val_idx.append(pool.pop())
val_idx = np.array(sorted(val_idx))
train_idx = np.array([i for i in range(len(st)) if i not in set(val_idx.tolist())])

for out, idx in [(a.train_out, train_idx), (a.val_out, val_idx)]:
    with h5py.File(out, "w") as f:
        f.create_dataset("stamps", data=st[idx])
        f.create_dataset("src_index", data=src[idx])
    print("wrote %s: %d stamps (src %s)" % (out, len(idx), list(src[idx])))
print("val stamp Re[px]: %s" % np.round(re_px[val_idx], 1).tolist())
