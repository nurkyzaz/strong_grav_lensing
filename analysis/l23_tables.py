#!/usr/bin/env python
"""EVAL #23 — DERIVED two-model ensemble (Nurkyz ruling 2026-07-13): mean of
G4 cnv2_3 (eval #19 Euclid primary) and g4ar r50_3 (eval #22 S4TM-Euclid best),
computed ENTIRELY from the banked per-lens CSVs in results/ — no new model
passes on the frozen benchmark. Conventions identical to l16/l22 tables:
met() defs, EXCLUDE J0955+0101, 4000-draw bootstrap, per-theta bins.
Each side keeps its own frozen sim-val recal (g4_recal / g4ar_recal), applied
exactly as the parent evals applied them; equal weight per MODEL (not member).
Self-check: each side alone must reproduce its parent published row."""
import os
import numpy as np
import pandas as pd

D = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "results")
EXCLUDE = {"J0955+0101"}
LEMON = dict(bias=-0.03, rmse=0.14, nmad=0.11, r2=0.53)
RNG = np.random.default_rng(20260713)

# frozen recals (cluster g4_recal.json / g4ar_recal.json, both fitted sim-val pre-eval)
SIDES = {
    "g4_cnv2_3":  dict(files="preds_l19_g4_cnv2_s%d_%s.csv",  seeds=(1, 2, 3),
                       B=-0.0015423929634094113, S=0.9618278137772992,
                       parent="eval #19"),
    "g4ar_r50_3": dict(files="preds_l22_g4ar_r50_s%d_%s.csv", seeds=(1, 2, 3),
                       B=-0.0032367853597006224, S=1.0152982705791773,
                       parent="eval #22"),
}
REF = {"euclid_slacs_images_g3": [
        ("eval #19 g4cnv2", -0.010, 0.137, 0.056, +0.71, 15.0),
        ("eval #22 r50_3", -0.054, 0.202, 0.087, +0.37, 24.0),
        ("eval #22 ens", -0.028, 0.157, 0.061, +0.62, 15.0)],
       "euclid_s4tm_images_g3": [
        ("eval #19 g4cnv2", None, None, None, None, None),  # printed from side repro
        ("eval #22 r50_3", +0.020, 0.103, 0.071, +0.86, 22.0),
        ("eval #22 ens", +0.034, 0.134, 0.080, +0.76, 25.0)]}


def met(pp, tt):
    dd = pp - tt
    return dict(bias=dd.mean(), rmse=float(np.sqrt((dd ** 2).mean())),
                nmad=float(1.4826 * np.median(np.abs(dd - np.median(dd)))),
                r2=float(1 - (dd ** 2).sum() / ((tt - tt.mean()) ** 2).sum()),
                fail=float((np.abs(dd / tt) > 0.15).mean()))


def row(label, m):
    print("  %-18s bias %+.3f  RMSE %.3f  NMAD %.3f  R2 %+.2f  fail %.0f%%"
          % (label, m["bias"], m["rmse"], m["nmad"], m["r2"], 100 * m["fail"]))


print("EVAL #23 — derived ensemble mean(G4 cnv2_3, g4ar r50_3); frozen per-side recals; from banked CSVs")
for sample in ("euclid_slacs_images_g3", "euclid_s4tm_images_g3"):
    names, gt = None, None
    side_mu, side_sig = {}, {}
    for sname, cfg in SIDES.items():
        mus, sigs = [], []
        for s in cfg["seeds"]:
            d = pd.read_csv(os.path.join(D, cfg["files"] % (s, sample)))
            if names is None:
                names, gt = d["name"].copy(), d["theta_E_pub_arcsec"].values.astype(float)
            assert (d["name"] == names).all(), "name order mismatch: %s seed %d" % (sname, s)
            mus.append(d["theta_E_pred_arcsec"].values.astype(float))
            sigs.append(d["theta_E_sigma_arcsec"].values.astype(float))
        M, Sg = np.stack(mus), np.stack(sigs)
        mm = M.mean(0)
        s_ens = np.sqrt(np.maximum((Sg ** 2 + M ** 2).mean(0) - mm ** 2, 1e-12))
        side_mu[sname] = mm + cfg["B"]
        side_sig[sname] = cfg["S"] * s_ens

    Mx = np.stack([side_mu[s] for s in SIDES])
    Sx = np.stack([side_sig[s] for s in SIDES])
    mu = Mx.mean(0)
    sig = np.sqrt(np.maximum((Sx ** 2 + Mx ** 2).mean(0) - mu ** 2, 1e-12))

    keep = ~names.isin(EXCLUDE).values
    p, t, srec = mu[keep], gt[keep], sig[keep]
    n = len(p)
    d_, frac = p - t, (p - t) / t

    tag = "SLACS (primary)" if "slacs" in sample else "S4TM (secondary)"
    print("\n=== %s  N=%d ===" % (tag, n))
    for rname, bi_, rm, nm, r2_, fl in REF[sample]:
        if bi_ is not None:
            print("  %-18s bias %+.3f  RMSE %.3f  NMAD %.3f  R2 %+.2f  fail %.0f%%"
                  % (rname, bi_, rm, nm, r2_, fl))
    for sname in SIDES:  # reproduction check of parent rows, same passes
        row("side " + sname, met(side_mu[sname][keep], t))
    m0 = met(p, t)
    row("EVAL #23 ens2", m0)
    boot = {k: np.empty(4000) for k in m0}
    for bi in range(4000):
        idx = RNG.integers(0, n, n)
        mb = met(p[idx], t[idx])
        for k in mb:
            boot[k][bi] = mb[k]
    print("  bootstrap: P(|bias|<0.03)=%.2f  P(RMSE<0.14)=%.2f  P(NMAD<0.11)=%.2f  P(R2>0.53)=%.2f"
          % ((np.abs(boot["bias"]) < 0.03).mean(), (boot["rmse"] < LEMON["rmse"]).mean(),
             (boot["nmad"] < LEMON["nmad"]).mean(), (boot["r2"] > LEMON["r2"]).mean()))
    rel = srec / p
    conf = rel <= np.median(rel)
    z = np.abs(d_) / srec
    print("  median frac %+.1f%% | conf-half fail %.0f%% | cov RECAL %.0f/%.0f%%"
          % (100 * np.median(frac), 100 * (np.abs(frac[conf]) > 0.15).mean(),
             100 * (z <= 1).mean(), 100 * (z <= 1.96).mean()))
    print("  per-theta_E bins (fail%% / median frac):")
    for lo, hi in [(0.0, 0.9), (0.9, 1.2), (1.2, 1.5), (1.5, 3.0)]:
        msk = (t >= lo) & (t < hi)
        if msk.sum():
            print("    [%.1f,%.1f): N=%2d  %3.0f%%  %+5.1f%%"
                  % (lo, hi, msk.sum(), 100 * (np.abs(frac[msk]) > 0.15).mean(),
                     100 * np.median(frac[msk])))
    out = pd.DataFrame(dict(name=names, theta_E_pred_arcsec=mu,
                            theta_E_pub_arcsec=gt, theta_E_sigma_arcsec=sig))
    out_fn = os.path.join(D, "preds_l23_ens2_%s.csv" % sample)
    out.to_csv(out_fn, index=False)
    print("  wrote %s" % out_fn)
