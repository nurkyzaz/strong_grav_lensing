#!/usr/bin/env python
"""EVAL #19 — the 2x2 operator cross-diagnostic, PRE-REGISTERED question:
is the SLACS regression in eval #18 caused by the TRAINING operator or the
BENCHMARK operator? Cells: rows = training generation (G4=gauss-op,
G3=real-op), cols = benchmark operator (gauss, real). Diagonals = evals
#17/#18 (reprinted for reference); off-diagonals computed here from the
frozen primary of each generation with ITS OWN frozen recal."""
import json
import os

import numpy as np
import pandas as pd

D = os.path.expanduser("~/einstein_cnn/brian_run")
R4 = json.load(open(os.path.expanduser("~/einstein_cnn/g4_recal.json")))
R3 = json.load(open(os.path.expanduser("~/einstein_cnn/g3_recal.json")))
EXCLUDE = {"J0955+0101"}

CELLS = [
    # (label, members, recal, sample file prefix, preds tag)
    ("G4-train on REAL-op bench", R4["members"], R4, "euclid_slacs_images_g3", "l19"),
    ("G4-train on REAL-op bench (S4TM)", R4["members"], R4, "euclid_s4tm_images_g3", "l19"),
    ("G3-train on GAUSS-op bench", R3["members"], R3, "euclid_slacs_images", "l19"),
    ("G3-train on GAUSS-op bench (S4TM)", R3["members"], R3, "euclid_s4tm_images", "l19"),
]

REF = [
    ("DIAG #17 G4-train/gauss-bench SLACS", -0.005, 0.145, 0.047, 0.67, 11.0),
    ("DIAG #18 G3-train/real-bench  SLACS", -0.059, 0.201, 0.083, 0.37, 23.0),
    ("DIAG #17 G4-train/gauss-bench S4TM ", 0.050, 0.163, 0.081, 0.64, 30.0),
    ("DIAG #18 G3-train/real-bench  S4TM ", 0.027, 0.117, 0.082, 0.81, 22.0),
]
print("EVAL #19 — operator 2x2 cross-diagnostic")
for nm, b, rm, nd, r2, fl in REF:
    print("  %s: bias %+.3f RMSE %.3f NMAD %.3f R2 %+.2f fail %.0f%%"
          % (nm, b, rm, nd, r2, fl))
print()

for label, members, R, sample, tag in CELLS:
    mu_all, base = {}, None
    for t in members:
        fn = os.path.join(D, "preds_%s_%s_%s.csv" % (tag, t, sample))
        d = pd.read_csv(fn)
        if base is None:
            base = d[["name"]].copy()
            base["gt"] = d[[c for c in d.columns if "pub" in c][0]]
        mu_all[t] = d[[c for c in d.columns if "pred" in c][0]].values.astype(float)
    M = np.stack([mu_all[t] for t in members])
    p_all = M.mean(0) + float(R["bias_recenter_arcsec"])
    W = ~base["name"].isin(EXCLUDE).values
    p, t_ = p_all[W], base["gt"].values[W]
    d_ = p - t_
    frac = d_ / t_
    print("%s  (N=%d, members=%s)" % (label, len(p), ",".join(members)))
    print("  bias %+.3f RMSE %.3f NMAD %.3f R2 %+.2f fail %.0f%%  med-frac %+.1f%%"
          % (d_.mean(), np.sqrt((d_ ** 2).mean()),
             1.4826 * np.median(np.abs(d_ - np.median(d_))),
             1 - (d_ ** 2).sum() / ((t_ - t_.mean()) ** 2).sum(),
             100 * (np.abs(frac) > .15).mean(), 100 * np.median(frac)))
    for lo, hi in [(0.0, 0.9), (0.9, 1.2), (1.2, 1.5), (1.5, 3.0)]:
        m = (t_ >= lo) & (t_ < hi)
        if m.sum():
            print("    [%.1f,%.1f): N=%2d fail %3.0f%%  med %+5.1f%%"
                  % (lo, hi, m.sum(), 100 * (np.abs(frac[m]) > .15).mean(),
                     100 * np.median(frac[m])))
    print()
print("EVAL19_TABLES_DONE")
