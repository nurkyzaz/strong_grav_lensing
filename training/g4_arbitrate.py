#!/usr/bin/env python
"""G4 arbitration — SIM-VAL ONLY, TTA-consistent (reb_arbitrate lineage).
Members: 16 grid + logpolar probe. Freezes g4_recal.json for ⛔ eval #17."""
import json
import os
import numpy as np
import h5py
import torch

import sys
sys.path.insert(0, os.path.expanduser("~/einstein_cnn"))
from train_cnn_paltas import normalize_images, build_model

HOME = os.path.expanduser("~/einstein_cnn")
VAL = os.path.join(HOME, "val_g4_5k.h5")
DEV = "cuda" if torch.cuda.is_available() else "cpu"

MEMBERS = (["g4_resnet_s%d" % i for i in (1, 2, 3, 4, 5)] +
           ["g4_incnext_s%d" % i for i in (1, 2, 3, 4, 5)] +
           ["g4_cnv2_s%d" % i for i in (1, 2, 3)] +
           ["g4_r50_s%d" % i for i in (1, 2, 3)] +
           ["g4_logpolar_s1"])

with h5py.File(VAL, "r") as f:
    key = "lensed" if "lensed" in f else "images"
    imgs = f[key][:].astype("float32")
    theta = f["theta_E"][:].astype("float64")
if imgs.ndim == 4:
    imgs = imgs[:, 0]
x = normalize_images(imgs, "asinh", 1.0)
amax = np.arcsinh(imgs.max(axis=(1, 2)))
xt = torch.from_numpy(x).unsqueeze(1).float()


def views(t):
    outs = []
    for flip in (False, True):
        tt = torch.flip(t, dims=[-1]) if flip else t
        for k in range(4):
            outs.append(torch.rot90(tt, k, dims=[-2, -1]))
    return outs


mu, sig = {}, {}
for tag in MEMBERS:
    p = os.path.join(HOME, tag + ".pt")
    if not os.path.exists(p):
        print("[skip]", tag)
        continue
    ck = torch.load(p, map_location=DEV)
    net = build_model(ck.get("arch", "resnet"), int(ck.get("out_dim", 2))).to(DEV)
    net.load_state_dict(ck.get("model_state", ck.get("state_dict", ck)))
    net.eval()
    scale = torch.from_numpy(((amax - ck["scale_mean"]) / ck["scale_std"])
                             .astype("float32")).unsqueeze(1)
    mus, varis = [], []
    with torch.no_grad():
        for i in range(0, len(xt), 256):
            xb, sb = xt[i:i + 256].to(DEV), scale[i:i + 256].to(DEV)
            mv, vv = [], []
            for v in views(xb):
                out = net(v, sb)
                mv.append(out[:, 0].cpu().numpy())
                vv.append(np.exp(out[:, 1].clamp(-10, 3).cpu().numpy()))
            mus.append(np.stack(mv))
            varis.append(np.stack(vv))
    m = np.concatenate(mus, axis=1)
    v = np.concatenate(varis, axis=1)
    mu[tag] = m.mean(0).astype("float64")
    sig[tag] = np.sqrt(v.mean(0) + m.var(0)).astype("float64")
    err = mu[tag] - theta
    print("member %-16s MAE %.4f  bias %+5.2f%%  fail %4.1f%%"
          % (tag, np.abs(err).mean(), 100 * np.median(err / theta),
             100 * (np.abs(err / theta) > 0.15).mean()))

print("\nSMALL-THETA pre-eval readout (the GEN4 hypothesis):")
for tag in mu:
    frac = (mu[tag] - theta) / theta
    m_ = theta < 0.9
    print("  %-16s theta<0.9: median frac %+5.1f%%  fail %4.1f%%"
          % (tag, 100 * np.median(frac[m_]), 100 * (np.abs(frac[m_]) > 0.15).mean()))


def ens(tags):
    M = np.stack([mu[t] for t in tags])
    S = np.stack([sig[t] for t in tags])
    m = M.mean(0)
    return m, np.sqrt(np.maximum((S ** 2 + M ** 2).mean(0) - m ** 2, 1e-12))


V = {"resnet5": [t for t in mu if "resnet_s" in t],
     "incnext5": [t for t in mu if "incnext" in t],
     "cnv2_3": [t for t in mu if "cnv2" in t],
     "r50_3": [t for t in mu if "r50" in t]}
V["custom10"] = V["resnet5"] + V["incnext5"]
V["all16"] = V["custom10"] + V["cnv2_3"] + V["r50_3"]
if "g4_logpolar_s1" in mu:
    V["all17+lp"] = V["all16"] + ["g4_logpolar_s1"]

print("\nEnsembles (sim-val, TTA-consistent):")
best, bmae = None, np.inf
for name, tags in V.items():
    if len(tags) < 2:
        continue
    m, s = ens(tags)
    mae = np.abs(m - theta).mean()
    print("  %-10s (%2d) MAE %.4f  bias %+5.2f%%  fail %4.1f%%"
          % (name, len(tags), mae, 100 * np.median((m - theta) / theta),
             100 * (np.abs((m - theta) / theta) > 0.15).mean()))
    if mae < bmae:
        best, bmae = name, mae

tags = V[best]
m, s = ens(tags)
b = float(np.median(theta - m))
err = np.abs((m + b) - theta)
srecal = float(np.quantile(err / s, 0.68))
z = err / (srecal * s)
print("\nRECOMMENDED: %s | b=%+.4f | s=%.3f | cov %.0f/%.0f%% | rho %.2f"
      % (best, b, srecal, 100 * (z <= 1).mean(), 100 * (z <= 1.96).mean(),
         np.corrcoef(s, err)[0, 1]))
json.dump(dict(variant=best, members=tags, bias_recenter_arcsec=b,
               sigma_scale=srecal, fitted_on="val_g4_5k.h5 (sim-val, TTA)",
               note="frozen before eval #17"),
          open(os.path.join(HOME, "g4_recal.json"), "w"), indent=2)
print("frozen -> g4_recal.json")
