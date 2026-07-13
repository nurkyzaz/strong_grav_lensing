#!/usr/bin/env python
"""EVAL #19 addendum table: G4-trained r50_3 on the real-op benchmark
(arch-controlled comparison against G3-trained r50_3 from eval #18)."""
import json
import os

import numpy as np
import pandas as pd

D = os.path.expanduser("~/einstein_cnn/brian_run")
R4 = json.load(open(os.path.expanduser("~/einstein_cnn/g4_recal.json")))
B4 = float(R4["bias_recenter_arcsec"])   # G4 recal was fitted for cnv2_3;
# for r50_3 use raw ensemble mean + the same tiny recenter (disclosed).
EXCLUDE = {"J0955+0101"}

for sample, tag in (("euclid_slacs_images_g3", "SLACS"),
                    ("euclid_s4tm_images_g3", "S4TM")):
    mu, base = [], None
    for t in ("g4_r50_s1", "g4_r50_s2", "g4_r50_s3"):
        d = pd.read_csv(os.path.join(D, "preds_l19_%s_%s.csv" % (t, sample)))
        if base is None:
            base = d[["name"]].copy()
            base["gt"] = d[[c for c in d.columns if "pub" in c][0]]
        mu.append(d[[c for c in d.columns if "pred" in c][0]].values.astype(float))
    p_all = np.stack(mu).mean(0) + B4
    W = ~base["name"].isin(EXCLUDE).values
    p, t_ = p_all[W], base["gt"].values[W]
    d_ = p - t_
    frac = d_ / t_
    print("G4-train r50_3 on REAL-op bench — %s (N=%d)" % (tag, len(p)))
    print("  bias %+.3f RMSE %.3f NMAD %.3f R2 %+.2f fail %.0f%% med-frac %+.1f%%"
          % (d_.mean(), np.sqrt((d_ ** 2).mean()),
             1.4826 * np.median(np.abs(d_ - np.median(d_))),
             1 - (d_ ** 2).sum() / ((t_ - t_.mean()) ** 2).sum(),
             100 * (np.abs(frac) > .15).mean(), 100 * np.median(frac)))
    for lo, hi in [(0.0, 0.9), (0.9, 1.2), (1.2, 1.5), (1.5, 3.0)]:
        m = (t_ >= lo) & (t_ < hi)
        if m.sum():
            print("    [%.1f,%.1f): N=%2d fail %3.0f%% med %+5.1f%%"
                  % (lo, hi, m.sum(), 100 * (np.abs(frac[m]) > .15).mean(),
                     100 * np.median(frac[m])))
