#!/usr/bin/env python
"""EVAL #16 tables — PRE-REGISTERED protocol (written before any benchmark
numbers existed; eval-#15 lessons folded in):
  - ensemble = the sim-val-arbitrated variant from reb_recal.json (frozen b, s)
  - report RAW and RECALIBRATED coverage
  - 10k-bootstrap CIs + P(beats LEMON) per metric
  - per-theta_E-bin failure/bias (THE readout: did the flat-theta_E dataset
    kill the small-theta_E tail? eval #15 baseline: <0.9" fail 62%, +33%)
  - reference rows: LEMON Table 3, eval #14 pair, eval #15 all12
"""
import json
import os
import numpy as np
import pandas as pd

D = os.path.expanduser("~/einstein_cnn/brian_run")
R = json.load(open(os.path.expanduser("~/einstein_cnn/reb_recal.json")))
B, S = float(R["bias_recenter_arcsec"]), float(R["sigma_scale"])
MEMBERS = R["members"]
EXCLUDE = {"J0955+0101"}
LEMON = dict(bias=-0.03, rmse=0.14, nmad=0.11, r2=0.53)
REF = {"euclid_slacs_images": [
        ("eval #14 pair", +0.062, 0.208, 0.084, +0.33, 31.0),
        ("eval #15 all12", +0.092, 0.217, 0.091, +0.27, 27.0)],
       "euclid_s4tm_images": [
        ("eval #14 pair", +0.129, 0.250, 0.092, +0.16, 30.0),
        ("eval #15 all12", +0.136, 0.246, 0.090, +0.19, 35.0)]}
RNG = np.random.default_rng(20260711)

print("EVAL #16 — %s (%d members), frozen b=%+.4f\" s=%.3f (sim-val, TTA-consistent)"
      % (R["variant"], len(MEMBERS), B, S))
print("LEMON Table 3 ref: bias -0.03  RMSE 0.14  NMAD 0.11  R2 0.53")

ALL16 = (["reb_resnet_s%d" % i for i in (1, 2, 3, 4, 5)] +
         ["reb_incnext_s%d" % i for i in (1, 2, 3, 4, 5)] +
         ["reb_cnv2_s%d" % i for i in (1, 2, 3)] +
         ["reb_r50_s%d" % i for i in (1, 2, 3)])
DERIVED = {"custom10": ALL16[:10], "pretrained6": ALL16[10:],
           "cnv2_3": ALL16[10:13], "r50_3": ALL16[13:], "all16": ALL16}

