#!/usr/bin/env python
"""EVAL #17 tables — PRE-REGISTERED before any benchmark numbers exist.
GEN4 hypothesis on the line: self-consistent light->mass training should
attack the small-theta_E bin (eval #15/#16 baseline: 62% fail, +29..33%).
Primary = the g4_recal.json variant; arch ensembles + logpolar as DERIVED
columns from the same passes; bootstrap P(beats LEMON); RAW+RECAL coverage."""
import json
import os
import numpy as np
import pandas as pd

D = os.path.expanduser("~/einstein_cnn/brian_run")
R = json.load(open(os.path.expanduser("~/einstein_cnn/g4_recal.json")))
B, S = float(R["bias_recenter_arcsec"]), float(R["sigma_scale"])
MEMBERS = R["members"]
EXCLUDE = {"J0955+0101"}
LEMON = dict(bias=-0.03, rmse=0.14, nmad=0.11, r2=0.53)
REF = {"euclid_slacs_images": [
        ("eval #14 pair", +0.062, 0.208, 0.084, +0.33, 31.0),
        ("eval #16 resnet5", +0.063, 0.220, 0.131, +0.25, 31.0)],
       "euclid_s4tm_images": [
        ("eval #14 pair", +0.129, 0.250, 0.092, +0.16, 30.0),
        ("eval #16 resnet5", +0.116, 0.245, 0.095, +0.19, 32.0)]}
ALL = (["g4_resnet_s%d" % i for i in (1, 2, 3, 4, 5)] +
       ["g4_incnext_s%d" % i for i in (1, 2, 3, 4, 5)] +
       ["g4_cnv2_s%d" % i for i in (1, 2, 3)] +
       ["g4_r50_s%d" % i for i in (1, 2, 3)] + ["g4_logpolar_s1"])
DERIVED = {"custom10": ALL[:10], "cnv2_3": ALL[10:13], "r50_3": ALL[13:16],
           "all16": ALL[:16], "logpolar1": ALL[16:]}
RNG = np.random.default_rng(20260712)

print("EVAL #17 — %s (%d members), frozen b=%+.4f s=%.3f (sim-val, TTA)"
      % (R["variant"], len(MEMBERS), B, S))
print("LEMON ref: bias -0.03  RMSE 0.14  NMAD 0.11  R2 0.53")

for sample in ("euclid_slacs_images", "euclid_s4tm_images"):
    mu_all, sig_all, base = {}, {}, None
    for t in ALL:
        fn = os.path.join(D, "preds_l17_%s_%s.csv" % (t, sample))
        if not os.path.exists(fn):
            continue
        d = pd.read_csv(fn)
        if base is None:
            base = d[["name"]].copy()
            base["gt"] = d[[c for c in d.columns if "pub" in c][0]]
        mu_all[t] = d[[c for c in d.columns if "pred" in c][0]].values.astype(float)
        sig_all[t] = d[[c for c in d.columns if "sigma" in c][0]].values.astype(float)

    def mix(tags):
        tags = [t for t in tags if t in mu_all]
        M = np.stack([mu_all[t] for t in tags])
        Sg = np.stack([sig_all[t] for t in tags])
        m = M.mean(0)
        return m, np.sqrt(np.maximum((Sg ** 2 + M ** 2).mean(0) - m ** 2, 1e-12))

    mu, sraw = mix(MEMBERS)
    base["pred"] = mu + B
    base["sigma_raw"] = sraw
    base["sigma_recal"] = S * sraw
    out_fn = os.path.join(D, "preds_l17_ens_%s.csv" % sample)
    base.rename(columns={"pred": "theta_E_pred_arcsec", "gt": "theta_E_pub_arcsec",
                         "sigma_recal": "theta_E_sigma_arcsec"}).to_csv(out_fn, index=False)
    W = base[~base["name"].isin(EXCLUDE)]
    p, t_, srw, src_ = (W["pred"].values, W["gt"].values,
                        W["sigma_raw"].values, W["sigma_recal"].values)
    d_ = p - t_
    frac = d_ / t_
    n = len(W)

    def met(pp, tt):
        dd = pp - tt
        return dict(bias=dd.mean(), rmse=float(np.sqrt((dd ** 2).mean())),
                    nmad=float(1.4826 * np.median(np.abs(dd - np.median(dd)))),
                    r2=float(1 - (dd ** 2).sum() / ((tt - tt.mean()) ** 2).sum()),
                    fail=float((np.abs(dd / tt) > 0.15).mean()))
    m0 = met(p, t_)
    boot = {k: np.empty(4000) for k in m0}
    for bi in range(4000):
        idx = RNG.integers(0, n, n)
        mb = met(p[idx], t_[idx])
        for k in mb:
            boot[k][bi] = mb[k]
    tag = "SLACS (primary)" if "slacs" in sample else "S4TM (secondary)"
    print("\n=== %s N=%d ===" % (tag, n))
    for nm, b_, rm, nd, r2_, fl in REF[sample]:
        print("  %-16s bias %+.3f RMSE %.3f NMAD %.3f R2 %+.2f fail %.0f%%"
              % (nm, b_, rm, nd, r2_, fl))
    print("  %-16s bias %+.3f RMSE %.3f NMAD %.3f R2 %+.2f fail %.0f%%"
          % ("eval #17 ens", m0["bias"], m0["rmse"], m0["nmad"], m0["r2"], 100 * m0["fail"]))
    print("  boot: P(|bias|<.03)=%.2f P(RMSE<.14)=%.2f P(NMAD<.11)=%.2f P(R2>.53)=%.2f"
          % ((np.abs(boot["bias"]) < .03).mean(), (boot["rmse"] < .14).mean(),
             (boot["nmad"] < .11).mean(), (boot["r2"] > .53).mean()))
    rel = src_ / p
    conf = rel <= np.median(rel)
    print("  med frac %+.1f%% | conf-half fail %.0f%% | cov RAW %.0f/%.0f RECAL %.0f/%.0f"
          % (100 * np.median(frac), 100 * (np.abs(frac[conf]) > .15).mean(),
             100 * (np.abs(d_) / srw <= 1).mean(), 100 * (np.abs(d_) / srw <= 1.96).mean(),
             100 * (np.abs(d_) / src_ <= 1).mean(), 100 * (np.abs(d_) / src_ <= 1.96).mean()))
    print("  DERIVED (same passes):")
    for vn, vt in DERIVED.items():
        if not [t for t in vt if t in mu_all]:
            continue
        vm, _ = mix(vt)
        vd = (vm + B)[~base["name"].isin(EXCLUDE).values] - t_
        vf = vd / t_
        print("    %-10s bias %+.3f RMSE %.3f NMAD %.3f R2 %+.2f fail %.0f%%"
              % (vn, vd.mean(), np.sqrt((vd ** 2).mean()),
                 1.4826 * np.median(np.abs(vd - np.median(vd))),
                 1 - (vd ** 2).sum() / ((t_ - t_.mean()) ** 2).sum(),
                 100 * (np.abs(vf) > .15).mean()))
    print("  per-theta bins [#16 baseline at <0.9: 62%%/+28.7%%]:")
    for lo, hi in [(0.0, 0.9), (0.9, 1.2), (1.2, 1.5), (1.5, 3.0)]:
        msk = (t_ >= lo) & (t_ < hi)
        if msk.sum():
            print("    [%.1f,%.1f): N=%2d %3.0f%% %+5.1f%%"
                  % (lo, hi, msk.sum(), 100 * (np.abs(frac[msk]) > .15).mean(),
                     100 * np.median(frac[msk])))
    print("  wrote", out_fn)
