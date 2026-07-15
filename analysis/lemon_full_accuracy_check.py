#!/usr/bin/env python
"""Recompute LEMON's reported accuracy per subsample AND combined, against
GT independently fetched from the exact papers/tables their own methods
section cites (Nurkyz request 2026-07-15):
  EELs:    Oldham & Auger 2017 (MNRAS 465 3185) Table 2 - R_Ein, elliptical
           power-law + external shear model.
  COSMOS:  Faure et al. 2008 (ApJS 176 19) Table 4 - Erad, the "erratum"
           SIE(+shear) Einstein radius (corrects Scoville 2007).
  ACS/Pawase: Pawase et al. 2014 (MNRAS 439 3392) Table 3 - arc radius
           (LEMON's own disclosed theta_E substitute; no mass model GT).
  SLACS:   Bolton 2008 Table 5 b_SIE (already verified 2026-07-15, R2=-4.26).
Purpose: check whether LEMON's own predictions reproduce their published
Table 3 aggregate (bias -0.03, RMSE 0.14, NMAD 0.11, R2 0.53, N~60)."""
import os
import re

import numpy as np
import pandas as pd

DL = "/Users/nurkyz/Downloads"
OUT = "/Users/nurkyz/Desktop/LensFusion/lemon_headtohead"

EEL_GT = {  # Oldham & Auger 2017 Table 2, R_Ein
    "J0837": 0.56, "J0901": 0.67, "J0913": 0.42, "J1125": 0.86, "J1144": 0.68,
    "J1218": 0.68, "J1323": 0.31, "J1347": 0.43, "J1446": 0.41, "J1605": 0.64,
    "J1606": 0.52, "J1619": 0.50, "J2228": 0.60,
}
COSMOS_GT = {  # Faure et al. 2008 Table 4, Erad
    "0012+2015": 0.67, "0018+3845": 1.32, "0038+4133": 0.73, "0047+5023": 1.41,
    "0049+5128": 2.09, "0050+4901": 1.69, "0056+1226": 1.64, "0124+5121": 0.86,
    "0211+1139": 3.14, "0216+2955": 1.75, "0227+0451": 2.64, "5857+5949": 2.28,
    "5914+1219": 1.65, "5921+0638": 0.70, "5941+3628": 1.17, "5947+4752": 1.97,
}
ACS_GT = {  # Pawase et al. 2014 Table 3, arc radius (theta_E substitute)
    "001423.02-302109.8": 1.52, "001426.26-302255.9": 1.00, "011018.22+193819.5": 3.10,
    "084710.65+344826.4": 1.98, "095139.44+684731.2": 0.77, "103751.40-124327.5": 1.48,
    "122332.64-123940.3": 0.36, "130042.73+280523.3": 1.08, "140237.11+542716.4": 1.85,
    "140339.94+541633.3": 0.90, "171817.43+593146.4": 2.35, "221501.12-135822.9": 0.82,
    "235130.60-261459.7": 3.32,
}


def met(p, t):
    d = p - t
    return dict(bias=d.mean(), rmse=float(np.sqrt((d ** 2).mean())),
                nmad=float(1.4826 * np.median(np.abs(d - np.median(d)))),
                r2=float(1 - (d ** 2).sum() / ((t - t.mean()) ** 2).sum()),
                fail=float((np.abs(d / t) > 0.15).mean()), n=len(p))


def row(label, m):
    print("  %-30s N=%3d bias %+.3f RMSE %.3f NMAD %.3f R2 %+.2f fail %.0f%%"
          % (label, m["n"], m["bias"], m["rmse"], m["nmad"], m["r2"], 100 * m["fail"]))


all_pred, all_gt, all_sub = [], [], []

# --- SLACS-29 (already verified; reload for the combined check) ---
slacs = pd.read_csv(os.path.join(DL, "LEMON_SLACS_predictions.csv")).dropna(subset=["Name"])
slacs["jname"] = slacs["Name"].apply(lambda s: re.search(r"(J\d{4}[+-]\d{4})", s).group(1))
bolton = {}
for line in open("/tmp/bolton_table5_raw.tsv"):
    if not line.startswith("       ") and not re.match(r"^\s*\d", line):
        continue
    parts = line.rstrip("\n").split("\t")
    if len(parts) > 2:
        try:
            bolton[parts[1].strip()] = float(parts[2].strip())
        except ValueError:
            pass
slacs["gt"] = slacs["jname"].map(bolton)
slacs = slacs.dropna(subset=["gt"])
m_slacs = met(slacs["Einstein_radius(arcsec)"].values, slacs["gt"].values)
row("SLACS-29 (Bolton+08 b_SIE)", m_slacs)
all_pred += list(slacs["Einstein_radius(arcsec)"]); all_gt += list(slacs["gt"])
all_sub += ["SLACS"] * len(slacs)

