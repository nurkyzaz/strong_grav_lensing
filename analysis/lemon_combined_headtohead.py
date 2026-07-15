#!/usr/bin/env python
"""⛔ Q1b eval harvest + final combined LEMON head-to-head table
(Nurkyz LEMON program, 2026-07-15): SLACS-29 (verified) + EEL-12 + COSMOS-5
+ ACS-12 (1 excluded, chip-gap cutout), native (G4n cnv2_3) and Euclid
(G4 cnv2_3) domains, both vs LEMON's own predictions on the same lenses."""
import os
import re

import numpy as np
import pandas as pd

DL = "/Users/nurkyz/Downloads"
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(REPO, "results")
OUT = "/Users/nurkyz/Desktop/LensFusion/lemon_headtohead"
BRIAN = "brian_run"  # scp'd locally under RES/lemonq1b/

EEL_GT = {
    "J0837": 0.56, "J0901": 0.67, "J0913": 0.42, "J1125": 0.86, "J1144": 0.68,
    "J1218": 0.68, "J1323": 0.31, "J1347": 0.43, "J1446": 0.41, "J1605": 0.64,
    "J1606": 0.52, "J1619": 0.50, "J2228": 0.60,
}
COSMOS_GT = {
    "0012+2015": 0.67, "0038+4133": 0.73, "0047+5023": 1.41, "0211+1139": 3.14,
    "5921+0638": 0.70,
}
ACS_GT = {
    "001423.02-302109.8": 1.52, "001426.26-302255.9": 1.00, "011018.22+193819.5": 3.10,
    "084710.65+344826.4": 1.98, "095139.44+684731.2": 0.77, "103751.40-124327.5": 1.48,
    "122332.64-123940.3": 0.36, "130042.73+280523.3": 1.08, "140237.11+542716.4": 1.85,
    "140339.94+541633.3": 0.90, "171817.43+593146.4": 2.35, "235130.60-261459.7": 3.32,
}  # 221501 excluded (bad cutout)
B_G4, B_G4N = -0.0015423929634094113, -0.005201080657959101


def met(p, t):
    d = p - t
    return dict(bias=d.mean(), rmse=float(np.sqrt((d ** 2).mean())),
                nmad=float(1.4826 * np.median(np.abs(d - np.median(d)))),
                r2=float(1 - (d ** 2).sum() / ((t - t.mean()) ** 2).sum()),
                fail=float((np.abs(d / t) > 0.15).mean()), n=len(p))


def row(label, m):
    print("  %-30s N=%3d bias %+.3f RMSE %.3f NMAD %.3f R2 %+.2f fail %.0f%%"
          % (label, m["n"], m["bias"], m["rmse"], m["nmad"], m["r2"], 100 * m["fail"]))


def load_ens(sub, domain):
    dfs = [pd.read_csv(os.path.join(RES, "lemonq1b",
           "preds_lemonq1b_%s_cnv2_s%d_%s_%s.csv" % ("g4n" if domain == "native" else "g4",
                                                      s, sub, domain)))
           for s in (1, 2, 3)]
    for d in dfs[1:]:
        assert (d["name"] == dfs[0]["name"]).all()
    B = B_G4N if domain == "native" else B_G4
    p = np.mean([d["theta_E_pred_arcsec"].values for d in dfs], axis=0) + B
    return dfs[0]["name"].values, p


records = []

# --- SLACS-29 (already verified 2026-07-15) ---
slacs = pd.read_csv(os.path.join(DL, "LEMON_SLACS_predictions.csv")).dropna(subset=["Name"])
slacs["jname"] = slacs["Name"].apply(lambda s: re.search(r"(J\d{4}[+-]\d{4})", s).group(1))
bolton = {}
for line in open("/tmp/bolton_table5_raw.tsv"):
    parts = line.rstrip("\n").split("\t")
    if len(parts) > 2 and re.match(r"J\d{4}[+-]\d{4}", parts[1].strip()):
        try:
            bolton[parts[1].strip()] = float(parts[2].strip())
        except ValueError:
            pass
slacs["gt"] = slacs["jname"].map(bolton)
slacs = slacs.dropna(subset=["gt"])
ns, pn = load_ens("SLACS", "native") if os.path.exists(
    os.path.join(RES, "lemonq1b", "preds_lemonq1b_g4n_cnv2_s1_SLACS_native.csv")) else (None, None)
# SLACS native/Euclid already computed earlier from the main 62-lens benchmark
n19, p19 = None, None
dfs19 = [pd.read_csv(os.path.join(RES, "preds_l19_g4_cnv2_s%d_euclid_slacs_images_g3.csv" % s))
         for s in (1, 2, 3)]
p19 = np.mean([d["theta_E_pred_arcsec"].values for d in dfs19], axis=0) + B_G4
n19 = dfs19[0]["name"].values
dfs21 = [pd.read_csv(os.path.join(RES, "preds_l21_g4n_cnv2_s%d_real_slacs_images.csv" % s))
         for s in (1, 2, 3)]
