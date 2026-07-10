#!/usr/bin/env python
"""L0 item 3: bootstrap CIs + R2/RMSE sample-composition math vs LEMON Table 3.

Analysis-only: reads existing per-lens prediction CSVs (default: eval-#14
ensemble, Euclidised SLACS). No model passes, no benchmark image access.

What it computes:
 1. 10k-bootstrap CIs for bias, RMSE, NMAD, R2, fail%. (Reviewers will ask at N=62.)
 2. R2 decomposition: R2 = 1 - MSE/Var(GT). Since R2 depends on the GT variance
    of the evaluation SAMPLE, we compute (a) the GT variance LEMON's sample must
    have for their (RMSE 0.14, R2 0.53) to co-exist, (b) our R2 counterfactually
    evaluated at THEIR sample variance, (c) the MSE we need for R2 >= 0.53 at
    OUR sample variance.
 3. Trim curve: metrics after removing the k worst lenses, k = 0..10
    (DIAGNOSTIC ONLY - not reportable as ours; quantifies tail leverage).
 4. Tail arithmetic: RMSE^2 = (1-f) RMS_ok^2 + f RMS_tail^2 -> the failure
    fraction f needed to reach RMSE targets given the measured ok/tail RMS.

Usage: l0_sample_math.py [preds.csv ...]
"""
import os
import sys
import numpy as np
import pandas as pd

LEMON = dict(bias=-0.03, rmse=0.14, nmad=0.11, r2=0.53)   # Table 3, theta_E col
EXCLUDE = {"J0955+0101"}
FAIL = 0.15
NBOOT = 10000
RNG = np.random.default_rng(20260710)

DEFAULT = os.path.expanduser(
    "~/einstein_cnn/brian_run/preds_einstein_cnn_euclid_sel_ensemble_euclid_slacs_images.csv")


def metrics(pred, gt):
    d = pred - gt
    frac = d / gt
    ss_tot = ((gt - gt.mean()) ** 2).sum()
    return dict(bias=d.mean(),
                rmse=float(np.sqrt((d ** 2).mean())),
                nmad=float(1.4826 * np.median(np.abs(d - np.median(d)))),
                r2=float(1.0 - (d ** 2).sum() / ss_tot),
                fail=float((np.abs(frac) > FAIL).mean()))


