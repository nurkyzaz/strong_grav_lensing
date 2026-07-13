#!/usr/bin/env python
"""Confident-half failure rates (sigma-gated, the project headline metric) +
real-GT coverage with the sim-val-frozen recalibration factors."""
import os
import glob
import pandas as pd
import numpy as np

D = os.path.expanduser("~/einstein_cnn/brian_run")
RECAL = {"inceptionnext": 1.320, "resnet": 1.712, "ensemble": None}
EXCLUDE = {"J0955+0101"}

for fn in sorted(glob.glob(os.path.join(D, "preds_einstein_cnn_euclid_sel_*_real_*.csv"))):
    d = pd.read_csv(fn)
    if "name" in d.columns:
        d = d[~d["name"].isin(EXCLUDE)]
    pcol = [c for c in d.columns if "pred" in c][0]
    tcol = [c for c in d.columns if "pub" in c or "true" in c][0]
    scols = [c for c in d.columns if "sigma" in c]
    frac = (d[pcol] - d[tcol]) / d[tcol]
    tag = os.path.basename(fn).replace("preds_einstein_cnn_euclid_sel_", "").replace(".csv", "")
    line = "%-34s N=%3d fail %2.0f%%" % (tag, len(d), 100 * (frac.abs() > 0.15).mean())
    if scols:
        rel = d[scols[0]] / d[pcol]
        conf = rel <= rel.median()
        line += " | conf-half fail %2.0f%%" % (100 * (frac[conf].abs() > 0.15).mean())
        arch = tag.split("_real")[0]
        s = RECAL.get(arch)
        if s:
            z = (d[pcol] - d[tcol]).abs() / (s * d[scols[0]])
            line += " | recal 68/95%% cov: %2.0f/%2.0f%%" % (
                100 * (z <= 1).mean(), 100 * (z <= 1.96).mean())
    print(line)
