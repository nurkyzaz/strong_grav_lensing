#!/usr/bin/env python
"""Build the '14 july' results pack for Nurkyz: per-eval tables, pred-vs-true
scatters, headline comparison vs LEMON, plus all lens-image galleries.
Derived ensembles recomputed from banked member CSVs with each recipe's
frozen recal bias (reproduction-checked against the published rows)."""
import os
import shutil

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(REPO, "results")
PACK = "/Users/nurkyz/Desktop/LensFusion/14 july"
EXCLUDE = {"J0955+0101"}
B_G4 = -0.0015423929634094113   # g4_recal.json (evals 17/19)
B_G4N = -0.005201080657959101   # g4n_recal.json (eval 21)
B_G4AR = -0.0032367853597006224  # g4ar_recal.json (eval 22)

os.makedirs(PACK, exist_ok=True)


def met(p, t):
    d = p - t
    return dict(bias=d.mean(), rmse=float(np.sqrt((d ** 2).mean())),
                nmad=float(1.4826 * np.median(np.abs(d - np.median(d)))),
                r2=float(1 - (d ** 2).sum() / ((t - t.mean()) ** 2).sum()),
                fail=float((np.abs(d / t) > 0.15).mean()),
                medfrac=float(np.median(d / t)), n=len(p))


def ens_from(members, B):
    dfs = [pd.read_csv(os.path.join(RES, m)) for m in members]
    for d in dfs[1:]:
        assert (d["name"] == dfs[0]["name"]).all()
    p = np.mean([d["theta_E_pred_arcsec"].values for d in dfs], axis=0) + B
    return dfs[0]["name"].values, p, dfs[0]["theta_E_pub_arcsec"].values


def scatter(fn, name, p, t, m, color="#1f77b4"):
    fig, ax = plt.subplots(figsize=(5.4, 5.4))
    lim = [0, max(2.4, t.max() * 1.08, p.max() * 1.08)]
    ax.fill_between(lim, [v * 0.85 for v in lim], [v * 1.15 for v in lim],
                    color="0.9", label=r"$\pm$15%")
    ax.plot(lim, lim, "k--", lw=1)
    ax.scatter(t, p, s=16, alpha=0.75, color=color)
    ax.set_xlim(lim), ax.set_ylim(lim)
    ax.set_xlabel(r"true $\theta_E$ [arcsec]")
    ax.set_ylabel(r"predicted $\theta_E$ [arcsec]")
    ax.set_title("%s\nN=%d  bias %+.3f\"  RMSE %.3f\"  NMAD %.3f\"  R$^2$ %+.2f  fail %.0f%%"
                 % (name, m["n"], m["bias"], m["rmse"], m["nmad"], m["r2"],
                    100 * m["fail"]), fontsize=9)
    ax.legend(loc="upper left", fontsize=8)
    plt.tight_layout()
    plt.savefig(fn, dpi=150)
    plt.close()


rows = []


def bank(folder, label, names, p, t, published, color, excl=True, suffix=""):
    d = os.path.join(PACK, folder)
    os.makedirs(d, exist_ok=True)
    if excl:
        keep = ~pd.Series(names).isin(EXCLUDE).values
        names, p, t = np.asarray(names)[keep], p[keep], t[keep]
    m = met(p, t)
    pd.DataFrame(dict(name=names, theta_E_true=t, theta_E_pred=np.round(p, 4),
                      frac_err=np.round(p / t - 1, 4))).to_csv(
        os.path.join(d, "per_lens%s.csv" % suffix), index=False)
    scatter(os.path.join(d, "scatter%s.png" % suffix), label, p, t, m, color)
    ok = ""
    if published:
        ok = "REPRO-OK" if all(abs(m[k] - v) < tol for k, (v, tol) in published.items()) \
            else "REPRO-CHECK: " + str({k: round(m[k], 3) for k in published})
    rows.append((folder, label, m, ok))
    print("%-34s bias %+.3f RMSE %.3f NMAD %.3f R2 %+.2f fail %.0f%%  %s"
          % (label[:34], m["bias"], m["rmse"], m["nmad"], m["r2"], 100 * m["fail"], ok))
    return m


# --- eval 19: THE beat-LEMON board (Euclidised SLACS) ---
n, p, t = ens_from(["preds_l19_g4_cnv2_s%d_euclid_slacs_images_g3.csv" % s for s in (1, 2, 3)], B_G4)
bank("eval19_beat_lemon_euclid", "EVAL 19 Euclidised SLACS (G4 cnv2_3) — the beat-LEMON row",
     n, p, t, dict(rmse=(0.137, 0.003), r2=(0.71, 0.02)), "#1f77b4", suffix="_slacs")
n, p, t = ens_from(["preds_l19_g4_cnv2_s%d_euclid_s4tm_images_g3.csv" % s for s in (1, 2, 3)], B_G4)
bank("eval19_beat_lemon_euclid", "EVAL 19 Euclidised S4TM (G4 cnv2_3)", n, p, t, None, "#4c9be8", excl=False, suffix="_s4tm")

# --- eval 21: native best ---
n, p, t = ens_from(["preds_l21_g4n_cnv2_s%d_real_slacs_images.csv" % s for s in (1, 2, 3)], B_G4N)
bank("eval21_native_best", "EVAL 21 Native HST SLACS (g4n cnv2_3)",
     n, p, t, dict(rmse=(0.152, 0.003), r2=(0.64, 0.02)), "#2ca02c", suffix="_slacs")
