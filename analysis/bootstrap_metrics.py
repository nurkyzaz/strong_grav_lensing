#!/usr/bin/env python3
"""Bootstrap confidence intervals for the headline theta_E metrics (reviewer
concern R6: point estimates on N=62/40 need CIs). Reads a predictions CSV with
columns name, theta_E_pred_arcsec, theta_E_pub_arcsec[, theta_E_sigma_arcsec]
and reports R2, NMAD, RMSE, bias, and fail-rate with 68% bootstrap CIs.

Usage: python analysis/bootstrap_metrics.py <preds.csv> [n_boot]
"""
import sys, csv
import numpy as np

FAIL_THRESH = 0.15  # |fractional error| > 15% == failure (paper definition)

def load(path):
    pred, pub = [], []
    with open(path) as f:
        for r in csv.DictReader(f):
            try:
                pred.append(float(r["theta_E_pred_arcsec"]))
                pub.append(float(r["theta_E_pub_arcsec"]))
            except (KeyError, ValueError):
                continue
    return np.asarray(pred), np.asarray(pub)

def metrics(pred, pub):
    resid = pred - pub
    ss_res = np.sum(resid**2)
    ss_tot = np.sum((pub - pub.mean())**2)
    r2 = 1.0 - ss_res / ss_tot
    nmad = 1.4826 * np.median(np.abs(resid - np.median(resid)))
    rmse = np.sqrt(np.mean(resid**2))
    bias = np.mean(resid)
    fail = np.mean(np.abs(resid) / pub > FAIL_THRESH)
    return dict(R2=r2, NMAD=nmad, RMSE=rmse, bias=bias, fail=fail)

def bootstrap(pred, pub, n_boot=10000, seed=0):
    rng = np.random.default_rng(seed)
    n = len(pred)
    keys = ["R2", "NMAD", "RMSE", "bias", "fail"]
    samples = {k: [] for k in keys}
    for _ in range(n_boot):
        idx = rng.integers(0, n, n)
        m = metrics(pred[idx], pub[idx])
        for k in keys:
            samples[k].append(m[k])
    ci = {}
    for k in keys:
        lo, hi = np.percentile(samples[k], [16, 84])  # 68% CI
        ci[k] = (lo, hi)
    return ci

if __name__ == "__main__":
    path = sys.argv[1]
    n_boot = int(sys.argv[2]) if len(sys.argv) > 2 else 10000
    pred, pub = load(path)
    pt = metrics(pred, pub)
    ci = bootstrap(pred, pub, n_boot)
    print(f"file: {path}   N={len(pred)}   n_boot={n_boot}")
    for k in ["R2", "NMAD", "RMSE", "bias", "fail"]:
        lo, hi = ci[k]
        unit = "" if k in ("R2",) else ("" if k == "fail" else " arcsec")
        if k == "fail":
            print(f"  {k:5s} = {pt[k]*100:6.1f}%   68% CI [{lo*100:5.1f}, {hi*100:5.1f}]%")
        else:
            print(f"  {k:5s} = {pt[k]:+.4f}{unit}   68% CI [{lo:+.4f}, {hi:+.4f}]")