for sample in ("euclid_slacs_images", "euclid_s4tm_images"):
    mu_all, sig_all, base = {}, {}, None
    for mtag in ALL16:
        d = pd.read_csv(os.path.join(D, "preds_l16_%s_%s.csv" % (mtag, sample)))
        if base is None:
            base = d[["name"]].copy()
            base["gt"] = d[[c for c in d.columns if "pub" in c][0]]
        assert (d["name"] == base["name"]).all()
        mu_all[mtag] = d[[c for c in d.columns if "pred" in c][0]].values.astype(float)
        sig_all[mtag] = d[[c for c in d.columns if "sigma" in c][0]].values.astype(float)

    def mix(tags):
        Mx, Sx = np.stack([mu_all[t] for t in tags]), np.stack([sig_all[t] for t in tags])
        mm = Mx.mean(0)
        return mm, np.sqrt(np.maximum((Sx ** 2 + Mx ** 2).mean(0) - mm ** 2, 1e-12))

    mu, sig_raw = mix(MEMBERS)
    base["pred"] = mu + B
    base["sigma_raw"] = sig_raw
    base["sigma_recal"] = S * sig_raw
    out_fn = os.path.join(D, "preds_l16_ens_%s.csv" % sample)
    base.rename(columns={"pred": "theta_E_pred_arcsec", "gt": "theta_E_pub_arcsec",
                         "sigma_recal": "theta_E_sigma_arcsec"}).to_csv(out_fn, index=False)

    W = base[~base["name"].isin(EXCLUDE)]
    p, t = W["pred"].values, W["gt"].values
    sraw, srec = W["sigma_raw"].values, W["sigma_recal"].values
    d_ = p - t
    frac = d_ / t
    n = len(W)

    def met(pp, tt):
        dd = pp - tt
        return dict(bias=dd.mean(), rmse=float(np.sqrt((dd ** 2).mean())),
                    nmad=float(1.4826 * np.median(np.abs(dd - np.median(dd)))),
                    r2=float(1 - (dd ** 2).sum() / ((tt - tt.mean()) ** 2).sum()),
                    fail=float((np.abs(dd / tt) > 0.15).mean()))

    m0 = met(p, t)
    boot = {k: np.empty(4000) for k in m0}
    for bi in range(4000):
        idx = RNG.integers(0, n, n)
        mb = met(p[idx], t[idx])
        for k in mb:
            boot[k][bi] = mb[k]

    tag = "SLACS (primary)" if "slacs" in sample else "S4TM (secondary)"
    print("\n=== %s  N=%d ===" % (tag, n))
    for name, bi_, rm, nm, r2_, fl in REF[sample]:
        print("  %-16s bias %+.3f  RMSE %.3f  NMAD %.3f  R2 %+.2f  fail %.0f%%"
              % (name, bi_, rm, nm, r2_, fl))
    print("  %-16s bias %+.3f  RMSE %.3f  NMAD %.3f  R2 %+.2f  fail %.0f%%"
          % ("eval #16 ens", m0["bias"], m0["rmse"], m0["nmad"], m0["r2"], 100 * m0["fail"]))
    print("  bootstrap: P(|bias|<0.03)=%.2f  P(RMSE<0.14)=%.2f  P(NMAD<0.11)=%.2f  P(R2>0.53)=%.2f"
          % ((np.abs(boot["bias"]) < 0.03).mean(), (boot["rmse"] < LEMON["rmse"]).mean(),
             (boot["nmad"] < LEMON["nmad"]).mean(), (boot["r2"] > LEMON["r2"]).mean()))
    rel = srec / p
    conf = rel <= np.median(rel)
    z_raw, z_rec = np.abs(d_) / sraw, np.abs(d_) / srec
    print("  median frac %+.1f%% | conf-half fail %.0f%% | cov RAW %.0f/%.0f%% RECAL %.0f/%.0f%%"
          % (100 * np.median(frac), 100 * (np.abs(frac[conf]) > 0.15).mean(),
             100 * (z_raw <= 1).mean(), 100 * (z_raw <= 1.96).mean(),
             100 * (z_rec <= 1).mean(), 100 * (z_rec <= 1.96).mean()))
    print("  DERIVED arch-ensembles (same passes; the pretrained-robustness readout):")
    for vname, vtags in DERIVED.items():
        vm, _ = mix(vtags)
        vm = vm + B
        vd = vm[~base["name"].isin(EXCLUDE).values] - t
        vfrac = vd / t
        print("    %-12s bias %+.3f  RMSE %.3f  NMAD %.3f  R2 %+.2f  fail %.0f%%"
              % (vname, vd.mean(), np.sqrt((vd ** 2).mean()),
                 1.4826 * np.median(np.abs(vd - np.median(vd))),
                 1 - (vd ** 2).sum() / ((t - t.mean()) ** 2).sum(),
                 100 * (np.abs(vfrac) > 0.15).mean()))
    print("  per-theta_E bins (fail%% / median frac)  [eval-#15 SLACS baseline: 62%%/+33%% at <0.9]:")
    for lo, hi in [(0.0, 0.9), (0.9, 1.2), (1.2, 1.5), (1.5, 3.0)]:
        msk = (t >= lo) & (t < hi)
        if msk.sum():
            print("    [%.1f,%.1f): N=%2d  %3.0f%%  %+5.1f%%"
                  % (lo, hi, msk.sum(), 100 * (np.abs(frac[msk]) > 0.15).mean(),
                     100 * np.median(frac[msk])))
    print("  wrote %s" % out_fn)