n, p, t = ens_from(["preds_l21_g4n_r50_s%d_real_s4tm_images.csv" % s for s in (1, 2, 3)], B_G4N)
m = bank("eval21_native_best", "EVAL 21 Native HST S4TM (g4n r50_3, derived) — PROJECT BEST",
         n, p, t, dict(rmse=(0.088, 0.004), r2=(0.90, 0.02)), "#0e6e0e", excl=False, suffix="_s4tm_r50")

# --- eval 22: S4TM-Euclid best ---
n, p, t = ens_from(["preds_l22_g4ar_r50_s%d_euclid_s4tm_images_g3.csv" % s for s in (1, 2, 3)], B_G4AR)
bank("eval22_g4ar", "EVAL 22 Euclidised S4TM (g4ar r50_3) — S4TM-Euclid best",
     n, p, t, dict(rmse=(0.103, 0.003), r2=(0.86, 0.02)), "#9467bd", excl=False, suffix="_s4tm_r50")
n, p, t = ens_from(["preds_l22_g4ar_cnv2_s%d_euclid_slacs_images_g3.csv" % s for s in (1, 2, 3)], B_G4AR)
bank("eval22_g4ar", "EVAL 22 Euclidised SLACS (g4ar cnv2_3, null vs #19)", n, p, t, None, "#b493d3", suffix="_slacs")

# --- eval 23 + 24 + g5b: direct from ens CSVs ---
for folder, label, fn, col, excl in (
        ("eval23_combined_ens2", "EVAL 23 Euclidised SLACS (ens2 combined row)",
         "preds_l23_ens2_euclid_slacs_images_g3.csv", "#8c564b", True),
        ("eval23_combined_ens2", "EVAL 23 Euclidised S4TM (ens2)",
         "preds_l23_ens2_euclid_s4tm_images_g3.csv", "#b0857b", False)):
    d = pd.read_csv(os.path.join(RES, fn))
    bank(folder, label, d["name"].values, d["theta_E_pred_arcsec"].values,
         d["theta_E_pub_arcsec"].values, None, col, excl=excl, suffix="_s4tm" if "s4tm" in fn else "_slacs")

d = pd.read_csv(os.path.join(RES, "preds_l24_ens_q1_slde_f11p4.csv"))
bank("eval24_realQ1_negative_finding", "EVAL 24 REAL Euclid Q1 N=322 (cnv2_3) — the negative finding",
     d["name"].values, d["pred_cnv2_3"].values, d["theta_E_gt"].values, None, "#d62728", excl=False)

g5 = [pd.read_csv(os.path.join(RES, "g5b/preds_g5b_g4_cnv2_s%d.csv" % s)) for s in (1, 2, 3)]
p = np.mean([x["theta_E_pred_arcsec"].values for x in g5], axis=0) + B_G4
bank("g5b_roman_zeroshot", "G5b Roman Rung0 zero-shot (G4 cnv2_3) — baseline",
     g5[0]["name"].values, p, g5[0]["theta_E_pub_arcsec"].values, None, "#ff7f0e", excl=False)

# --- headline table ---
md = ["# Headline results vs LEMON (2026-07-14)\n",
      "| board | who | bias | RMSE | NMAD | R2 | fail>15% |",
      "|---|---|---|---|---|---|---|",
      "| Euclidised HST 60 (their Table 3) | **LEMON** | -0.03 | 0.14 | 0.11 | 0.53 | — |"]
for folder, label, m, ok in rows:
    md.append("| %s | **us** | %+.3f | %.3f | %.3f | %+.2f | %.0f%% |"
              % (label, m["bias"], m["rmse"], m["nmad"], m["r2"], 100 * m["fail"]))
md += ["| real Euclid Q1 354 (their Fig 12a) | **LEMON** | +0.01 | 0.17 | 0.07 | 0.71 | — |",
       "",
       "Notes: our Euclidised rows are the 62-lens SLACS superset (their exact 29",
       "pending their email; 13/60 of their GT is arc radius, not theta_E).",
       "Cao et al. 2025 (conventional, same lenses): <~5% median dev, ~10% fail,",
       "~3 min/lens vs our ~ms/lens. Eval 24: their 354 is success-filtered; our",
       "322 was not (2 collapsed GTs found). Full context: DECISIONS_LOG.md."]
open(os.path.join(PACK, "01_headline_vs_lemon.md"), "w").write("\n".join(md))
pd.DataFrame([dict(board=lb, bias=m["bias"], rmse=m["rmse"], nmad=m["nmad"],
                   r2=m["r2"], fail=m["fail"], n=m["n"]) for _, lb, m, _ in rows]).to_csv(
    os.path.join(PACK, "01_headline_rows.csv"), index=False)

# --- copy image galleries ---
IMG = os.path.join(PACK, "images")
os.makedirs(IMG, exist_ok=True)
SRC = ["/Users/nurkyz/Desktop/LensFusion/lemon60_inspection",
       "/Users/nurkyz/Desktop/LensFusion/q2e_inspection",
       os.path.join(REPO, "paper_figures")]
for sdir in SRC:
    if os.path.isdir(sdir):
        for f in os.listdir(sdir):
            if f.endswith(".png"):
                shutil.copy(os.path.join(sdir, f), os.path.join(IMG, f))
print("images copied:", len(os.listdir(IMG)))
print("PACK BUILT:", PACK)
