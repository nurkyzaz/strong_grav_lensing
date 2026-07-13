#!/usr/bin/env python
"""R0 ensemble column (P9-Q2): average the two architectures' TTA predictions
per lens. Derived from the SAME two benchmark prediction passes (no extra
model-on-benchmark pass). Sigma: quadrature mean (report-only)."""
import os
import pandas as pd
import numpy as np

D = os.path.expanduser("~/einstein_cnn/brian_run")
for sample in ("euclid_slacs_images", "euclid_s4tm_images"):
    a = pd.read_csv(os.path.join(D, "preds_einstein_cnn_euclid_sel_inceptionnext_%s.csv" % sample))
    b = pd.read_csv(os.path.join(D, "preds_einstein_cnn_euclid_sel_resnet_%s.csv" % sample))
    assert (a["name"] == b["name"]).all()
    out = a.copy()
    pcol = [c for c in a.columns if "pred" in c][0]
    out[pcol] = 0.5 * (a[pcol] + b[pcol])
    scols = [c for c in a.columns if "sigma" in c]
    for sc in scols:
        out[sc] = 0.5 * np.sqrt(a[sc] ** 2 + b[sc] ** 2)
    fn = os.path.join(D, "preds_einstein_cnn_euclid_sel_ensemble_%s.csv" % sample)
    out.to_csv(fn, index=False)
    print("wrote", fn, len(out))
