#!/usr/bin/env python
"""L1 arbitration: evaluate all deep-ensemble members + compositions on SIM-VAL
ONLY, pick the recommended ensemble, and freeze bias-recentering + sigma-recal
constants for it (written to l1_recal.json). NO benchmark contact here - the
frozen constants go to eval #15, which happens with Nurkyz at the checkpoint.

Members (12): the two eval-#14 seed-0 checkpoints + 8 fresh seeds (1-4 x 2
archs) + 2 E5 transfer-init runs. Plain forward passes (no TTA) for
arbitration; TTA stays an eval-time-only choice as in the protocol.

Ensemble sigma: mixture variance sigma_ens^2 = mean(sigma_i^2 + mu_i^2) - mu_ens^2.
Bias recentering: additive offset b = median(theta - pred) on sim-val.
Sigma recal: scale s such that 68% of |err_recentered| <= s * sigma_ens.
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
VAL = os.path.join(HOME, "val_euclid_sel_5k.h5")
DEV = "cuda" if torch.cuda.is_available() else "cpu"

MEMBERS = [
    ("inc_s0", "einstein_cnn_euclid_sel_inceptionnext.pt"),
    ("inc_s1", "einstein_cnn_euclid_sel_inceptionnext_s1.pt"),
    ("inc_s2", "einstein_cnn_euclid_sel_inceptionnext_s2.pt"),
    ("inc_s3", "einstein_cnn_euclid_sel_inceptionnext_s3.pt"),
    ("inc_s4", "einstein_cnn_euclid_sel_inceptionnext_s4.pt"),
    ("inc_tinit", "einstein_cnn_euclid_sel_inceptionnext_tinit.pt"),
    ("res_s0", "einstein_cnn_euclid_sel_resnet.pt"),
    ("res_s1", "einstein_cnn_euclid_sel_resnet_s1.pt"),
    ("res_s2", "einstein_cnn_euclid_sel_resnet_s2.pt"),
    ("res_s3", "einstein_cnn_euclid_sel_resnet_s3.pt"),
    ("res_s4", "einstein_cnn_euclid_sel_resnet_s4.pt"),
    ("res_tinit", "einstein_cnn_euclid_sel_resnet_tinit.pt"),
]

with h5py.File(VAL, "r") as f:
    key = "lensed" if "lensed" in f else "images"
    imgs = f[key][:].astype("float32")
    theta = f["theta_E"][:].astype("float64")
if imgs.ndim == 4:
    imgs = imgs[:, 0]
x = normalize_images(imgs, "asinh", 1.0)
amax = np.arcsinh(imgs.max(axis=(1, 2)))

mu, sig = {}, {}
for tag, fn in MEMBERS:
    path = os.path.join(HOME, fn)
    if not os.path.exists(path):
        print("[skip] missing member %s" % fn)
        continue
    ck = torch.load(path, map_location=DEV)
    state = ck.get("model_state", ck.get("state_dict", ck))
    net = build_model(ck.get("arch", "resnet"), int(ck.get("out_dim", 2))).to(DEV)
    net.load_state_dict(state)
    net.eval()
    scale = (amax - ck["scale_mean"]) / ck["scale_std"]
    m, s = [], []
    with torch.no_grad():
        for i in range(0, len(x), 256):
            xb = torch.from_numpy(x[i:i + 256]).unsqueeze(1).float().to(DEV)
            sb = torch.from_numpy(scale[i:i + 256].astype("float32")).unsqueeze(1).to(DEV)
            out = net(xb, sb)
            m.append(out[:, 0].cpu().numpy())
            if out.shape[1] > 1:
                s.append(np.sqrt(np.exp(out[:, 1].cpu().numpy())))
    mu[tag] = np.concatenate(m).astype("float64")
    sig[tag] = np.concatenate(s).astype("float64") if s else np.full(len(x), np.nan)
    err = mu[tag] - theta
    print("member %-10s MAE %.4f  bias(med frac) %+5.2f%%  fail %4.1f%%"
          % (tag, np.abs(err).mean(), 100 * np.median(err / theta),
             100 * (np.abs(err / theta) > 0.15).mean()))


def ens(tags):
    M = np.stack([mu[t] for t in tags])
    S = np.stack([sig[t] for t in tags])
    m = M.mean(0)
    v = (S ** 2 + M ** 2).mean(0) - m ** 2
    return m, np.sqrt(np.maximum(v, 1e-12))


have = set(mu)
variants = {}
inc = [t for t in ("inc_s0", "inc_s1", "inc_s2", "inc_s3", "inc_s4") if t in have]
res = [t for t in ("res_s0", "res_s1", "res_s2", "res_s3", "res_s4") if t in have]
variants["inc5"] = inc
variants["res5"] = res
variants["scratch10"] = inc + res
if "inc_tinit" in have and "res_tinit" in have:
    variants["tinit2"] = ["inc_tinit", "res_tinit"]
    variants["all12"] = inc + res + ["inc_tinit", "res_tinit"]
variants["pair_s0"] = [t for t in ("inc_s0", "res_s0") if t in have]  # = eval #14 recipe

print("\nEnsemble variants on sim-val (selection on SIM-VAL ONLY):")
best, best_mae = None, np.inf
for name, tags in variants.items():
    if len(tags) < 2:
        continue
    m, s = ens(tags)
    err = m - theta
    mae = np.abs(err).mean()
    print("  %-10s (%2d members) MAE %.4f  bias %+5.2f%%  fail %4.1f%%"
          % (name, len(tags), mae, 100 * np.median(err / theta),
             100 * (np.abs(err / theta) > 0.15).mean()))
    if mae < best_mae:
        best, best_mae = name, mae

tags = variants[best]
m, s = ens(tags)
b = float(np.median(theta - m))          # additive recentering, sim-val frozen
err_rc = np.abs((m + b) - theta)
srecal = float(np.quantile(err_rc / s, 0.68))
z = err_rc / (srecal * s)
print("\nRECOMMENDED: %s | recentering b=%+.4f\" | sigma scale s=%.3f | "
      "recal coverage 68/95: %.0f%%/%.0f%%"
      % (best, b, srecal, 100 * (z <= 1).mean(), 100 * (z <= 1.96).mean()))
rho = np.corrcoef(s, err_rc)[0, 1]
print("rho(sigma, |err|) = %+.2f" % rho)

out = dict(variant=best, members=tags, bias_recenter_arcsec=b,
           sigma_scale=srecal, fitted_on="val_euclid_sel_5k.h5 (sim-val ONLY)",
           note="plain-forward arbitration; TTA remains eval-time choice; "
                "constants FROZEN before benchmark eval #15")
with open(os.path.join(HOME, "l1_recal.json"), "w") as f:
    json.dump(out, f, indent=2)
print("frozen -> l1_recal.json")
