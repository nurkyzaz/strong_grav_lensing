#!/usr/bin/env python3
"""Uncertainty calibration + confidence-gating trade-off (reviewer concern R7).
Reads a predictions CSV with theta_E_pred_arcsec, theta_E_pub_arcsec,
theta_E_sigma_arcsec and reports:
  (1) empirical coverage at 1sigma/2sigma (nominal 68.3%/95.5%) -> calibration;
  (2) the failure-rate vs retained-fraction trade-off when gating on sigma.

Usage: python analysis/calibration_gating.py <preds.csv>
"""
import sys, csv
import numpy as np

FAIL = 0.15

def load(path):
    p, g, s = [], [], []
    with open(path) as f:
        for r in csv.DictReader(f):
            try:
                p.append(float(r["theta_E_pred_arcsec"]))
                g.append(float(r["theta_E_pub_arcsec"]))
                s.append(float(r["theta_E_sigma_arcsec"]))
            except (KeyError, ValueError):
                continue
    return map(np.asarray, (p, g, s))

if __name__ == "__main__":
    path = sys.argv[1]
    pred, pub, sig = load(path)
    n = len(pred)
    resid = np.abs(pred - pub)
    z = resid / sig
    cov1 = np.mean(z <= 1.0)
    cov2 = np.mean(z <= 2.0)
    print(f"file: {path}   N={n}")
    print(f"  coverage @1sigma = {cov1*100:5.1f}%  (nominal 68.3%)")
    print(f"  coverage @2sigma = {cov2*100:5.1f}%  (nominal 95.5%)")
    # recalibration factor so 1-sigma coverage hits 68.3% (temperature on sigma)
    # scale s.t. median(|resid|/(k*sigma)) matches ~0.6745 (the 68% half-width)
    k = np.percentile(z, 68.3) / 1.0
    print(f"  suggested global sigma-scale k = {k:.2f}  (multiply sigma by k to calibrate 1sigma)")
    # gating trade-off: sort by sigma ascending (most confident first)
    order = np.argsort(sig)
    fe = resid[order] / pub[order]
    print("  gating trade-off (retain most-confident fraction -> failure rate):")
    for f in [0.25, 0.5, 0.6, 0.75, 0.9, 1.0]:
        m = max(1, int(round(f * n)))
        fail = np.mean(fe[:m] > FAIL)
        print(f"     retain {int(f*100):3d}%  (N={m:2d})  fail = {fail*100:5.1f}%")
