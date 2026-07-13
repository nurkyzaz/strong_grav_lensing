#!/usr/bin/env python
"""Add per-image deflector_re (arcsec, half-light radius of the REAL deflector
stamp) to a merged h5, from deflector_index + shard id (sub-shards >= 80 used
the val stamp library). Aux-head label; images untouched.
Usage: add_deflector_re.py <merged.h5>"""
import sys
import numpy as np
import h5py

PIX = 0.05
TRAIN_LIB = "/home/user/nurkyz/cosmos_acs/tiles/deflector_stamps_lrg_v6_train.h5"
VAL_LIB = "/home/user/nurkyz/cosmos_acs/tiles/deflector_stamps_lrg_v6_val.h5"
VAL_SHARD_MIN = 80


def halflight_radii(lib):
    with h5py.File(lib, "r") as f:
        key = "stamps" if "stamps" in f else list(f.keys())[0]
        st = f[key][:]
    out = np.zeros(len(st))
    for i, s in enumerate(st):
        s = np.clip(s.astype("float64"), 0, None)
        n = s.shape[0]
        c = n // 2
        yy, xx = np.mgrid[0:n, 0:n]
        rr = np.hypot(yy - c, xx - c).ravel()
        order = np.argsort(rr)
        cum = np.cumsum(s.ravel()[order])
        tot = cum[-1]
        out[i] = rr[order][np.searchsorted(cum, 0.5 * tot)] * PIX if tot > 0 else np.nan
    return out


fn = sys.argv[1]
re_train = halflight_radii(TRAIN_LIB)
re_val = halflight_radii(VAL_LIB)
print("stamp Re: train lib n=%d median %.2f\" | val lib n=%d median %.2f\""
      % (len(re_train), np.nanmedian(re_train), len(re_val), np.nanmedian(re_val)))

with h5py.File(fn, "a") as f:
    idx = f["deflector_index"][:].astype(int)
    if "shard" in f:
        is_val = f["shard"][:] >= VAL_SHARD_MIN
    else:  # val-only file (merged val has no shard? then infer from filename)
        is_val = np.full(len(idx), "val" in fn)
    re = np.where(is_val, re_val[np.clip(idx, 0, len(re_val) - 1)],
                  re_train[np.clip(idx, 0, len(re_train) - 1)])
    if "deflector_re" in f:
        del f["deflector_re"]
    f.create_dataset("deflector_re", data=re.astype("float32"))
    print("%s: deflector_re written (n=%d, median %.2f\", val-lib rows %d)"
          % (fn, len(re), np.nanmedian(re), int(is_val.sum())))
