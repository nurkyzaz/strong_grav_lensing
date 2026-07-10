#!/usr/bin/env python
"""P7 STOP-rule diagnostic (plan Q3, pulled forward): is the quick-train model's
error concentrated in the invisible-arc images?

Runs the quick-train checkpoint on pilot v7 (200 final-recipe images, per-image
arc SNR already computed in arc_snr_v7.npy) and reports MAE / frac error
stratified by arc-SNR bin. If the visible-arc bins show v3-like error while the
invisible bins are catastrophic, the aggregate sim-val MAE is dominated by
unlearnable (arc-buried) images — which grade-A benchmark lenses are not.
Uses the same normalization path as training (imports from train_cnn_paltas).
"""
import os
import sys
import numpy as np
import h5py
import torch

sys.path.insert(0, os.path.expanduser("~/einstein_cnn"))
from train_cnn_paltas import normalize_images, build_model

CKPT = os.path.expanduser(sys.argv[1] if len(sys.argv) > 1
                          else "~/einstein_cnn/einstein_cnn_pathb_v2_quicktrain.pt")
SIM = os.path.expanduser("~/einstein_cnn/pathb_pilot_v7.h5")
SNR = os.path.expanduser("~/cosmos_acs/tiles/arc_snr_v7.npy")
SCALE_MEAN, SCALE_STD = 0.05039, 1.0  # from the training log

with h5py.File(SIM, "r") as f:
    imgs = f["lensed"][:].astype("float32")
    theta = f["theta_E"][:].astype("float32")
snr = np.load(SNR)
assert len(imgs) == len(theta) == len(snr)

x = normalize_images(imgs, "asinh", 1.0)
scale = (np.arcsinh(imgs.max(axis=(1, 2))) - SCALE_MEAN) / SCALE_STD

ck = torch.load(CKPT, map_location="cpu")
state = ck.get("model_state", ck.get("state_dict", ck))
arch = ck.get("arch", "inceptionnext")
out_dim = 2  # NLL head (mu, logvar)
model = build_model(arch, out_dim)
model.load_state_dict(state)
model.eval()

preds = []
with torch.no_grad():
    for i in range(0, len(x), 64):
        xb = torch.from_numpy(x[i:i + 64]).unsqueeze(1).float()
        sb = torch.from_numpy(scale[i:i + 64]).float().unsqueeze(1)
        out = model(xb, sb)
        preds.append(out[:, 0].numpy())
pred = np.concatenate(preds)

err = pred - theta
frac = err / theta
bins = [(0.0, 0.3, "invisible (<0.3)"), (0.3, 0.7, "marginal (0.3-0.7)"),
        (0.7, 1.83, "faint-visible (0.7-1.8)"), (1.83, np.inf, "clear (>1.8)")]
print("quick-train ckpt on pilot v7 (N=200), stratified by arc SNR:")
print("overall: MAE %.3f\"  median frac %+.1f%%  |frac|>15%%: %.0f%%"
      % (np.abs(err).mean(), 100 * np.median(frac), 100 * (np.abs(frac) > 0.15).mean()))
for lo, hi, name in bins:
    m = (snr >= lo) & (snr < hi)
    if m.sum() == 0:
        continue
    print("%-24s N=%3d  MAE %.3f\"  median frac %+.1f%%  |frac|>15%%: %.0f%%"
          % (name, m.sum(), np.abs(err[m]).mean(), 100 * np.median(frac[m]),
             100 * (np.abs(frac[m]) > 0.15).mean()))
# correlation
from scipy.stats import spearmanr
rho, p = spearmanr(snr, np.abs(frac))
print("Spearman rho(arc SNR, |frac err|) = %+.2f (p=%.1e)" % (rho, p))
