#!/usr/bin/env python
"""R1.2b premise check, step 2: compute POST-DEGRADATION arc SNR (v2 metric,
azimuthal-residual denominator) on the Euclidised pilot, then stratify the
Euclid-model's errors by it. If error concentrates at low Euclidised arc SNR,
the arc-visibility-selection fix (R1.2b) is justified.
Caveat (disclosed): pilot is pathb-recipe (real deflector light) while the
Euclid model trained on euclidised v3 (parametric light) -> absolute errors
inflated; the TREND with arc SNR is the readout.
Usage: euclid_stratified.py <ckpt>
"""
import glob
import os
import sys
import numpy as np
import h5py
import torch
from scipy.ndimage import gaussian_filter
from scipy.stats import spearmanr

sys.path.insert(0, os.path.expanduser("~/einstein_cnn"))
from train_cnn_paltas import normalize_images, build_model

CKPT = os.path.expanduser(sys.argv[1])
SIM = os.path.expanduser("~/einstein_cnn/euclid_sim_pilot.h5")
ARCDIR = os.path.expanduser("~/paltas_arcs_seed111_euclid")

files = sorted(glob.glob(os.path.join(ARCDIR, "image_*.npy")))
with h5py.File(SIM, "r") as f:
    sim = f["lensed"][:].astype("float32")
    theta = f["theta_E"][:].astype("float32")
assert len(files) == len(sim)

n = sim.shape[1]
c = n // 2
yy, xx = np.mgrid[0:n, 0:n]
rr = np.hypot(yy - c, xx - c)
rbin = rr.astype(int)

snrs = []
for fn, comp in zip(files, sim):
    arc = np.load(fn).astype("float64")
    arc_s = gaussian_filter(arc, 1.5)
    pk = arc_s.max()
    if pk <= 0:
        snrs.append(0.0)
        continue
    fp = arc_s > 0.5 * pk
    rest_s = gaussian_filter(comp.astype("float64") - arc, 1.5)
    prof = np.zeros(rbin.max() + 1)
    for k in range(rbin.max() + 1):
        m = rbin == k
        if m.any():
            prof[k] = np.median(rest_s[m])
    resid = rest_s - prof[rbin]
    ann = (rr >= rr[fp].min() - 3) & (rr <= rr[fp].max() + 3) & (~fp)
    loc = resid[ann]
    mad = np.median(np.abs(loc - np.median(loc))) * 1.4826
    snrs.append(float(arc_s[fp].max() / mad) if mad > 0 else 0.0)
snrs = np.array(snrs)

x = normalize_images(sim, "asinh", 1.0)
ck = torch.load(CKPT, map_location="cpu")
state = ck.get("model_state", ck.get("state_dict", ck))
model = build_model(ck.get("arch", "inceptionnext"), 2)
model.load_state_dict(state)
model.eval()
scale = (np.arcsinh(sim.max(axis=(1, 2))) - ck.get("scale_mean", 0.05039)) / ck.get("scale_std", 1.0)
preds = []
with torch.no_grad():
    for i in range(0, len(x), 64):
        xb = torch.from_numpy(x[i:i + 64]).unsqueeze(1).float()
        sb = torch.from_numpy(np.asarray(scale[i:i + 64], dtype="float32")).unsqueeze(1)
        preds.append(model(xb, sb)[:, 0].numpy())
pred = np.concatenate(preds)
frac = (pred - theta) / theta

print("POST-DEGRADATION arc SNR: median %.2f; fraction > 0.7: %.2f (native was 0.58)"
      % (np.median(snrs), (snrs > 0.7).mean()))
qs = np.quantile(snrs, [0.25, 0.5, 0.75])
bins = [(-1, qs[0], "Q1 (lowest SNR)"), (qs[0], qs[1], "Q2"),
        (qs[1], qs[2], "Q3"), (qs[2], 1e9, "Q4 (highest SNR)")]
for lo, hi, name in bins:
    m = (snrs > lo) & (snrs <= hi)
    print("%-18s N=%3d  MAE %.3f\"  median frac %+.1f%%  |frac|>15%%: %.0f%%"
          % (name, m.sum(), np.abs(pred - theta)[m].mean(),
             100 * np.median(frac[m]), 100 * (np.abs(frac[m]) > 0.15).mean()))
rho, p = spearmanr(snrs, np.abs(frac))
print("Spearman rho(euclid arc SNR, |frac err|) = %+.2f (p=%.1e)" % (rho, p))
np.save(os.path.expanduser("~/einstein_cnn/arc_snr_euclid_v7.npy"), snrs)
