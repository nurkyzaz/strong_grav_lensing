#!/usr/bin/env python
"""L0 tail + bias forensics (IMPROVEMENT_PIVOT_PLAN_20260710, Stage L0 items 1+2).

Uses ONLY existing per-lens prediction CSVs (no model forward passes anywhere)
plus image STATISTICS of the benchmark files: same-estimator arc prominence,
copied verbatim from arc_prominence_compare.py (extended >=300 px residual
features, azimuthal-median-subtracted, in units of residual MAD). This is
gate-style diagnostic usage of the benchmark images, NOT a model evaluation;
the running eval count is unaffected.

Questions answered (plan refs):
  B3  do eval-#14 failures concentrate at low real-image arc prominence,
      i.e. below the regime the visibility-selected training set contains?
  B4  is the new positive bias a selection-survivor signature (bias graded
      in prominence)?
  A2a which lenses fail EVERY model generation (benchmark-intrinsic tail)?

Outputs (in ~/einstein_cnn/):
  l0_prominence_cache.csv   per-lens prominence, native + euclidised domains
  l0_perlens_matrix.csv     per-lens GT, prominences, per-model frac errors,
                            fail flags, fail counts
  l0_tail_forensics.png     overlap heatmap + stratification panels
  stdout                    the L0 report (paste key lines into DECISIONS_LOG)
"""
import os
import sys
import numpy as np
import pandas as pd
import h5py
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.ndimage import gaussian_filter, label
from scipy.stats import spearmanr

HOME = os.path.expanduser("~/einstein_cnn")
BR = os.path.join(HOME, "brian_run")
PIX = 0.05          # arcsec/px on both grids (native and upsampled Euclid)
FAIL = 0.15         # |frac err| failure threshold (house convention)
EXCLUDE = {"J0955+0101"}   # eval_protocol.json (bad cutout; kept in matrix, flagged)
CAO_FAIL = {"J0841+3824"}  # Cao et al. 2025's known shared failure (log 2026-07-09)

# ---------------------------------------------------------------- prominence
# Copied VERBATIM from arc_prominence_compare.py (same-estimator discipline).
def prominence(img):
    n = img.shape[0]
    c = n // 2
    yy, xx = np.mgrid[0:n, 0:n]
    rr = np.hypot(yy - c, xx - c)
    rbin = rr.astype(int)
    s = gaussian_filter(img.astype("float64"), 1.5)
    prof = np.zeros(rbin.max() + 1)
    for k in range(rbin.max() + 1):
        m = rbin == k
        if m.any():
            prof[k] = np.median(s[m])
    resid = s - prof[rbin]
    ann = (rr >= 0.4 / PIX) & (rr <= 2.6 / PIX)
    out = (rr > 2.6 / PIX)
    mad = np.median(np.abs(resid[out] - np.median(resid[out]))) * 1.4826
    if mad <= 0:
        return np.nan
    det = (resid > 3.0 * mad) & ann
    lab, nl = label(det)
    best = 0.0
    for i in range(1, nl + 1):
        m = lab == i
        if m.sum() >= 300:
            best = max(best, float(resid[m].max() / mad))
    return best


def load_h5_names_images(path):
    with h5py.File(path, "r") as f:
        names = [x.decode() if hasattr(x, "decode") else str(x) for x in f["names"][:]]
        imgs = f["images"][:]
        gt = f["theta_E_pub"][:].astype("float64")
    if imgs.ndim == 4:
        imgs = imgs[:, 0]
    return names, imgs.astype("float64"), gt


def prominence_table():
    cache = os.path.join(HOME, "l0_prominence_cache.csv")
    if os.path.exists(cache):
        print("[prominence] using cache %s" % cache)
        return pd.read_csv(cache)
    rows = []
    for survey, native_f, euclid_f in [
            ("SLACS", "real_slacs_images.h5", "euclid_slacs_images.h5"),
            ("S4TM", "real_s4tm_images.h5", "euclid_s4tm_images.h5")]:
        nn, ni, gt = load_h5_names_images(os.path.join(HOME, native_f))
        en, ei, _ = load_h5_names_images(os.path.join(HOME, euclid_f))
        assert nn == en, "name order mismatch %s vs %s" % (native_f, euclid_f)
        for j, name in enumerate(nn):
            rows.append(dict(name=name, survey=survey, theta_E_pub=gt[j],
                             prom_native=prominence(ni[j]),
                             prom_euclid=prominence(ei[j])))
        print("[prominence] %s done (%d lenses)" % (survey, len(nn)))
    t = pd.DataFrame(rows)
    t.to_csv(cache, index=False)
    return t


