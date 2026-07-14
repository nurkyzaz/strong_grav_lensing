#!/usr/bin/env python
"""G5a v2 harvest + submission build (Nurkyz 2026-07-14: retrain with more
data, maximize the certainty score). v2 design: train on 10,660 (fresh
500-lens calibration holdout — a zero-holdout run cannot calibrate sigma,
and TDLMC Goodness punishes miscalibration quadratically). Harvest on the
500: ensembles f106_all6 / 3band_all6 / MIXED12 (all 12 members across both
variants — decorrelation shrinks honest sigma = better Precision at chi2=1).
Writes submission2 CSVs from the unlabeled set for 3band_all6_v2 and
mixed12_v2."""
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
ARCHS = {"cnv2": "convnextv2", "r50": "resnet50"}


def tta_predict(model, x):
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


def load_set(fn):
    with h5py.File(fn, "r") as f:
        x = f["lensed"][:]
        names = [n.decode() if isinstance(n, bytes) else str(n) for n in f["names"][:]]
        t = f["theta_E"][:].astype(float) if "theta_E" in f else None
    x = normalize_images(x.astype("float32"), "asinh", 1.0)
    xt = torch.from_numpy(x)
    if xt.ndim == 3:
        xt = xt.unsqueeze(1)
    return xt, names, t


def run_members(xt, var, ic):
    out = []
    for short, arch in ARCHS.items():
        for sd in (1, 2, 3):
            ck = torch.load(os.path.join(EC, "rung0v2_%s_%s_s%d.pt" % (var, short, sd)),
                            map_location="cpu")
            model = build_model(arch, ck["out_dim"], in_chans=ic).to(DEV)
            model.load_state_dict(ck["state_dict"])
            model.eval()
            out.append(tta_predict(model, xt))
            print("  %s %s_s%d done" % (var, short, sd), flush=True)
    return out


# --- calibration harvest on the fresh 500 ---
val, scales = {}, {}
for var, ic in (("f106", 1), ("3band", 3)):
    xt, names, t = load_set(os.path.join(EC, "val_rung0v2_%s.h5" % var))
    val[var] = (run_members(xt, var, ic), t)
mems_mixed = val["f106"][0] + val["3band"][0]
t = val["f106"][1]
print("== v2 harvest on calib-500 (selection touched this split; hidden test is clean) ==")
for tag, mems in (("f106_all6", val["f106"][0]), ("3band_all6", val["3band"][0]),
                  ("mixed12", mems_mixed)):
    mu, s = mix(mems)
    d = mu - t
    sc = float(np.sqrt(((d / s) ** 2).mean()))          # rmsz -> chi2=1
    ss = s * sc
    scales[tag] = sc
    print("%-10s RMSE %.3f NMAD %.3f R2 %+.2f | chi2 %.3f  P %.4f  A %+.4f  (sigma x%.2f)"
          % (tag, float(np.sqrt((d ** 2).mean())),
             float(1.4826 * np.median(np.abs(d - np.median(d)))),
             float(1 - (d ** 2).sum() / ((t - t.mean()) ** 2).sum()),
             float(((d / ss) ** 2).mean()), float((ss / t).mean()),
             float((d / t).mean()), sc))

# --- submission2 on the unlabeled set ---
un = {}
for var, ic in (("f106", 1), ("3band", 3)):
    xt, names_u, _ = load_set(os.path.join(EC, "eval_rung0_unlabeled_%s.h5" % var))
    un[var] = run_members(xt, var, ic)
for tag, mems in (("3band_all6", un["3band"]), ("mixed12", un["f106"] + un["3band"])):
    mu, s = mix(mems)
    s = s * scales[tag]
    fn = os.path.join(OUT, "rung0_submission2_%s_v2.csv" % tag)
    with open(fn, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["ID", "theta_E", "theta_E_sigma"])
        for i, n in enumerate(names_u):
            w.writerow([n, "%.5f" % mu[i], "%.5f" % s[i]])
    print("wrote %s  N=%d  theta med %.3f  sigma med %.3f" % (fn, len(names_u),
                                                              np.median(mu), np.median(s)))
print("G5A2_DONE")