p21 = np.mean([d["theta_E_pred_arcsec"].values for d in dfs21], axis=0) + B_G4N
n21 = dfs21[0]["name"].values
mp19 = dict(zip(n19, p19)); mp21 = dict(zip(n21, p21))
slacs = slacs[slacs["jname"].isin(mp19) & slacs["jname"].isin(mp21)]
for _, r in slacs.iterrows():
    records.append(dict(subsample="SLACS", name=r["jname"], gt=r["gt"],
                        lemon=r["Einstein_radius(arcsec)"],
                        our_native=mp21[r["jname"]], our_euclid=mp19[r["jname"]]))

# --- EEL / COSMOS / ACS ---
for sub, gt_map, name_col, name_re in (
        ("EEL", EEL_GT, "jname", r"EEL(J\d{4})"),
        ("COSMOS", COSMOS_GT, "field", r"COSMOS(\S+?)_Euclid"),
        ("ACS", ACS_GT, "coord", r"ACS(\S+?)_Euclid")):
    lemon_df = pd.read_csv(os.path.join(DL, "LEMON_%s_predictions.csv" % sub)).dropna(subset=["Name"])
    lemon_df[name_col] = lemon_df["Name"].apply(lambda s: re.search(name_re, s).group(1))
    lemon_df["gt"] = lemon_df[name_col].map(gt_map)
    lemon_df = lemon_df.dropna(subset=["gt"])

    h5_prefix = {"EEL": "EEL_", "COSMOS": "COSMOS_", "ACS": "ACS_"}[sub]
    names_nat, p_nat = load_ens(sub, "native")
    names_euc, p_euc = load_ens(sub, "euclid")
    map_nat = dict(zip(names_nat, p_nat))
    map_euc = dict(zip(names_euc, p_euc))

    def encode(s):
        return s.replace(".", "p").replace("+", "P").replace("-", "M")

    for _, r in lemon_df.iterrows():
        raw_key = h5_prefix + r[name_col]
        key = raw_key if sub != "ACS" else h5_prefix + encode(r[name_col])
        if key not in map_nat:
            continue
        records.append(dict(subsample=sub, name=r[name_col], gt=r["gt"],
                            lemon=r["Einstein_radius(arcsec)"],
                            our_native=map_nat[key], our_euclid=map_euc[key]))

df = pd.DataFrame(records)
print("Combined table: N=%d (%s)" % (len(df), dict(df["subsample"].value_counts())))

print("\n=== PER-SUBSAMPLE ===")
for sub in ("SLACS", "EEL", "COSMOS", "ACS"):
    d = df[df["subsample"] == sub]
    if len(d) == 0:
        continue
    print("-- %s (N=%d) --" % (sub, len(d)))
    row("LEMON", met(d["lemon"].values, d["gt"].values))
    row("OURS native", met(d["our_native"].values, d["gt"].values))
    row("OURS Euclid", met(d["our_euclid"].values, d["gt"].values))

print("\n=== COMBINED ALL SUBSAMPLES (N=%d) ===" % len(df))
m_lemon = met(df["lemon"].values, df["gt"].values)
m_nat = met(df["our_native"].values, df["gt"].values)
m_euc = met(df["our_euclid"].values, df["gt"].values)
row("LEMON", m_lemon)
row("OURS native", m_nat)
row("OURS Euclid", m_euc)

df.to_csv(os.path.join(OUT, "lemon_combined_headtohead.csv"), index=False)
with open(os.path.join(OUT, "lemon_combined_headtohead_report.md"), "w") as f:
    f.write("# LEMON combined head-to-head: SLACS-29 + EEL-12 + COSMOS-5 + ACS-12 (N=%d)\n\n"
            % len(df))
    f.write("GT sourced directly from the papers LEMON's own methods cite: Bolton+08 T5, "
            "Oldham&Auger17 T2, Faure+08 T4, Pawase+14 T3 (arc radius). "
            "1 ACS lens excluded (confirmed chip-gap cutout).\n\n")
    f.write("| domain | N | bias | RMSE | NMAD | R2 | fail>15%% |\n|---|---|---|---|---|---|---|\n")
    for lab, m in (("LEMON (all 4 subsamples)", m_lemon),
                   ("OURS native HST", m_nat), ("OURS Euclid-domain", m_euc)):
        f.write("| %s | %d | %+.3f | %.3f | %.3f | %+.2f | %.0f%% |\n"
                % (lab, m["n"], m["bias"], m["rmse"], m["nmad"], m["r2"], 100 * m["fail"]))
    f.write("\n## Per-subsample\n\n")
    for sub in ("SLACS", "EEL", "COSMOS", "ACS"):
        d = df[df["subsample"] == sub]
        if len(d) == 0:
            continue
        f.write("\n### %s (N=%d)\n\n" % (sub, len(d)))
        f.write("| config | bias | RMSE | NMAD | R2 | fail>15%% |\n|---|---|---|---|---|---|\n")
        for lab, m in (("LEMON", met(d["lemon"].values, d["gt"].values)),
                       ("OURS native", met(d["our_native"].values, d["gt"].values)),
                       ("OURS Euclid", met(d["our_euclid"].values, d["gt"].values))):
            f.write("| %s | %+.3f | %.3f | %.3f | %+.2f | %.0f%% |\n"
                    % (lab, m["bias"], m["rmse"], m["nmad"], m["r2"], 100 * m["fail"]))
print("\nwrote %s/lemon_combined_headtohead.csv + lemon_combined_headtohead_report.md" % OUT)