# ---------------------------------------------------------------- registry
# model key -> (domain, survey, csv path). Missing files are skipped loudly.
def registry():
    R = {}
    nat = [("m3", "theta_E_%s_m3_baseline.csv"),
           ("paltas_v1", "theta_E_%s_paltas_v1.csv"),
           ("hyb_v2", "theta_E_%s_paltas_v2.csv"),
           ("v3_inc", "theta_E_%s_v3_inceptionnext.csv"),
           ("v3_res", "theta_E_%s_v3_resnet.csv"),
           ("pathb_inc", "preds_pathb_v2_inceptionnext_real_%s.csv"),
           ("pathb_res", "preds_pathb_v2_resnet_real_%s.csv"),
           ("pathb_ens", "preds_pathb_v2_ensemble_real_%s.csv")]
    euc = [("euc_v3_inc", "preds_einstein_cnn_euclid_v3_inceptionnext_euclid_%s_images.csv"),
           ("euc_v3_res", "preds_einstein_cnn_euclid_v3_resnet_euclid_%s_images.csv"),
           ("sel_inc", "preds_einstein_cnn_euclid_sel_inceptionnext_euclid_%s_images.csv"),
           ("sel_res", "preds_einstein_cnn_euclid_sel_resnet_euclid_%s_images.csv"),
           ("sel_ens", "preds_einstein_cnn_euclid_sel_ensemble_euclid_%s_images.csv")]
    for survey, tag_nat, tag_euc in [("SLACS", "slacs", "slacs"), ("S4TM", "s4tm", "s4tm")]:
        for key, pat in nat:
            R[(key, "native", survey)] = os.path.join(BR, pat % tag_nat)
        for key, pat in euc:
            R[(key, "euclid", survey)] = os.path.join(BR, pat % tag_euc)
    return R


def load_preds(path):
    d = pd.read_csv(path)
    pcol = [c for c in d.columns if "pred" in c][0]
    tcol = [c for c in d.columns if "pub" in c or "true" in c][0]
    d = d.rename(columns={pcol: "pred", tcol: "gt"})
    return d[["name", "pred", "gt"]]