# --- EELs ---
eel = pd.read_csv(os.path.join(DL, "LEMON_EEL_predictions.csv")).dropna(subset=["Name"])
eel["jname"] = eel["Name"].apply(lambda s: re.search(r"EEL(J\d{4})", s).group(1))
eel["gt"] = eel["jname"].map(EEL_GT)
missing = eel[eel["gt"].isna()]["jname"].tolist()
if missing:
    print("EEL names with no GT match:", missing)
eel = eel.dropna(subset=["gt"])
m_eel = met(eel["Einstein_radius(arcsec)"].values, eel["gt"].values)
row("EELs (Oldham&Auger17 R_Ein)", m_eel)
all_pred += list(eel["Einstein_radius(arcsec)"]); all_gt += list(eel["gt"])
all_sub += ["EEL"] * len(eel)

# --- COSMOS ---
cosmos = pd.read_csv(os.path.join(DL, "LEMON_COSMOS_predictions.csv")).dropna(subset=["Name"])
cosmos["field"] = cosmos["Name"].apply(lambda s: re.search(r"COSMOS(\S+?)_Euclid", s).group(1))
cosmos["gt"] = cosmos["field"].map(COSMOS_GT)
missing = cosmos[cosmos["gt"].isna()]["field"].tolist()
if missing:
    print("COSMOS fields with no GT match:", missing)
cosmos = cosmos.dropna(subset=["gt"])
m_cosmos = met(cosmos["Einstein_radius(arcsec)"].values, cosmos["gt"].values)
row("COSMOS (Faure+08 T4 Erad)", m_cosmos)
all_pred += list(cosmos["Einstein_radius(arcsec)"]); all_gt += list(cosmos["gt"])
all_sub += ["COSMOS"] * len(cosmos)

# --- ACS/Pawase (arc radius substitute, LEMON's own disclosed convention) ---
acs = pd.read_csv(os.path.join(DL, "LEMON_ACS_predictions.csv")).dropna(subset=["Name"])
acs["coord"] = acs["Name"].apply(lambda s: re.search(r"ACS(\S+?)_Euclid", s).group(1))
acs["gt"] = acs["coord"].map(ACS_GT)
missing = acs[acs["gt"].isna()]["coord"].tolist()
if missing:
    print("ACS coords with no GT match:", missing)
acs = acs.dropna(subset=["gt"])
m_acs = met(acs["Einstein_radius(arcsec)"].values, acs["gt"].values)
row("ACS/Pawase (arc-radius substitute)", m_acs)
all_pred += list(acs["Einstein_radius(arcsec)"]); all_gt += list(acs["gt"])
all_sub += ["ACS"] * len(acs)

print("\n=== COMBINED (all subsamples, LEMON's own predictions vs GT from their cited tables) ===")
all_pred, all_gt = np.array(all_pred), np.array(all_gt)
m_all = met(all_pred, all_gt)
row("ALL %d" % len(all_pred), m_all)
print("\nLEMON's PUBLISHED Table 3 aggregate (their paper, N~60): bias -0.03  RMSE 0.14  NMAD 0.11  R2 0.53")
print("Recomputed here (excl. any GT-less rows), N=%d: bias %+.3f  RMSE %.3f  NMAD %.3f  R2 %+.2f"
      % (m_all["n"], m_all["bias"], m_all["rmse"], m_all["nmad"], m_all["r2"]))

out = pd.DataFrame(dict(subsample=all_sub, lemon_pred=all_pred, gt=all_gt,
                        frac_err=(all_pred - all_gt) / all_gt))
out.to_csv(os.path.join(OUT, "lemon_full60_accuracy_check.csv"), index=False)
with open(os.path.join(OUT, "lemon_full60_accuracy_report.md"), "w") as f:
    f.write("# LEMON's own predictions vs GT from their cited tables, per subsample\n\n")
    f.write("| subsample | N | bias | RMSE | NMAD | R2 | fail>15%% |\n|---|---|---|---|---|---|---|\n")
    for lab, m in (("SLACS", m_slacs), ("EEL", m_eel), ("COSMOS", m_cosmos),
                   ("ACS/Pawase", m_acs), ("ALL COMBINED", m_all)):
        f.write("| %s | %d | %+.3f | %.3f | %.3f | %+.2f | %.0f%% |\n"
                % (lab, m["n"], m["bias"], m["rmse"], m["nmad"], m["r2"], 100 * m["fail"]))
    f.write("\nLEMON published (Table 3, N~60): bias -0.03  RMSE 0.14  NMAD 0.11  R2 0.53\n")
print("\nwrote %s/lemon_full60_accuracy_check.csv + lemon_full60_accuracy_report.md" % OUT)
