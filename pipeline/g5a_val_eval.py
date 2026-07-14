#!/usr/bin/env python
"""G5a harvest: challenge-val (N=1000) scores for the 12 Path-A members.
Ensembles per variant (cnv2_3, r50_3, all6), TTA x8, our metrics + the
challenge's TDLMC grading (chi2/P/A) with raw and calibrated sigma.
HONESTY NOTE printed in the report: best-epoch selection used this same val
split, so these numbers are mildly optimistic; the hidden-test submission is
the clean readout. Writes ens CSVs preds_g5a_<variant>_<ens>.csv."""
import csv
import os
import sys

import h5py
import numpy as np
import torch

EC = os.path.expanduser("~/einstein_cnn")
OUT = os.path.expanduser("~/cosmos_acs/roman_dc")
sys.path.insert(0, EC)
from train_cnn_paltas import build_model, normalize_images  # noqa: E402

DEV = "cuda" if torch.cuda.is_available() else "cpu"
VARIANTS = {"f106": 1, "3band": 3}
ARCHS = {"cnv2": "convnextv2", "r50": "resnet50"}


def tta_predict(model, x):
    """x: (N,C,H,W) tensor. Returns mu, sigma (total-variance over 8 views)."""
    mus, sigs = [], []
    for k in range(4):
        for fl in (False, True):
            v = torch.rot90(x, k, dims=[-2, -1])
            if fl:
                v = torch.flip(v, dims=[-2])
            outs = []
            with torch.no_grad():
                for i in range(0, len(v), 256):
                    b = v[i:i + 256].to(DEV)
                    s = torch.zeros(len(b), 1, device=DEV)
                    outs.append(model(b, s).cpu())
            o = torch.cat(outs)
            mus.append(o[:, 0].numpy())
            sigs.append(np.exp(0.5 * o[:, 1].clamp(-10, 3).numpy()))
    M, S = np.array(mus), np.array(sigs)
    mu = M.mean(0)
    return mu, np.sqrt(np.maximum((S ** 2 + M ** 2).mean(0) - mu ** 2, 1e-12))


def mix(mems):
    M = np.array([m[0] for m in mems])
    S = np.array([m[1] for m in mems])
    mu = M.mean(0)
    return mu, np.sqrt(np.maximum((S ** 2 + M ** 2).mean(0) - mu ** 2, 1e-12))


def report(tag, p, s, t):
    d = p - t
    frac = d / t
    z = d / s
    sc_q68 = float(np.quantile(np.abs(z), 0.68))
    sc_rms = float(np.sqrt((z ** 2).mean()))
    for lab, sc in (("raw", 1.0), ("q68", sc_q68), ("rmsz", sc_rms)):
        ss = s * sc
        print("  %-14s %-5s bias %+.3f RMSE %.3f NMAD %.3f R2 %+.2f fail %.0f%% | "
              "chi2 %6.2f  P %.3f  A %+.4f"
              % (tag, lab, d.mean(), float(np.sqrt((d ** 2).mean())),
                 float(1.4826 * np.median(np.abs(d - np.median(d)))),
                 float(1 - (d ** 2).sum() / ((t - t.mean()) ** 2).sum()),
                 100 * (np.abs(frac) > 0.15).mean(),
                 float(((d / ss) ** 2).mean()), float((ss / t).mean()),
                 float(frac.mean())))
    return sc_rms


print("G5a Path-A harvest on challenge-val N=1000 (NOTE: best-epoch used this "
      "split -> mildly optimistic; hidden test is the clean readout)")
for var, ic in VARIANTS.items():
    with h5py.File(os.path.join(EC, "val_rung0_%s.h5" % var), "r") as f:
        x = f["lensed"][:]
        t = f["theta_E"][:].astype(float)
        names = [n.decode() if isinstance(n, bytes) else str(n) for n in f["names"][:]]
    x = normalize_images(x.astype("float32"), "asinh", 1.0)
    xt = torch.from_numpy(x)
    if xt.ndim == 3:
        xt = xt.unsqueeze(1)
    mems = {}
    for short, arch in ARCHS.items():
        for sd in (1, 2, 3):
            ck = torch.load(os.path.join(EC, "rung0_%s_%s_s%d.pt" % (var, short, sd)),
                            map_location="cpu")
            model = build_model(arch, ck["out_dim"], in_chans=ic).to(DEV)
            model.load_state_dict(ck["state_dict"])
            model.eval()
            mems["%s_s%d" % (short, sd)] = tta_predict(model, xt)
    print("== VARIANT %s ==" % var)
    for ens, keys in (("cnv2_3", ["cnv2_s1", "cnv2_s2", "cnv2_s3"]),
                      ("r50_3", ["r50_s1", "r50_s2", "r50_s3"]),
                      ("all6", list(mems.keys()))):
        mu, s = mix([mems[k] for k in keys])
        sc = report("%s/%s" % (var, ens), mu, s, t)
        fn = os.path.join(OUT, "preds_g5a_%s_%s.csv" % (var, ens))
        with open(fn, "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["ID", "theta_E", "theta_E_sigma", "theta_E_true",
                        "sigma_scale_rmsz_val"])
            for i, n in enumerate(names):
                w.writerow([n, "%.4f" % mu[i], "%.4f" % (s[i] * sc), "%.4f" % t[i],
                            "%.4f" % sc])
        print("  wrote %s (sigma pre-scaled x%.2f rmsz)" % (fn, sc))
print("G5A_VAL_EVAL_DONE")
