#!/usr/bin/env python
"""Per-lens LEMON-vs-ours comparison table for the email + paper (C16).

One row per lens: subsample, system, ground truth (+source), LEMON's predicted
theta_E, our predicted theta_E (Euclid-domain g4 cnv2 seed-ensemble). Covers the
three subsamples with a published theta_E GT (SLACS/EEL/COSMOS); ACS is arc-radius
only and omitted. Emits a CSV + a Markdown table + the two aggregate summaries
(LEMON-vs-GT and ours-vs-GT), so the email can show exactly what numbers come out
of the shared table.

Run: python analysis/lemon_perlens_comparison.py
Writes results/lemon_perlens_comparison.csv
"""
import csv
import glob
import math
import re
import statistics as st

PD = "tables/lemon_predictions"
OUT = "results/lemon_perlens_comparison.csv"


def ens(pattern, keyfn):
    pred, gt = {}, {}
    for f in sorted(glob.glob(pattern)):
        for r in csv.DictReader(open(f)):
            k = keyfn(r["name"])
            if k is None:
                continue
            pred.setdefault(k, []).append(float(r["theta_E_pred_arcsec"]))
            gt[k] = float(r["theta_E_pub_arcsec"])
    return {k: sum(v) / len(v) for k, v in pred.items()}, gt


def lemon(fn, keyfn):
    out = {}
    for r in csv.DictReader(open(fn)):
        k = keyfn(r["Name"])
        if k:
            out[k] = float(r["Einstein_radius(arcsec)"])
    return out


jS = lambda s: (re.search(r"(J\d{4}[+-]\d{4})", s) or [None])[0] if re.search(r"(J\d{4}[+-]\d{4})", s) else None
jE = lambda s: (re.search(r"(J\d{4})", s).group(1) if re.search(r"(J\d{4})", s) else None)
jC = lambda s: (re.search(r"(\d{4}[+-]\d{4})", s).group(1) if re.search(r"(\d{4}[+-]\d{4})", s) else None)

# SLACS: eval #19 Euclid-domain g4 cnv2 ensemble; GT (pub) = Bolton b_SIE
os_slacs, gt_slacs = ens("results/preds_l19_g4_cnv2_s*_euclid_slacs_images_g3.csv", jS)
lm_slacs = lemon(f"{PD}/lemon_slacs_predictions.csv", jS)
# EEL / COSMOS: lemon-q1b Euclid-domain preds; GT (pub) = Oldham / Faure
os_eel, gt_eel = ens("results/preds_lemonq1b_g4_cnv2_s*_EEL_euclid.csv", jE)
lm_eel = lemon(f"{PD}/lemon_eel_predictions.csv", jE)
os_cos, gt_cos = ens("results/preds_lemonq1b_g4_cnv2_s*_COSMOS_euclid.csv", jC)
lm_cos = lemon(f"{PD}/lemon_cosmos_predictions.csv", jC)

BLOCKS = [
    ("SLACS", "Bolton 2008 b_SIE", os_slacs, gt_slacs, lm_slacs),
    ("EEL", "Oldham 2017 PL+shear", os_eel, gt_eel, lm_eel),
    ("COSMOS", "Faure 2008 Lenstool", os_cos, gt_cos, lm_cos),
]

rows = []
for sub, src, ours, gt, lm in BLOCKS:
    for k in sorted(gt):
        if gt[k] > 0 and k in lm and k in ours:
            rows.append((sub, k, gt[k], src, lm[k], ours[k]))

with open(OUT, "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["subsample", "system", "ground_truth_theta_E", "GT_source",
                "LEMON_pred_theta_E", "our_pred_theta_E"])
    for r in rows:
        w.writerow([r[0], r[1], round(r[2], 3), r[3], round(r[4], 3), round(r[5], 3)])


def agg(pairs):
    d = [p - t for p, t in pairs]
    n = len(d)
    bias = sum(d) / n
    rmse = math.sqrt(sum(x * x for x in d) / n)
    med = st.median(d)
    nmad = 1.4826 * st.median([abs(x - med) for x in d])
    tb = sum(t for _, t in pairs) / n
    sstot = sum((t - tb) ** 2 for _, t in pairs)
    r2 = 1 - sum(x * x for x in d) / sstot if sstot > 0 else float("nan")
    return n, bias, rmse, nmad, r2


print("Per-lens table -> %s (%d lenses)\n" % (OUT, len(rows)))
print("| subsample | system | GT θ_E | LEMON pred | our pred |")
print("|---|---|---|---|---|")
for sub, k, gt, src, lm, ours in rows:
    print("| %s | %s | %.2f | %.2f | %.2f |" % (sub, k, gt, lm, ours))

print("\nAggregate from THIS table (predictions vs the GT column):")
print("%-22s %-28s %-28s" % ("", "LEMON vs GT", "OURS vs GT"))
allL, allO = [], []
for sub, src, ours, gt, lm in BLOCKS:
    keys = [k for k in gt if gt[k] > 0 and k in lm and k in ours]
    L = [(lm[k], gt[k]) for k in keys]
    O = [(ours[k], gt[k]) for k in keys]
    allL += L; allO += O
    nL, bL, rL, mL, r2L = agg(L)
    nO, bO, rO, mO, r2O = agg(O)
    print("%-10s N=%2d   bias%+.2f RMSE%.2f NMAD%.2f R²%+.2f | bias%+.2f RMSE%.2f NMAD%.2f R²%+.2f"
          % (sub, nL, bL, rL, mL, r2L, bO, rO, mO, r2O))
nL, bL, rL, mL, r2L = agg(allL)
nO, bO, rO, mO, r2O = agg(allO)
print("%-10s N=%2d   bias%+.2f RMSE%.2f NMAD%.2f R²%+.2f | bias%+.2f RMSE%.2f NMAD%.2f R²%+.2f"
      % ("POOLED", nL, bL, rL, mL, r2L, bO, rO, mO, r2O))
print("\nLEMON's PUBLISHED Table 3 (their 60 mixed lenses): bias -0.03 RMSE 0.14 NMAD 0.11 R² 0.53")
