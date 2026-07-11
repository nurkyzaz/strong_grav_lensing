#!/usr/bin/env python
"""G3 merge label verification (runs BEFORE any shard deletion)."""
import h5py
import numpy as np

for fn in ("/home/user/nurkyz/einstein_cnn/train_g3_100k.h5",
           "/home/user/nurkyz/einstein_cnn/val_g3_5k.h5"):
    with h5py.File(fn, "r") as f:
        th = f["theta_E"][:]
        assert (th == 0).sum() == 0, "ZERO labels in " + fn
        for k in ("mass_e1", "mass_e2", "deflector_index", "deflector_mag",
                  "arc_snr", "arc_extent"):
            assert k in f, k + " missing in " + fn
        print(fn.split("/")[-1], "n=%d theta[%.2f,%.2f] med %.3f OK"
              % (len(th), th.min(), th.max(), np.median(th)))
        for lo, hi in ((0.45, .8), (.8, 1.2), (1.2, 1.7), (1.7, 2.3)):
            m = (th >= lo) & (th < hi)
            print("   theta [%.2f,%.2f): frac %.3f" % (lo, hi, m.mean()))
print("MERGE_LABELS_OK")
