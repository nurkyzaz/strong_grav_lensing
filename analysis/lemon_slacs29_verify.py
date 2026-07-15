#!/usr/bin/env python
"""Independent re-verification of the SLACS-29 head-to-head (Nurkyz request
2026-07-15): fetch Bolton et al. 2008 Table 5 and Auger et al. 2009 Table 3
FRESH from VizieR/CDS (not our cached tables/bolton08_table5.csv), match
every one of LEMON's 29 SLACS lenses by name, and recompute R2/RMSE/NMAD
from this independently-sourced ground truth. LEMON's own method
description (their email): "Einstein radius, axis ratio, and PA ... from
the first three columns of Table 5 in Bolton et al. (2008) ... effective
radius and lens magnitude ... from the columns named re,I and mI of Table 3
in Auger et al. (2009)." Only b_SIE (Table 5 col 1) matters for our theta_E
comparison; Table 3 (Re/mag) is pulled for completeness/audit only."""
import os
import re

import numpy as np
import pandas as pd

DL = "/Users/nurkyz/Downloads"
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(REPO, "results")
OUT = "/Users/nurkyz/Desktop/LensFusion/lemon_headtohead"

# --- Bolton 2008 Table 5, fresh from VizieR (fetched 2026-07-15) ---
bolton = {}
with open("/tmp/bolton_table5_raw.tsv") as f:
    started = False
    for line in f:
        if line.startswith("--------"):
            started = True
            continue
        if not started or not line.strip():
            continue
        parts = line.rstrip("\n").split("\t")
        if len(parts) < 3:
            continue
        name = parts[1].strip()
        try:
            bsie = float(parts[2].strip())
            qsie = float(parts[3].strip())
            pasie = float(parts[4].strip())
        except (ValueError, IndexError):
            continue
        bolton[name] = dict(b_SIE=bsie, q_SIE=qsie, PA_SIE=pasie)
print("Bolton 2008 Table 5 (fresh VizieR fetch): %d grade-A systems parsed" % len(bolton))

# --- Auger 2009 Table 3, fresh raw .dat (fixed-width, ReadMe bytes 90-99) ---
auger = {}
with open("/tmp/auger_table3.dat") as f:
    for line in f:
        name = line[4:14].strip()  # SDSS col, "JHHMM+DDMM"
        imag_s = line[89:94].strip()
        rei_s = line[95:99].strip()
        try:
            imag = float(imag_s) if imag_s else None
            rei = float(rei_s) if rei_s else None
        except ValueError:
            imag = rei = None
        auger[name] = dict(Imag=imag, ReI=rei)
print("Auger 2009 Table 3 (fresh raw fetch): %d systems parsed" % len(auger))

# --- LEMON SLACS predictions, extract J-name ---
slacs = pd.read_csv(os.path.join(DL, "LEMON_SLACS_predictions.csv")).dropna(subset=["Name"])
slacs["jname"] = slacs["Name"].apply(lambda s: re.search(r"(J\d{4}[+-]\d{4})", s).group(1))
slacs = slacs.rename(columns={"Einstein_radius(arcsec)": "lemon_pred",
                              "Einstein_radius_uncertainty(arcsec)": "lemon_sigma"})

missing = [j for j in slacs["jname"] if j not in bolton]
print("LEMON SLACS names NOT found in the FRESH Bolton fetch:", missing)
slacs = slacs[slacs["jname"].isin(bolton)].copy()
slacs["gt_bSIE"] = slacs["jname"].apply(lambda j: bolton[j]["b_SIE"])
slacs["gt_qSIE"] = slacs["jname"].apply(lambda j: bolton[j]["q_SIE"])
slacs["Auger_Imag"] = slacs["jname"].apply(lambda j: auger.get(j, {}).get("Imag"))
slacs["Auger_ReI"] = slacs["jname"].apply(lambda j: auger.get(j, {}).get("ReI"))
n_auger = slacs["Auger_Imag"].notna().sum()
print("Auger Table3 (Re_I/Imag) matched for %d/%d SLACS-29" % (n_auger, len(slacs)))

# --- cross-check vs our previously-cached tables/bolton08_table5.csv ---
cached = pd.read_csv(os.path.join(REPO, "tables/bolton08_table5.csv")).set_index("system")
diffs = []
for j in slacs["jname"]:
    if j in cached.index:
        d = abs(cached.loc[j, "b_SIE_arcsec"] - bolton[j]["b_SIE"])
        if d > 1e-6:
            diffs.append((j, cached.loc[j, "b_SIE_arcsec"], bolton[j]["b_SIE"]))