def report(path):
    d = pd.read_csv(path)
    if "name" in d.columns:
        d = d[~d["name"].isin(EXCLUDE)]
    pcol = [c for c in d.columns if "pred" in c][0]
    tcol = [c for c in d.columns if "pub" in c or "true" in c][0]
    pred, gt = d[pcol].values.astype(float), d[tcol].values.astype(float)
    names = d["name"].values if "name" in d.columns else np.arange(len(d)).astype(str)
    n = len(d)
    m0 = metrics(pred, gt)

    print("=" * 78)
    print("L0 SAMPLE MATH - %s  (N=%d, J0955 excluded)" % (os.path.basename(path), n))
    print("=" * 78)
    print("LEMON Table 3 (theta_E, 60 mixed-GT):  bias %+0.2f  RMSE %.2f  NMAD %.2f  R2 %.2f"
          % (LEMON["bias"], LEMON["rmse"], LEMON["nmad"], LEMON["r2"]))
    print("ours (point):                          bias %+0.3f  RMSE %.3f  NMAD %.3f  R2 %+.2f  fail %.0f%%"
          % (m0["bias"], m0["rmse"], m0["nmad"], m0["r2"], 100 * m0["fail"]))

    # 1) bootstrap
    boot = {k: np.empty(NBOOT) for k in m0}
    for b in range(NBOOT):
        idx = RNG.integers(0, n, n)
        mb = metrics(pred[idx], gt[idx])
        for k in mb:
            boot[k][b] = mb[k]
    print("\n[1] 10k-bootstrap 95%% CIs:")
    for k in ("bias", "rmse", "nmad", "r2", "fail"):
        lo, hi = np.percentile(boot[k], [2.5, 97.5])
        beats = None
        if k == "nmad":
            beats = (boot[k] < LEMON["nmad"]).mean()
        if k == "rmse":
            beats = (boot[k] < LEMON["rmse"]).mean()
        if k == "r2":
            beats = (boot[k] > LEMON["r2"]).mean()
        line = "  %-5s %+.3f  [%+.3f, %+.3f]" % (k, m0[k], lo, hi)
        if beats is not None:
            line += "   P(beats LEMON %s) = %.2f" % (k.upper(), beats)
        print(line)

    # 2) R2 sample-composition decomposition
    var_ours = float(gt.var())            # population var of GT in OUR sample
    mse_ours = float(((pred - gt) ** 2).mean())
    var_lemon = LEMON["rmse"] ** 2 / (1.0 - LEMON["r2"])
    r2_ours_at_lemon_var = 1.0 - mse_ours / var_lemon
    mse_needed = (1.0 - LEMON["r2"]) * var_ours
    print("\n[2] R2 depends on the evaluation sample's GT variance:")
    print("  our sample:   Var(theta_E)=%.4f (sd %.3f\"), MSE=%.4f -> R2 %+.2f"
          % (var_ours, np.sqrt(var_ours), mse_ours, m0["r2"]))
    print("  LEMON implied: Var=%.4f (sd %.3f\") from their RMSE+R2"
          % (var_lemon, np.sqrt(var_lemon)))
    print("  our MSE evaluated at THEIR sample variance -> R2 %+.2f" % r2_ours_at_lemon_var)
    print("  MSE needed for R2>=%.2f at OUR variance: %.4f (RMSE %.3f\", vs ours %.3f\")"
          % (LEMON["r2"], mse_needed, np.sqrt(mse_needed), m0["rmse"]))

    # 3) trim curve (diagnostic only)
    print("\n[3] Trim curve - remove k worst |frac err| lenses (DIAGNOSTIC ONLY):")
    order = np.argsort(-np.abs((pred - gt) / gt))
    for k in range(0, 11):
        keep = order[k:]
        mk = metrics(pred[keep], gt[keep])
        star = " <- crosses LEMON RMSE" if mk["rmse"] <= LEMON["rmse"] else ""
        print("  k=%2d (N=%2d): RMSE %.3f  NMAD %.3f  R2 %+.2f  fail %4.0f%%%s"
              % (k, len(keep), mk["rmse"], mk["nmad"], mk["r2"], 100 * mk["fail"], star))
        if k <= 4 and k > 0:
            print("      removed: %s" % names[order[k - 1]])

    # 4) tail arithmetic
    frac = (pred - gt) / gt
    ok = np.abs(frac) <= FAIL
    d = pred - gt
    rms_ok = float(np.sqrt((d[ok] ** 2).mean()))
    rms_tail = float(np.sqrt((d[~ok] ** 2).mean())) if (~ok).any() else 0.0
    print("\n[4] Tail arithmetic: RMS(ok)=%.3f\" (N=%d), RMS(tail)=%.3f\" (N=%d)"
          % (rms_ok, ok.sum(), rms_tail, (~ok).sum()))
    for target in (LEMON["rmse"], 0.16, 0.18):
        f = (target ** 2 - rms_ok ** 2) / (rms_tail ** 2 - rms_ok ** 2)
        print("  RMSE <= %.2f\" requires fail fraction <= %4.0f%% at current tail RMS"
              % (target, 100 * max(f, 0.0)))
    print("  (current fail: %.0f%%; conf-half already 10-13%% -> the gate story)"
          % (100 * m0["fail"]))


if __name__ == "__main__":
    paths = sys.argv[1:] if len(sys.argv) > 1 else [DEFAULT]
    for p in paths:
        report(os.path.expanduser(p))
