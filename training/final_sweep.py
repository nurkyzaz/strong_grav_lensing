#!/usr/bin/env python
"""Final pre-training bug sweep on the Euclid-arm dataset (train + val)."""
import numpy as np
import h5py

for path, tag in (("/home/user/nurkyz/einstein_cnn/train_euclid_sel_100k.h5", "TRAIN"),
                  ("/home/user/nurkyz/einstein_cnn/val_euclid_sel_5k.h5", "VAL")):
    with h5py.File(path, "r") as f:
        th = f["theta_E"][:]
        snr = f["arc_snr"][:]
        ext = f["arc_extent"][:]
        sh = f["shard"][:]
        n = f["lensed"].shape[0]
        rng = np.random.default_rng(1)
        idx = np.sort(rng.choice(n, 500, replace=False))
        sample = f["lensed"][idx]
    ok_sel = (snr > 0.7).all() and (ext >= 150).all()
    print("%s: N=%d | theta [%.3f, %.3f] med %.3f zeros=%d | "
          "arc_snr min %.2f | extent min %.0f | selection-consistent: %s"
          % (tag, n, th.min(), th.max(), np.median(th), (th == 0).sum(),
             snr.min(), ext.min(), ok_sel))
    print("  shards: %d unique [%d..%d]; per-shard count min/max %d/%d"
          % (len(np.unique(sh)), sh.min(), sh.max(),
             np.bincount(sh - sh.min()).min(), np.bincount(sh - sh.min()).max()))
    print("  sample(500): NaN %s | Inf %s | max %.2f | min %.4f"
          % (bool(np.isnan(sample).any()), bool(np.isinf(sample).any()),
             sample.max(), sample.min()))
    if tag == "TRAIN":
        tr_shards = set(np.unique(sh).tolist())
    else:
        assert not (set(np.unique(sh).tolist()) & tr_shards), "shard overlap!"
        print("  train/val shard sets DISJOINT (kernels+stamps+seeds by construction)")
print("SWEEP_OK")
