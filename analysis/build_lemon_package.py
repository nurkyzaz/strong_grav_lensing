#!/usr/bin/env python
"""Build lemon_comparison_package/ — three aligned tables (ground truth / LEMON
predictions / our predictions) + a combined join, keyed on LEMON's EXACT 59-lens
list (29 SLACS + 12 EEL + 5 COSMOS + 13 ACS).

Ground truth is VERIFIED against the primary sources (2026-08-01):
  SLACS  -> Bolton 2008 b_SIE (tables/bolton08_table5.csv, all 29 exact)
  COSMOS -> Faure 2008 Table 4 (VizieR J/ApJS/176/19, all 5 exact)
  EEL    -> Oldham 2017 Table 2 (arXiv:1611.00008, all 12 checked; J1446 was
            corrected 0.41 -> 0.43 to match the paper)
  ACS    -> Pawase 2014: NO theta_E GT (arc radius only) -> excluded from combined
Run: python analysis/build_lemon_package.py
"""
import csv, glob, re, os, shutil

PKG = "lemon_comparison_package"
os.makedirs(f"{PKG}/raw_sources", exist_ok=True)
jS = lambda s: (re.search(r"(J\d{4}[+-]\d{4})", s) or [None])[0] if re.search(r"(J\d{4}[+-]\d{4})", s) else None
jE = lambda s: (re.search(r"(J\d{4})", s).group(1) if re.search(r"(J\d{4})", s) else None)
jC = lambda s: (re.search(r"(\d{4}[+-]\d{4})", s).group(1) if re.search(r"(\d{4}[+-]\d{4})", s) else None)
jA = lambda s: (re.search(r"ACS(\d{6}\.\d{2}[+-]\d{6}\.\d)", s).group(1) if re.search(r"ACS(\d{6}\.\d{2}[+-]\d{6}\.\d)", s) else s)

SUBS = [("SLACS", "lemon_slacs_predictions.csv", jS), ("EEL", "lemon_eel_predictions.csv", jE),
        ("COSMOS", "lemon_cosmos_predictions.csv", jC), ("ACS", "lemon_acs_predictions.csv", jA)]
lemon, order = {}, []
for sub, fn, kf in SUBS:
    for r in csv.DictReader(open(f"tables/lemon_predictions/{fn}")):
        k = kf(r["Name"])
        lemon[(sub, k)] = (round(float(r["Einstein_radius(arcsec)"]), 3),
                           round(float(r["Einstein_radius_uncertainty(arcsec)"]), 3))
        order.append((sub, k))

bol = {r["system"]: float(r["b_SIE_arcsec"]) for r in csv.DictReader(open("tables/bolton08_table5.csv"))}
eel_gt, cos_gt = {}, {}
for r in csv.DictReader(open("tables/lemon60_targets.csv")):
    g = r["gt_theta_E_arcsec"]
    if not g:
        continue
    if r["subsample"] == "EEL":
        eel_gt[jE(r["system"].replace(" ", ""))] = float(g)
    if r["subsample"] == "COSMOS-cand":
        cos_gt[jC(r["system"].replace(" ", ""))] = float(g)


def gt_of(sub, k):
    if sub == "SLACS":
        return bol.get(k), "Bolton et al. 2008 b_SIE", "verified vs bolton08_table5.csv"
    if sub == "EEL":
        return eel_gt.get(k), "Oldham et al. 2017 Table 2 (power-law+shear)", "verified vs Oldham 2017 Table 2 (arXiv:1611.00008)"
    if sub == "COSMOS":
        return cos_gt.get(k), "Faure et al. 2008 Table 4 (Lenstool Erad)", "verified vs VizieR J/ApJS/176/19"
    return None, "Pawase et al. 2014 - ARC RADIUS ONLY", "NO theta_E GT"


def ens(pattern, kf):
    d = {}
    for fp in sorted(glob.glob(pattern)):
        for r in csv.DictReader(open(fp)):
            k = kf(r["name"])
            if k:
                d.setdefault(k, []).append(float(r["theta_E_pred_arcsec"]))
    return {k: round(sum(v) / len(v), 3) for k, v in d.items()}


OUR = {"SLACS": ens("results/preds_l19_g4_cnv2_s*_euclid_slacs_images_g3.csv", jS),
       "EEL": ens("results/preds_lemonq1b_g4_cnv2_s*_EEL_euclid.csv", jE),
       "COSMOS": ens("results/preds_lemonq1b_g4_cnv2_s*_COSMOS_euclid.csv", jC),
       "ACS": ens("results/preds_lemonq1b_g4_cnv2_s*_ACS_euclid.csv", jA)}
our_of = lambda sub, k: OUR[sub].get(k)

with open(f"{PKG}/ground_truth.csv", "w", newline="") as f:
    w = csv.writer(f); w.writerow(["subsample", "system", "ground_truth_theta_E_arcsec", "GT_source", "GT_check"])
    for sub, k in order:
        g, src, chk = gt_of(sub, k); w.writerow([sub, k, ("" if g is None else round(g, 3)), src, chk])
with open(f"{PKG}/lemon_predictions.csv", "w", newline="") as f:
    w = csv.writer(f); w.writerow(["subsample", "system", "LEMON_theta_E_arcsec", "LEMON_uncertainty_arcsec"])
    for sub, k in order:
        p, s = lemon[(sub, k)]; w.writerow([sub, k, p, s])
with open(f"{PKG}/our_predictions.csv", "w", newline="") as f:
    w = csv.writer(f); w.writerow(["subsample", "system", "our_theta_E_arcsec"])
    for sub, k in order:
        o = our_of(sub, k); w.writerow([sub, k, ("" if o is None else o)])
comb = []
for sub, k in order:
    g, src, chk = gt_of(sub, k); o = our_of(sub, k); p = lemon[(sub, k)][0]
    if g is not None and o is not None:
        comb.append([sub, k, round(g, 3), src, p, round((p - g) / g * 100, 1), o, round((o - g) / g * 100, 1)])
with open(f"{PKG}/combined_comparison.csv", "w", newline="") as f:
    w = csv.writer(f); w.writerow(["subsample", "system", "ground_truth", "GT_source", "LEMON_pred", "LEMON_%err", "our_pred", "our_%err"])
    for r in comb:
        w.writerow(r)
for src in glob.glob("tables/lemon_predictions/*.csv") + ["tables/bolton08_table5.csv", "tables/lemon60_targets.csv"]:
    shutil.copy(src, f"{PKG}/raw_sources/")
print("package rebuilt: 59-lens ground_truth/lemon_predictions/our_predictions + %d-lens combined" % len(comb))
