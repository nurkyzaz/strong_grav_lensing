#!/usr/bin/env python
"""EVAL #15 attribution: recombine the EXISTING 24 member prediction CSVs
(from the authorized eval-#15 passes) into sub-ensembles. No model touches the
benchmark here — same precedent as eval #14's ensemble column ("derived from
the same prediction passes, no extra benchmark pass"). Frozen b, s applied
identically; note s was fitted for the all12 mixture (disclosed)."""
import json
import os
import numpy as np
import pandas as pd

D = os.path.expanduser("~/einstein_cnn/brian_run")
R = json.load(open(os.path.expanduser("~/einstein_cnn/l1_recal.json")))
B, S = float(R["bias_recenter_arcsec"]), float(R["sigma_scale"])
EXCLUDE = {"J0955+0101"}

INC = ["einstein_cnn_euclid_sel_inceptionnext"] + \
      ["einstein_cnn_euclid_sel_inceptionnext_s%d" % i for i in (1, 2, 3, 4)]
RES = ["einstein_cnn_euclid_sel_resnet"] + \
      ["einstein_cnn_euclid_sel_resnet_s%d" % i for i in (1, 2, 3, 4)]
TIN = ["einstein_cnn_euclid_sel_inceptionnext_tinit", "einstein_cnn_euclid_sel_resnet_tinit"]
VARIANTS = {
    "pair_s0(TTA)": [INC[0], RES[0]],
    "inc5": INC, "res5": RES,
    "scratch10": INC + RES,
    "tinit2": TIN,
    "all12": INC + RES + TIN,
}

def load(m, sample):
    d = pd.read_csv(os.path.join(D, "preds_l15_%s_%s.csv" % (m, sample)))
    p = d[[c for c in d.columns if "pred" in c][0]].values.astype(float)
    s = d[[c for c in d.columns if "sigma" in c][0]].values.astype(float)
    return d["name"].values, p, s, d[[c for c in d.columns if "pub" in c][0]].values.astype(float)

for sample in ("euclid_slacs_images", "euclid_s4tm_images"):
    print("\n=== %s ===" % sample)
    print("%-14s %6s %6s %6s %6s %5s %9s" % ("variant", "bias", "RMSE", "NMAD", "R2", "fail", "conf-half"))
    for name, members in VARIANTS.items():
        Ms, Ss = [], []
        for m in members:
            nm, p, s, gt = load(m, sample)
            Ms.append(p); Ss.append(s)
        M, SG = np.stack(Ms), np.stack(Ss)
        mu = M.mean(0) + B
        sig = S * np.sqrt(np.maximum((SG ** 2 + M ** 2).mean(0) - M.mean(0) ** 2, 1e-12))
        keep = ~pd.Series(nm).isin(EXCLUDE).values
        p_, t_, sg_ = mu[keep], gt[keep], sig[keep]
        d_ = p_ - t_
        frac = d_ / t_
        r2 = 1 - (d_ ** 2).sum() / ((t_ - t_.mean()) ** 2).sum()
        nmad = 1.4826 * np.median(np.abs(d_ - np.median(d_)))
        rel = sg_ / p_
        conf = rel <= np.median(rel)
        print("%-14s %+.3f  %.3f  %.3f  %+.2f  %3.0f%%  %3.0f%%"
              % (name, d_.mean(), np.sqrt((d_ ** 2).mean()), nmad, r2,
                 100 * (np.abs(frac) > 0.15).mean(),
                 100 * (np.abs(frac[conf]) > 0.15).mean()))
