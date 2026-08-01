#!/usr/bin/env python
"""LEMON head-to-head, recomputed on the EXACT lenses LEMON reports (C16).

Inputs now in the repo (received from Nurkyz 2026-07-22 — LEMON's per-lens
Euclidised-HST predictions, all four Table-3 subsamples):
    tables/lemon_predictions/lemon_{slacs,eel,cosmos,acs}_predictions.csv
Ground truth: Bolton et al. 2008 b_SIE (tables/bolton08_table5.csv), which is
also the `theta_E_pub` column in our saved per-lens prediction CSVs.

This resolves the long-open "which 29 SLACS" question (their SLACS file names
each lens) and lets us score LEMON's OWN predictions against Bolton, alongside
ours on the identical 29 (row-filter on results/preds_l19_* and l21_*, per the
LEMON-plan checklist — no benchmark re-run).

Run: python analysis/lemon_headtohead_recompute.py
Writes results/lemon_vs_ours_slacs29.csv
"""
import csv
import glob
import math
import re
import statistics as st

PRED_DIR = "tables/lemon_predictions"
OUT = "results/lemon_vs_ours_slacs29.csv"


def jname(s):
    m = re.search(r"(J\d{4}[+-]\d{4})", s)
    return m.group(1) if m else None


# LEMON's 29 SLACS predictions (Euclidised HST, their CNN)
lemon = {}
for r in csv.DictReader(open(f"{PRED_DIR}/lemon_slacs_predictions.csv")):
    lemon[jname(r["Name"])] = float(r["Einstein_radius(arcsec)"])
names = set(lemon)

# GT = Bolton b_SIE (== theta_E_pub in our saved CSVs; cross-checks exactly)
gt = {}
for r in csv.DictReader(open(
        "results/preds_l19_g4_cnv2_s1_euclid_slacs_images_g3.csv")):
    gt[r["name"]] = float(r["theta_E_pub_arcsec"])


def ensemble(pattern):
    acc = {}
    for f in sorted(glob.glob(pattern)):
        for r in csv.DictReader(open(f)):
            acc.setdefault(r["name"], []).append(
                float(r["theta_E_pred_arcsec"]))
    return {k: sum(v) / len(v) for k, v in acc.items()}


ours_euclid = ensemble("results/preds_l19_g4_cnv2_s*_euclid_slacs_images_g3.csv")
ours_native = ensemble("results/preds_l21_g4n_cnv2_s*_real_slacs_images.csv")


def metrics(pred):
    d, frac, ts = [], [], []
    for j in names:
        if j in pred and j in gt:
            p, t = pred[j], gt[j]
            d.append(p - t)
            frac.append((p - t) / t)
            ts.append(t)
    n = len(d)
    bias = sum(d) / n
    rmse = math.sqrt(sum(x * x for x in d) / n)
    med = st.median(d)
    nmad = 1.4826 * st.median([abs(x - med) for x in d])
    tb = sum(ts) / n
    r2 = 1 - sum(x * x for x in d) / sum((t - tb) ** 2 for t in ts)
    fail = sum(1 for f in frac if abs(f) > 0.15) / n
    return dict(N=n, bias=bias, RMSE=rmse, NMAD=nmad, R2=r2,
                med_frac_pct=100 * st.median(frac), fail_pct=100 * fail)


rows = [("LEMON_euclidised_CNN", metrics(lemon)),
        ("OURS_euclid_g4_cnv2_ens", metrics(ours_euclid)),
        ("OURS_native_g4n_cnv2_ens", metrics(ours_native))]

print("On the EXACT 29 LEMON SLACS, GT = Bolton b_SIE:")
print("%-26s N  bias   RMSE  NMAD  R2     medfrac fail" % "model")
for lab, m in rows:
    print("%-26s %2d %+.3f %.3f %.3f %+.2f  %+.1f%%  %.0f%%"
          % (lab, m["N"], m["bias"], m["RMSE"], m["NMAD"], m["R2"],
             m["med_frac_pct"], m["fail_pct"]))

with open(OUT, "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["model", "N", "bias", "RMSE", "NMAD", "R2",
                "median_frac_pct", "fail_gt15pct_pct"])
    for lab, m in rows:
        w.writerow([lab, m["N"], round(m["bias"], 4), round(m["RMSE"], 4),
                    round(m["NMAD"], 4), round(m["R2"], 3),
                    round(m["med_frac_pct"], 1), round(m["fail_pct"], 0)])
print("wrote", OUT)