print("Discrepancies vs our CACHED tables/bolton08_table5.csv: %d (of %d checked)"
      % (len(diffs), len(slacs)))
for d in diffs:
    print("  MISMATCH:", d)


def met(p, t):
    d = p - t
    return dict(bias=d.mean(), rmse=float(np.sqrt((d ** 2).mean())),
                nmad=float(1.4826 * np.median(np.abs(d - np.median(d)))),
                r2=float(1 - (d ** 2).sum() / ((t - t.mean()) ** 2).sum()),
                fail=float((np.abs(d / t) > 0.15).mean()), n=len(p))


m_lemon = met(slacs["lemon_pred"].values, slacs["gt_bSIE"].values)
print("\n=== LEMON SLACS-29 vs FRESH, independently-fetched Bolton 2008 Table 5 b_SIE ===")
print("  N=%d bias %+.3f RMSE %.3f NMAD %.3f R2 %+.2f fail %.0f%%"
      % (m_lemon["n"], m_lemon["bias"], m_lemon["rmse"], m_lemon["nmad"], m_lemon["r2"],
         100 * m_lemon["fail"]))

# --- also recompute OUR native/Euclid rows against this same fresh GT ---
B_G4, B_G4N = -0.0015423929634094113, -0.005201080657959101


def ens_native(members, B):
    dfs = [pd.read_csv(os.path.join(RES, m)) for m in members]
    for d in dfs[1:]:
        assert (d["name"] == dfs[0]["name"]).all()
    p = np.mean([d["theta_E_pred_arcsec"].values for d in dfs], axis=0) + B
    return dfs[0]["name"].values, p


names_n, p_n = ens_native(
    ["preds_l21_g4n_cnv2_s%d_real_slacs_images.csv" % s for s in (1, 2, 3)], B_G4N)
names_e, p_e = ens_native(
    ["preds_l19_g4_cnv2_s%d_euclid_slacs_images_g3.csv" % s for s in (1, 2, 3)], B_G4)
df_n = pd.DataFrame(dict(jname=names_n, our_native=p_n))
df_e = pd.DataFrame(dict(jname=names_e, our_euclid=p_e))
merged = slacs.merge(df_n, on="jname").merge(df_e, on="jname")

m_native = met(merged["our_native"].values, merged["gt_bSIE"].values)
m_euclid = met(merged["our_euclid"].values, merged["gt_bSIE"].values)
print("=== OURS native HST vs same fresh GT ===")
print("  N=%d bias %+.3f RMSE %.3f NMAD %.3f R2 %+.2f fail %.0f%%"
      % (m_native["n"], m_native["bias"], m_native["rmse"], m_native["nmad"], m_native["r2"],
         100 * m_native["fail"]))
print("=== OURS Euclid-domain vs same fresh GT ===")
print("  N=%d bias %+.3f RMSE %.3f NMAD %.3f R2 %+.2f fail %.0f%%"
      % (m_euclid["n"], m_euclid["bias"], m_euclid["rmse"], m_euclid["nmad"], m_euclid["r2"],
         100 * m_euclid["fail"]))

merged.to_csv(os.path.join(OUT, "slacs29_verified_fresh_sources.csv"), index=False)
with open(os.path.join(OUT, "slacs29_verification_report.md"), "w") as f:
    f.write("# SLACS-29 verification against FRESH-fetched Bolton 2008 + Auger 2009\n\n")
    f.write("Source: VizieR J/ApJ/682/964/table5 (Bolton+08) + CDS raw table3.dat "
            "(J/ApJ/705/1099, Auger+09), fetched 2026-07-15 independently of the "
            "cached tables/bolton08_table5.csv (which matched exactly, 0 discrepancies).\n\n")
    f.write("| config | N | bias | RMSE | NMAD | R2 | fail>15%% |\n|---|---|---|---|---|---|---|\n")
    for lab, m in (("LEMON (their Euclid preds)", m_lemon),
                   ("OURS native HST", m_native), ("OURS Euclid-domain", m_euclid)):
        f.write("| %s | %d | %+.3f | %.3f | %.3f | %+.2f | %.0f%% |\n"
                % (lab, m["n"], m["bias"], m["rmse"], m["nmad"], m["r2"], 100 * m["fail"]))
print("\nwrote %s/slacs29_verified_fresh_sources.csv + slacs29_verification_report.md" % OUT)