# ---------------------------------------------------------------- main
def main():
    prom = prominence_table()
    R = registry()

    wide = prom.set_index("name").copy()
    model_cols = {}   # (key, domain) -> column name, per survey handled by rows
    for (key, domain, survey), path in sorted(R.items()):
        if not os.path.exists(path):
            print("[skip] missing %s (%s/%s/%s)" % (os.path.basename(path), key, domain, survey))
            continue
        d = load_preds(path)
        col = "%s@%s" % (key, domain)
        model_cols[col] = True
        for _, r in d.iterrows():
            wide.loc[r["name"], "frac_" + col] = (r["pred"] - r["gt"]) / r["gt"]
    wide = wide.reset_index()

    cols = sorted(model_cols.keys())
    for c in cols:
        wide["fail_" + c] = (wide["frac_" + c].abs() > FAIL).astype(float)
    nat_cols = [c for c in cols if c.endswith("@native")]
    euc_cols = [c for c in cols if c.endswith("@euclid")]
    # current-generation subsets for the "fails everything current" verdict
    cur_nat = [c for c in nat_cols if c.startswith(("v3_", "pathb_"))]
    cur_euc = [c for c in euc_cols if c.startswith("sel_")]
    wide["nfail_native_cur"] = wide[["fail_" + c for c in cur_nat]].sum(axis=1)
    wide["nfail_euclid_cur"] = wide[["fail_" + c for c in cur_euc]].sum(axis=1)
    wide["excluded"] = wide["name"].isin(EXCLUDE)
    wide.to_csv(os.path.join(HOME, "l0_perlens_matrix.csv"), index=False)

    W = wide[~wide["excluded"]].copy()

    print("=" * 78)
    print("L0 TAIL FORENSICS REPORT  (predictions reused from logged evals; no new")
    print("model passes; benchmark images used for image STATISTICS only)")
    print("=" * 78)

    # 1) per-model sanity summary
    print("\n[1] Per-model summary (J0955 excluded)")
    for c in cols:
        for survey in ("SLACS", "S4TM"):
            f = W.loc[W["survey"] == survey, "frac_" + c].dropna()
            if not len(f):
                continue
            print("  %-22s %-5s N=%3d  bias(frac) %+5.1f%%  fail %4.1f%%"
                  % (c, survey, len(f), 100 * f.median(), 100 * (f.abs() > FAIL).mean()))

    # 2) failure overlap (Jaccard), current generations, SLACS
    print("\n[2] Failure-set Jaccard overlap (SLACS, current models)")
    cur = cur_nat + cur_euc
    S = W[W["survey"] == "SLACS"]
    jac = np.full((len(cur), len(cur)), np.nan)
    for i, a in enumerate(cur):
        fa = set(S.loc[S["fail_" + a] == 1, "name"])
        for j, b in enumerate(cur):
            fb = set(S.loc[S["fail_" + b] == 1, "name"])
            u = fa | fb
            jac[i, j] = len(fa & fb) / len(u) if u else np.nan
        print("  %-22s fails N=%2d" % (a, len(fa)))
    hdr = " ".join("%6.6s" % c.split("@")[0] for c in cur)
    print("        " + hdr)
    for i, a in enumerate(cur):
        print("  %-6.6s" % a.split("@")[0] +
              " ".join("%6.2f" % jac[i, j] for j in range(len(cur))))

    # 3) lenses failing everything current
    print("\n[3] Benchmark-intrinsic tail candidates")
    for survey in ("SLACS", "S4TM"):
        sub = W[W["survey"] == survey]
        allnat = sub[sub["nfail_native_cur"] == len(cur_nat)]
        alleuc = sub[sub["nfail_euclid_cur"] == len(cur_euc)]
        both = sub[(sub["nfail_native_cur"] == len(cur_nat)) &
                   (sub["nfail_euclid_cur"] == len(cur_euc))]
        print("  %s: fail ALL current native models: %d | ALL current euclid: %d | BOTH: %d"
              % (survey, len(allnat), len(alleuc), len(both)))
        for _, r in both.iterrows():
            mark = "  <-- Cao also fails this lens" if r["name"] in CAO_FAIL else ""
            print("    %-16s theta_E %.2f  prom_nat %6.1f  prom_euc %6.1f%s"
                  % (r["name"], r["theta_E_pub"], r["prom_native"], r["prom_euclid"], mark))
        for nm in CAO_FAIL:
            row = sub[sub["name"] == nm]
            if len(row):
                r = row.iloc[0]
                print("    [Cao ref] %-10s nfail_native %d/%d nfail_euclid %d/%d"
                      % (nm, r["nfail_native_cur"], len(cur_nat),
                         r["nfail_euclid_cur"], len(cur_euc)))

    # 4) B3: eval-#14 ensemble stratified by EUCLIDISED prominence (SLACS primary)
    print("\n[4] B3 test - sel_ens (eval #14) stratified by real Euclidised prominence")
    for survey in ("SLACS", "S4TM"):
        sub = W[(W["survey"] == survey)].dropna(subset=["frac_sel_ens@euclid", "prom_euclid"])
        if not len(sub):
            continue
        f = sub["frac_sel_ens@euclid"].values
        p = sub["prom_euclid"].values
        qs = np.quantile(p, [0.25, 0.5, 0.75])
        print("  %s (N=%d): prominence quartile cuts %.1f / %.1f / %.1f" %
              (survey, len(sub), qs[0], qs[1], qs[2]))
        edges = [(-np.inf, qs[0], "Q1 faintest"), (qs[0], qs[1], "Q2"),
                 (qs[1], qs[2], "Q3"), (qs[2], np.inf, "Q4 brightest")]
        for lo, hi, tag in edges:
            m = (p > lo) & (p <= hi)
            print("    %-12s N=%2d  fail %4.0f%%  median frac %+5.1f%%  MAE(frac) %4.1f%%"
                  % (tag, m.sum(), 100 * (np.abs(f[m]) > FAIL).mean(),
                     100 * np.median(f[m]), 100 * np.abs(f[m]).mean()))
        rho, pv = spearmanr(p, np.abs(f))
        print("    Spearman rho(prom, |frac|) = %+.2f (p=%.1e)" % (rho, pv))
        # faint-16% group: the regime the real sample contains but selection may not
        cut16 = np.quantile(p, 0.16)
        m = p <= cut16
        print("    faintest 16%% (prom<=%.1f): N=%d fail %4.0f%% median frac %+5.1f%%"
              % (cut16, m.sum(), 100 * (np.abs(f[m]) > FAIL).mean(), 100 * np.median(f[m])))

    # 5) B4: bias vs prominence per model (selection-survivor signature)
    print("\n[5] B4 test - signed bias by prominence quartile (SLACS)")
    S2 = W[W["survey"] == "SLACS"]
    for c, pcol in [("sel_inc@euclid", "prom_euclid"), ("sel_res@euclid", "prom_euclid"),
                    ("sel_ens@euclid", "prom_euclid"), ("euc_v3_res@euclid", "prom_euclid"),
                    ("pathb_ens@native", "prom_native"), ("v3_inc@native", "prom_native")]:
        sub = S2.dropna(subset=["frac_" + c, pcol])
        if not len(sub):
            continue
        f, p = sub["frac_" + c].values, sub[pcol].values
        qs = np.quantile(p, [0.25, 0.5, 0.75])
        med = []
        for lo, hi in [(-np.inf, qs[0]), (qs[0], qs[1]), (qs[1], qs[2]), (qs[2], np.inf)]:
            m = (p > lo) & (p <= hi)
            med.append(100 * np.median(f[m]))
        print("  %-22s bias by quartile Q1..Q4: %+5.1f%% %+5.1f%% %+5.1f%% %+5.1f%%"
              % (c, med[0], med[1], med[2], med[3]))

    # 6) theta_E-bin failure (small-theta depletion check)
    print("\n[6] sel_ens (eval #14) failure by theta_E bin")
    for survey in ("SLACS", "S4TM"):
        sub = W[(W["survey"] == survey)].dropna(subset=["frac_sel_ens@euclid"])
        f, t = sub["frac_sel_ens@euclid"].values, sub["theta_E_pub"].values
        for lo, hi in [(0.0, 0.9), (0.9, 1.2), (1.2, 1.5), (1.5, 3.0)]:
            m = (t >= lo) & (t < hi)
            if m.sum() == 0:
                continue
            print("  %s theta_E [%.1f,%.1f): N=%2d fail %4.0f%% median frac %+5.1f%%"
                  % (survey, lo, hi, m.sum(),
                     100 * (np.abs(f[m]) > FAIL).mean(), 100 * np.median(f[m])))

    # ---- figure
    fig, axes = plt.subplots(2, 2, figsize=(13, 11))
    ax = axes[0, 0]
    im = ax.imshow(jac, vmin=0, vmax=1, cmap="viridis")
    ax.set_xticks(range(len(cur)))
    ax.set_xticklabels([c.split("@")[0] for c in cur], rotation=45, ha="right", fontsize=8)
    ax.set_yticks(range(len(cur)))
    ax.set_yticklabels([c.split("@")[0] for c in cur], fontsize=8)
    ax.set_title("Failure-set Jaccard (SLACS, current models)")
    fig.colorbar(im, ax=ax, shrink=0.8)

    ax = axes[0, 1]
    sub = W[W["survey"] == "SLACS"].dropna(subset=["frac_sel_ens@euclid", "prom_euclid"])
    ax.scatter(sub["prom_euclid"], 100 * sub["frac_sel_ens@euclid"], s=18)
    for _, r in sub[sub["frac_sel_ens@euclid"].abs() > FAIL].iterrows():
        ax.annotate(r["name"], (r["prom_euclid"], 100 * r["frac_sel_ens@euclid"]), fontsize=5)
    ax.axhline(15, ls="--", c="r"); ax.axhline(-15, ls="--", c="r"); ax.axhline(0, c="k", lw=0.5)
    ax.set_xscale("log"); ax.set_xlabel("Euclidised arc prominence (real image)")
    ax.set_ylabel("signed frac err %  (sel_ens, eval #14)")
    ax.set_title("B3/B4: error vs real arc prominence (SLACS)")

    ax = axes[1, 0]
    n_nat = W[W["survey"] == "SLACS"]["nfail_native_cur"]
    n_euc = W[W["survey"] == "SLACS"]["nfail_euclid_cur"]
    ax.hist([n_nat, n_euc], bins=np.arange(-0.5, max(len(cur_nat), len(cur_euc)) + 1.5),
            label=["native (of %d)" % len(cur_nat), "euclid (of %d)" % len(cur_euc)])
    ax.set_xlabel("number of current models failing the lens")
    ax.set_ylabel("lenses"); ax.legend(); ax.set_title("How concentrated is the tail? (SLACS)")

    ax = axes[1, 1]
    sub = W[W["survey"] == "SLACS"].dropna(subset=["frac_sel_ens@euclid"])
    ax.scatter(sub["theta_E_pub"], 100 * sub["frac_sel_ens@euclid"], s=18)
    ax.axhline(15, ls="--", c="r"); ax.axhline(-15, ls="--", c="r"); ax.axhline(0, c="k", lw=0.5)
    ax.set_xlabel("theta_E true (arcsec)"); ax.set_ylabel("signed frac err %")
    ax.set_title("sel_ens error vs theta_E (SLACS)")
    fig.tight_layout()
    fig.savefig(os.path.join(HOME, "l0_tail_forensics.png"), dpi=130)
    print("\nSaved: l0_perlens_matrix.csv, l0_prominence_cache.csv, l0_tail_forensics.png")


if __name__ == "__main__":
    main()
