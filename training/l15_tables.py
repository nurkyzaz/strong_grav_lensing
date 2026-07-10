#!/usr/bin/env python
"""EVAL #15 tables (⛔ Nurkyz present, running count 15).

Reads the 12 members' per-lens TTA prediction CSVs (written by
predict_real_lenses_paltas.py — identical invocation to eval #14), builds the
all12 mixture ensemble, applies the FROZEN l1_recal.json constants
(b recentering, s sigma-scale; fitted on sim-val ONLY, frozen before this
eval), and prints: LEMON-convention table, standard metrics, confident-half,
recalibrated coverage, and per-theta_E-bin failure (the L0 tail readout).

Sigma combination = MIXTURE (same formula the frozen s was fitted on):
sigma_ens^2 = mean_i(sigma_i^2 + mu_i^2) - mu_ens^2.
"""
import json
import os
import numpy as np
import pandas as pd

D = os.path.expanduser("~/einstein_cnn/brian_run")
RECAL = json.load(open(os.path.expanduser("~/einstein_cnn/l1_recal.json")))
B = float(RECAL["bias_recenter_arcsec"])
S = float(RECAL["sigma_scale"])
EXCLUDE = {"J0955+0101"}
LEMON = dict(bias=-0.03, rmse=0.14, nmad=0.11, r2=0.53)
EVAL14 = {"euclid_slacs_images": dict(bias=+0.062, rmse=0.208, nmad=0.084, r2=0.33, fail=31.0),
          "euclid_s4tm_images": dict(bias=+0.129, rmse=0.250, nmad=0.092, r2=0.16, fail=30.0)}

MEMBER_CKPTS = [
    "einstein_cnn_euclid_sel_inceptionnext",
    "einstein_cnn_euclid_sel_inceptionnext_s1",
    "einstein_cnn_euclid_sel_inceptionnext_s2",
    "einstein_cnn_euclid_sel_inceptionnext_s3",
    "einstein_cnn_euclid_sel_inceptionnext_s4",
    "einstein_cnn_euclid_sel_inceptionnext_tinit",
    "einstein_cnn_euclid_sel_resnet",
    "einstein_cnn_euclid_sel_resnet_s1",
    "einstein_cnn_euclid_sel_resnet_s2",
    "einstein_cnn_euclid_sel_resnet_s3",
    "einstein_cnn_euclid_sel_resnet_s4",
    "einstein_cnn_euclid_sel_resnet_tinit",
]

print("EVAL #15 — all12 TTA ensemble, frozen b=%+.4f\" s=%.3f (sim-val)" % (B, S))
print("LEMON Table 3 ref: bias -0.03  RMSE 0.14  NMAD 0.11  R2 0.53")

for sample in ("euclid_slacs_images", "euclid_s4tm_images"):
    mus, sigs, base = [], [], None
    for m in MEMBER_CKPTS:
        fn = os.path.join(D, "preds_l15_%s_%s.csv" % (m, sample))
        d = pd.read_csv(fn)
        if base is None:
            base = d[["name"]].copy()
            base["gt"] = d[[c for c in d.columns if "pub" in c][0]]
        assert (d["name"] == base["name"]).all(), "row order mismatch " + fn
        mus.append(d[[c for c in d.columns if "pred" in c][0]].values.astype(float))
        scol = [c for c in d.columns if "sigma" in c]
        sigs.append(d[scol[0]].values.astype(float))
    M, SG = np.stack(mus), np.stack(sigs)
    mu = M.mean(0)
    sig = np.sqrt(np.maximum((SG ** 2 + M ** 2).mean(0) - mu ** 2, 1e-12))
    base["pred_raw"] = mu
    base["pred"] = mu + B
    base["sigma_recal"] = S * sig
    out_fn = os.path.join(D, "preds_l15_all12_%s.csv" % sample)
    base.rename(columns={"pred": "theta_E_pred_arcsec", "gt": "theta_E_pub_arcsec",
                         "sigma_recal": "theta_E_sigma_arcsec"}).to_csv(out_fn, index=False)

    W = base[~base["name"].isin(EXCLUDE)]
    p, t, sg = W["pred"].values, W["gt"].values, W["sigma_recal"].values
    d_ = p - t
    frac = d_ / t
    r2 = 1 - (d_ ** 2).sum() / ((t - t.mean()) ** 2).sum()
    nmad = 1.4826 * np.median(np.abs(d_ - np.median(d_)))
    fail = (np.abs(frac) > 0.15).mean()
    rel = sg / p
    conf = rel <= np.median(rel)
    z = np.abs(d_) / sg
    e14 = EVAL14[sample]
    tag = "SLACS (primary)" if "slacs" in sample else "S4TM (secondary)"

    print("\n=== %s  N=%d (J0955 excluded) ===" % (tag, len(W)))
    print("  eval #14 (pair):  bias %+.3f  RMSE %.3f  NMAD %.3f  R2 %+.2f  fail %.0f%%"
          % (e14["bias"], e14["rmse"], e14["nmad"], e14["r2"], e14["fail"]))
    print("  eval #15 (all12): bias %+.3f  RMSE %.3f  NMAD %.3f  R2 %+.2f  fail %.0f%%"
          % (d_.mean(), np.sqrt((d_ ** 2).mean()), nmad, r2, 100 * fail))
    print("  median frac %+.1f%% | conf-half fail %.0f%% | recal cov 68/95: %.0f%%/%.0f%%"
          % (100 * np.median(frac), 100 * (np.abs(frac[conf]) > 0.15).mean(),
             100 * (z <= 1).mean(), 100 * (z <= 1.96).mean()))
    print("  per-theta_E bins (fail%% / median frac):")
    for lo, hi in [(0.0, 0.9), (0.9, 1.2), (1.2, 1.5), (1.5, 3.0)]:
        m_ = (t >= lo) & (t < hi)
        if m_.sum() == 0:
            continue
        print("    [%.1f,%.1f): N=%2d  %3.0f%%  %+5.1f%%"
              % (lo, hi, m_.sum(), 100 * (np.abs(frac[m_]) > 0.15).mean(),
                 100 * np.median(frac[m_])))
    print("  wrote %s" % out_fn)
