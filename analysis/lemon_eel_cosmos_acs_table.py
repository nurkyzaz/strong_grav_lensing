#!/usr/bin/env python
"""LEMON head-to-head, domain A subsamples EEL / COSMOS / ACS (C16).

Completes the SLACS-29 head-to-head (analysis/lemon_headtohead_recompute.py)
with the other three Table-3 subsamples, on the EXACT lenses LEMON reports.

GT (per-lens, already matched, = the convention LEMON scored against):
  EEL    -> Oldham et al. 2017 power-law + external shear theta_E
  COSMOS -> Faure et al. 2008 Lenstool SIE + shear theta_E
  ACS    -> NONE (arc radius only; theta_E_pub = 0 in our files) -> excluded.
GT is read from theta_E_pub_arcsec in our own per-lens CSVs (per-lens matched).

Predictions compared:
  LEMON (their CNN, Euclidised)  tables/lemon_predictions/lemon_{eel,cosmos}_predictions.csv
  OURS Euclid-domain (g4 cnv2 seed-ens)   results/preds_lemonq1b_g4_cnv2_s*_{SUB}_euclid.csv
  OURS native-HST     (g4n cnv2 seed-ens) results/preds_lemonq1b_g4n_cnv2_s*_{SUB}_native.csv

Run: python analysis/lemon_eel_cosmos_acs_table.py
Writes results/lemon_vs_ours_eel_cosmos_acs.csv
"""
import csv
import glob
import math
import re
import statistics as st

PD = "tables/lemon_predictions"
OUT = "results/lemon_vs_ours_eel_cosmos_acs.csv"


def eel_key(s):
    m = re.search(r"(J\d{4})", s)
    return m.group(1) if m else None


def cos_key(s):
    m = re.search(r"(\d{4}[+-]\d{4})", s)
    return m.group(1) if m else None


def load_ours(pattern, keyfn):
    """seed-ensemble mean pred + per-lens GT (theta_E_pub) keyed by keyfn."""
    preds, gt = {}, {}
    for f in sorted(glob.glob(pattern)):
        for r in csv.DictReader(open(f)):
            k = keyfn(r["name"])
            if k is None:
                continue
            preds.setdefault(k, []).append(float(r["theta_E_pred_arcsec"]))
            gt[k] = float(r["theta_E_pub_arcsec"])
    return {k: sum(v) / len(v) for k, v in preds.items()}, gt


def load_lemon(fn, keyfn):
    out = {}
    for r in csv.DictReader(open(fn)):
        k = keyfn(r["Name"])
        if k is not None:
            out[k] = float(r["Einstein_radius(arcsec)"])
    return out


def metrics(pred, gt, keys):
    d, frac, ts = [], [], []
    for k in keys:
        if k in pred and k in gt and gt[k] > 0:
            d.append(pred[k] - gt[k])
            frac.append((pred[k] - gt[k]) / gt[k])
            ts.append(gt[k])
    n = len(d)
    if n == 0:
        return None
    bias = sum(d) / n
    rmse = math.sqrt(sum(x * x for x in d) / n)
    med = st.median(d)
    nmad = 1.4826 * st.median([abs(x - med) for x in d])
    tb = sum(ts) / n
    sstot = sum((t - tb) ** 2 for t in ts)
    r2 = 1 - sum(x * x for x in d) / sstot if sstot > 0 else float("nan")
    fail = sum(1 for f in frac if abs(f) > 0.15) / n
    return dict(N=n, bias=bias, RMSE=rmse, NMAD=nmad, R2=r2,
                medfrac=100 * st.median(frac), fail=100 * fail)


SUBS = [("EEL", eel_key), ("COSMOS", cos_key)]
rows = []
pooled = {"LEMON": ({}, {}), "OURS_euclid": ({}, {}), "OURS_native": ({}, {})}

for sub, kf in SUBS:
    oe_p, gt = load_ours("results/preds_lemonq1b_g4_cnv2_s*_%s_euclid.csv" % sub, kf)
    on_p, _ = load_ours("results/preds_lemonq1b_g4n_cnv2_s*_%s_native.csv" % sub, kf)
    lem = load_lemon("%s/lemon_%s_predictions.csv" % (PD, sub.lower()), kf)
    keys = [k for k in gt if gt[k] > 0]
    for lab, pred in [("LEMON", lem), ("OURS_euclid", oe_p), ("OURS_native", on_p)]:
        m = metrics(pred, gt, keys)
        rows.append((sub, lab, m))
        for k in keys:
            if k in pred and gt.get(k, 0) > 0:
                pooled[lab][0][(sub, k)] = pred[k]
                pooled[lab][1][(sub, k)] = gt[k]

# pooled EEL+COSMOS
for lab in ("LEMON", "OURS_euclid", "OURS_native"):
    p, g = pooled[lab]
    rows.append(("EEL+COSMOS", lab, metrics(p, g, list(g.keys()))))


def fmt(m):
    if m is None:
        return "   no GT"
    return ("N=%2d bias %+.3f RMSE %.3f NMAD %.3f R2 %+.2f medfrac %+.1f%% fail %.0f%%"
            % (m["N"], m["bias"], m["RMSE"], m["NMAD"], m["R2"], m["medfrac"], m["fail"]))


print("LEMON head-to-head, EEL / COSMOS (ACS excluded: arc-radius GT only)\n")
last = None
for sub, lab, m in rows:
    if sub != last:
        print("== %s ==" % sub)
        last = sub
    print("  %-13s %s" % (lab, fmt(m)))

with open(OUT, "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["subsample", "model", "N", "bias", "RMSE", "NMAD", "R2",
                "median_frac_pct", "fail_gt15pct_pct"])
    for sub, lab, m in rows:
        if m:
            w.writerow([sub, lab, m["N"], round(m["bias"], 4), round(m["RMSE"], 4),
                        round(m["NMAD"], 4), round(m["R2"], 3),
                        round(m["medfrac"], 1), round(m["fail"], 0)])
print("\nwrote", OUT)
