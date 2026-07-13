#!/usr/bin/env python
"""R0.2 (MASTER_PLAN D3): sigma recalibration fitted on SIM-VAL ONLY.

Predicts (mu, sigma) on the held-out sim-val split, then fits a single scale
factor s (sigma -> s*sigma, Platt-style; cf. LEMON's per-parameter scaling)
such that the 68% empirical coverage matches nominal. Reports raw and
recalibrated 68%/95% coverage and rho(sigma, |err|). The benchmark is NOT
touched here; s is frozen before any real-lens evaluation.
Usage: recalibrate_sigma.py <ckpt> [val_h5]
"""
import os
import sys
import numpy as np
import h5py
import torch

sys.path.insert(0, os.path.expanduser("~/einstein_cnn"))
from train_cnn_paltas import normalize_images, build_model

CKPT = os.path.expanduser(sys.argv[1])
VAL = os.path.expanduser(sys.argv[2] if len(sys.argv) > 2
                         else "~/einstein_cnn/val_hybrid_5k_pathb_v2.h5")
SCALE_MEAN, SCALE_STD = 0.05039, 1.0

with h5py.File(VAL, "r") as f:
    imgs = f["lensed"][:].astype("float32")
    theta = f["theta_E"][:].astype("float32")

x = normalize_images(imgs, "asinh", 1.0)
scale = (np.arcsinh(imgs.max(axis=(1, 2))) - SCALE_MEAN) / SCALE_STD

ck = torch.load(CKPT, map_location="cpu")
state = ck.get("model_state", ck.get("state_dict", ck))
arch = ck.get("arch", "inceptionnext")
model = build_model(arch, 2)
model.load_state_dict(state)
model.eval()

mus, sigs = [], []
with torch.no_grad():
    for i in range(0, len(x), 128):
        xb = torch.from_numpy(x[i:i + 128]).unsqueeze(1).float()
        sb = torch.from_numpy(scale[i:i + 128]).float().unsqueeze(1)
        out = model(xb, sb)
        mus.append(out[:, 0].numpy())
        sigs.append(np.exp(0.5 * out[:, 1].numpy()))
mu = np.concatenate(mus)
sig = np.concatenate(sigs)
err = mu - theta
z = np.abs(err) / sig

from scipy.stats import spearmanr
rho, _ = spearmanr(sig, np.abs(err))


def coverage(s):
    return (z <= 1.0 * s).mean(), (z <= 1.96 * s).mean()


# fit s so that 68% coverage is nominal: s = 68th percentile of z
s_fit = float(np.percentile(z, 68.27))
c68_raw, c95_raw = coverage(1.0)
c68_rec, c95_rec = coverage(s_fit)

print("ckpt: %s  arch=%s  N_val=%d" % (os.path.basename(CKPT), arch, len(mu)))
print("val MAE %.4f\"  median frac %+.2f%%" % (np.abs(err).mean(),
      100 * np.median(err / theta)))
print("rho(sigma, |err|) = %+.2f" % rho)
print("RAW coverage:          68%%: %.1f%%   95%%: %.1f%%" % (100 * c68_raw, 100 * c95_raw))
print("scale factor s (sim-val fit, 68%% match): %.3f" % s_fit)
print("RECALIBRATED coverage: 68%%: %.1f%%   95%%: %.1f%%" % (100 * c68_rec, 100 * c95_rec))
print("FROZEN: apply sigma_recal = %.3f * sigma at real-lens evaluation" % s_fit)
