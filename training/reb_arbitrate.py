#!/usr/bin/env python
"""REB grid arbitration — SIM-VAL ONLY (no benchmark contact).

Improvements over l1_arbitrate.py (eval-#15 lessons):
  1. Members evaluated with the SAME TTA rule as the benchmark predict script
     (mu = mean over 8 dihedral views; sigma^2 = mean aleatoric var + view
     spread), so the frozen sigma-scale transfers by construction.
  2. Arch-level seed-spread reported (the seed-variance paper paragraph).
  3. Per-theta_E-bin bias for the recommended ensemble — pre-eval sanity: the
     flat-theta_E dataset should remove the +7-8% small-theta_E in-dist bias.
Freezes variant + b + s into reb_recal.json for ⛔ eval #16.
"""
import json
import os
import numpy as np
import h5py
import torch

import sys
sys.path.insert(0, os.path.expanduser("~/einstein_cnn"))
from train_cnn_paltas import normalize_images, build_model

HOME = os.path.expanduser("~/einstein_cnn")
VAL = os.path.join(HOME, "val_euclid_reb_5k.h5")
DEV = "cuda" if torch.cuda.is_available() else "cpu"

MEMBERS = (["reb_resnet_s%d" % i for i in (1, 2, 3, 4, 5)] +
           ["reb_incnext_s%d" % i for i in (1, 2, 3, 4, 5)] +
           ["reb_cnv2_s%d" % i for i in (1, 2, 3)] +
           ["reb_r50_s%d" % i for i in (1, 2, 3)])

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
    path = os.path.join(HOME, tag + ".pt")
    if not os.path.exists(path):
        print("[skip] missing", tag)
        continue
    ck = torch.load(path, map_location=DEV)
    state = ck.get("model_state", ck.get("state_dict", ck))
    net = build_model(ck.get("arch", "resnet"), int(ck.get("out_dim", 2))).to(DEV)
    net.load_state_dict(state)
    net.eval()
    scale = torch.from_numpy(((amax - ck["scale_mean"]) / ck["scale_std"])
                             .astype("float32")).unsqueeze(1)
    mus, varis = [], []
    with torch.no_grad():
        for i in range(0, len(xt), 256):
            xb, sb = xt[i:i + 256].to(DEV), scale[i:i + 256].to(DEV)
            m_v, v_v = [], []
            for v in views(xb):
                out = net(v, sb)
                m_v.append(out[:, 0].cpu().numpy())
                v_v.append(np.exp(out[:, 1].clamp(-10, 3).cpu().numpy()))
            m_v, v_v = np.stack(m_v), np.stack(v_v)
            mus.append(m_v)
            varis.append(v_v)
    m = np.concatenate(mus, axis=1)      # [8, N]
    v = np.concatenate(varis, axis=1)
    mu[tag] = m.mean(0).astype("float64")
    sig[tag] = np.sqrt(v.mean(0) + m.var(0)).astype("float64")
    err = mu[tag] - theta
    print("member %-16s MAE %.4f  bias %+5.2f%%  fail %4.1f%%"
          % (tag, np.abs(err).mean(), 100 * np.median(err / theta),
             100 * (np.abs(err / theta) > 0.15).mean()))

# arch seed-spread (paper paragraph)
print("\nArch seed-spread on sim-val (MAE min-max over seeds):")
for arch, pre in (("resnet", "reb_resnet"), ("incnext", "reb_incnext"),
                  ("convnextv2", "reb_cnv2"), ("resnet50", "reb_r50")):
    maes = [np.abs(mu[t] - theta).mean() for t in mu if t.startswith(pre)]
    if maes:
        print("  %-12s n=%d  %.4f - %.4f (spread %.4f)"
              % (arch, len(maes), min(maes), max(maes), max(maes) - min(maes)))


def ens(tags):
    M = np.stack([mu[t] for t in tags])
    S = np.stack([sig[t] for t in tags])
    m = M.mean(0)
    return m, np.sqrt(np.maximum((S ** 2 + M ** 2).mean(0) - m ** 2, 1e-12))


have = set(mu)
V = {
    "resnet5": [t for t in mu if t.startswith("reb_resnet")],
    "incnext5": [t for t in mu if t.startswith("reb_incnext")],
    "cnv2_3": [t for t in mu if t.startswith("reb_cnv2")],
    "r50_3": [t for t in mu if t.startswith("reb_r50")],
}
V["custom10"] = V["resnet5"] + V["incnext5"]
V["pretrained6"] = V["cnv2_3"] + V["r50_3"]
V["all16"] = V["custom10"] + V["pretrained6"]

print("\nEnsemble variants (sim-val, TTA-consistent):")
best, best_mae = None, np.inf
for name, tags in V.items():
    if len(tags) < 2:
        continue
    m, s = ens(tags)
    err = m - theta
    mae = np.abs(err).mean()
    print("  %-12s (%2d) MAE %.4f  bias %+5.2f%%  fail %4.1f%%"
          % (name, len(tags), mae, 100 * np.median(err / theta),
             100 * (np.abs(err / theta) > 0.15).mean()))
    if mae < best_mae:
        best, best_mae = name, mae

tags = V[best]
m, s = ens(tags)
b = float(np.median(theta - m))
err_rc = np.abs((m + b) - theta)
srecal = float(np.quantile(err_rc / s, 0.68))
z = err_rc / (srecal * s)
frac = ((m + b) - theta) / theta
print("\nRECOMMENDED: %s | b=%+.4f\" | s=%.3f | recal cov 68/95: %.0f%%/%.0f%% | "
      "rho(sigma,|err|)=%+.2f"
      % (best, b, srecal, 100 * (z <= 1).mean(), 100 * (z <= 1.96).mean(),
         np.corrcoef(s, err_rc)[0, 1]))
print("Per-theta_E bias of recommended (pre-eval sanity — expect ~flat now):")
for lo, hi in ((0.45, 0.9), (0.9, 1.2), (1.2, 1.5), (1.5, 2.3)):
    msk = (theta >= lo) & (theta < hi)
    print("  [%0.2f,%0.2f): N=%5d  median frac %+5.1f%%  fail %4.1f%%"
          % (lo, hi, msk.sum(), 100 * np.median(frac[msk]),
             100 * (np.abs(frac[msk]) > 0.15).mean()))

json.dump(dict(variant=best, members=tags, bias_recenter_arcsec=b,
               sigma_scale=srecal,
               fitted_on="val_euclid_reb_5k.h5 (sim-val ONLY, TTA-consistent)",
               note="frozen BEFORE benchmark eval #16"),
          open(os.path.join(HOME, "reb_recal.json"), "w"), indent=2)
np.savez(os.path.join(HOME, "reb_simval_preds.npz"), theta=theta,
         **{("mu_" + k): v for k, v in mu.items()},
         **{("sig_" + k): v for k, v in sig.items()})
print("frozen -> reb_recal.json ; preds -> reb_simval_preds.npz")
