#!/usr/bin/env python
"""LEMON head-to-head, Q1 arm (Nurkyz: LEMON reply landed 2026-07-14).
SLACS-29 sub-arm: their exact list resolves C16/Q1a — a row-filter on
ALREADY-BANKED predictions, no new model passes. Reproduces LEMON's own
SLACS-29 metrics from their csv (sanity check vs their paper's aggregate),
then computes our native (eval #21) and Euclid (eval #19) metrics on the
SAME 29, all vs Bolton 2008 b_SIE GT."""
import os
import re

import numpy as np
import pandas as pd

DL = "/Users/nurkyz/Downloads"
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(REPO, "results")
OUT = "/Users/nurkyz/Desktop/LensFusion/lemon_headtohead"
os.makedirs(OUT, exist_ok=True)

bolton = pd.read_csv(os.path.join(REPO, "tables/bolton08_table5.csv")).set_index("system")

# --- SLACS: extract J-name, join LEMON pred + Bolton GT ---
slacs = pd.read_csv(os.path.join(DL, "LEMON_SLACS_predictions.csv"))
slacs = slacs.dropna(subset=["Name"])
slacs["jname"] = slacs["Name"].apply(lambda s: re.search(r"(J\d{4}[+-]\d{4})", s).group(1))
slacs = slacs.rename(columns={"Einstein_radius(arcsec)": "lemon_pred",
                              "Einstein_radius_uncertainty(arcsec)": "lemon_sigma"})
print("SLACS: N=%d LEMON predictions, %d unique J-names" % (len(slacs), slacs["jname"].nunique()))

missing_gt = [j for j in slacs["jname"] if j not in bolton.index]
print("J-names NOT in our Bolton table5:", missing_gt)
slacs = slacs[slacs["jname"].isin(bolton.index)].copy()
slacs["gt"] = slacs["jname"].map(bolton["b_SIE_arcsec"])

in_our_bench = set(slacs["jname"]) & set(bolton.index)
print("SLACS-29 all resolvable against Bolton Table 5:", len(in_our_bench) == len(slacs))


def met(p, t):
    d = p - t
    return dict(bias=d.mean(), rmse=float(np.sqrt((d ** 2).mean())),
                nmad=float(1.4826 * np.median(np.abs(d - np.median(d)))),
                r2=float(1 - (d ** 2).sum() / ((t - t.mean()) ** 2).sum()),
                fail=float((np.abs(d / t) > 0.15).mean()), n=len(p))


def row(label, m):
    print("  %-28s N=%3d bias %+.3f RMSE %.3f NMAD %.3f R2 %+.2f fail %.0f%%"
          % (label, m["n"], m["bias"], m["rmse"], m["nmad"], m["r2"], 100 * m["fail"]))


print("\n=== SLACS-29 head-to-head vs Bolton 2008 b_SIE ===")
m_lemon = met(slacs["lemon_pred"].values, slacs["gt"].values)
row("LEMON (their Euclid preds)", m_lemon)

B_G4, B_G4N = -0.0015423929634094113, -0.005201080657959101


def ens_native(members, B):
    dfs = [pd.read_csv(os.path.join(RES, m)) for m in members]
    for d in dfs[1:]:
        assert (d["name"] == dfs[0]["name"]).all()
    p = np.mean([d["theta_E_pred_arcsec"].values for d in dfs], axis=0) + B
    return dfs[0]["name"].values, p, dfs[0]["theta_E_pub_arcsec"].values

names_n, p_n, t_n = ens_native(
    ["preds_l21_g4n_cnv2_s%d_real_slacs_images.csv" % s for s in (1, 2, 3)], B_G4N)
names_e, p_e, t_e = ens_native(
    ["preds_l19_g4_cnv2_s%d_euclid_slacs_images_g3.csv" % s for s in (1, 2, 3)], B_G4)
df_n = pd.DataFrame(dict(jname=names_n, our_native=p_n, gt_bench=t_n))
df_e = pd.DataFrame(dict(jname=names_e, our_euclid=p_e))

merged = slacs.merge(df_n, on="jname", how="left").merge(df_e, on="jname", how="left")
missing_bench = merged[merged["our_native"].isna()]["jname"].tolist()
print("LEMON SLACS names NOT in our 62-lens native benchmark:", missing_bench)
merged = merged.dropna(subset=["our_native"])

m_native = met(merged["our_native"].values, merged["gt"].values)
m_euclid = met(merged["our_euclid"].values, merged["gt"].values)
row("OURS native HST (eval #21)", m_native)
row("OURS Euclid-domain (eval #19)", m_euclid)

merged.to_csv(os.path.join(OUT, "slacs29_head_to_head.csv"), index=False)
with open(os.path.join(OUT, "slacs29_summary.md"), "w") as f:
    f.write("# LEMON SLACS-29 head-to-head (GT = Bolton 2008 b_SIE)\n\n")
    f.write("| config | N | bias | RMSE | NMAD | R2 | fail>15%% |\n|---|---|---|---|---|---|---|\n")
    for lab, m in (("LEMON (their Euclid preds)", m_lemon),
                   ("OURS native HST", m_native), ("OURS Euclid-domain", m_euclid)):
        f.write("| %s | %d | %+.3f | %.3f | %.3f | %+.2f | %.0f%% |\n"
                % (lab, m["n"], m["bias"], m["rmse"], m["nmad"], m["r2"], 100 * m["fail"]))
print("\nwrote %s/slacs29_head_to_head.csv + slacs29_summary.md" % OUT)

# --- EEL / COSMOS / ACS: parse + report fetch scope (no GT/predictions yet) ---
eel = pd.read_csv(os.path.join(DL, "LEMON_EEL_predictions.csv")).dropna(subset=["Name"])
eel["jname"] = eel["Name"].apply(lambda s: re.search(r"EEL(J\d{4})", s).group(1))
cosmos = pd.read_csv(os.path.join(DL, "LEMON_COSMOS_predictions.csv")).dropna(subset=["Name"])
cosmos["field"] = cosmos["Name"].apply(lambda s: re.search(r"COSMOS(\S+?)_Euclid", s).group(1))
acs = pd.read_csv(os.path.join(DL, "LEMON_ACS_predictions.csv")).dropna(subset=["Name"])
acs["coord"] = acs["Name"].apply(lambda s: re.search(r"ACS(\S+?)_Euclid", s).group(1))

print("\n=== Non-SLACS scope (native fetch required, C16/Q1b) ===")
print("EELs: N=%d  %s" % (len(eel), sorted(eel["jname"].tolist())))
print("COSMOS: N=%d  %s" % (len(cosmos), sorted(cosmos["field"].tolist())))
print("ACS/Pawase: N=%d  coords: %s" % (len(acs), sorted(acs["coord"].tolist())))
for name, df in (("eel", eel), ("cosmos", cosmos), ("acs", acs)):
    df.to_csv(os.path.join(OUT, "lemon_%s_predictions_parsed.csv" % name), index=False)
print("\nparsed non-SLACS csvs written to %s (for the MAST fetch stage)" % OUT)
