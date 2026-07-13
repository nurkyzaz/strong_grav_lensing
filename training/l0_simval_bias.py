#!/usr/bin/env python
"""L0 item 2b: sim-val bias forensics for the euclid_sel models (B4).

Runs the two eval-#14 checkpoints on the SIM-VAL split (val_euclid_sel_5k.h5,
which carries per-image arc_snr/arc_extent from the patched merge) and
stratifies signed bias by arc SNR and theta_E. Sim-val inference is allowed
freely (NOT a benchmark evaluation; running count unaffected).

NOTE: sim-val is itself selection-filtered (arc_snr>0.7), so this measures the
WITHIN-SELECTION bias gradient - the selection-survivor signature is a positive
bias that grows toward the low-SNR edge. The below-floor regime is probed on
the real benchmark by l0_tail_forensics.py instead.

Run via l0_simval_bias.sbatch (GPU) - or CPU (slow) with --cpu.
"""
import os
import sys
import numpy as np
import h5py
import torch
from scipy.stats import spearmanr

sys.path.insert(0, os.path.expanduser("~/einstein_cnn"))
from train_cnn_paltas import normalize_images, build_model

VAL = os.path.expanduser("~/einstein_cnn/val_euclid_sel_5k.h5")
CKPTS = [os.path.expanduser("~/einstein_cnn/einstein_cnn_euclid_sel_inceptionnext.pt"),
         os.path.expanduser("~/einstein_cnn/einstein_cnn_euclid_sel_resnet.pt")]
DEV = "cpu" if "--cpu" in sys.argv else ("cuda" if torch.cuda.is_available() else "cpu")

with h5py.File(VAL, "r") as f:
    key = "lensed" if "lensed" in f else "images"
    imgs = f[key][:].astype("float32")
    theta = f["theta_E"][:].astype("float64")
    snr = f["arc_snr"][:].astype("float64") if "arc_snr" in f else None
    ext = f["arc_extent"][:].astype("float64") if "arc_extent" in f else None
if imgs.ndim == 4:
    imgs = imgs[:, 0]
assert snr is not None, "val file lacks arc_snr - check merge provenance"
print("val: %d images, arc_snr median %.2f [%.2f, %.2f]"
      % (len(imgs), np.median(snr), np.percentile(snr, 16), np.percentile(snr, 84)))

x = normalize_images(imgs, "asinh", 1.0)
all_preds = {}
for ckpt in CKPTS:
    ck = torch.load(ckpt, map_location=DEV)
    state = ck.get("model_state", ck.get("state_dict", ck))
    arch = ck.get("arch", "resnet")
    net = build_model(arch, int(ck.get("out_dim", 2))).to(DEV)
    net.load_state_dict(state)
    net.eval()
    scale = (np.arcsinh(imgs.max(axis=(1, 2))) - ck["scale_mean"]) / ck["scale_std"]
    preds = []
    with torch.no_grad():
        for i in range(0, len(x), 256):
            xb = torch.from_numpy(x[i:i + 256]).unsqueeze(1).float().to(DEV)
            sb = torch.from_numpy(scale[i:i + 256].astype("float32")).unsqueeze(1).to(DEV)
            preds.append(net(xb, sb)[:, 0].cpu().numpy())
    all_preds[arch] = np.concatenate(preds).astype("float64")
    print("done: %s" % arch)
all_preds["ensemble"] = 0.5 * (all_preds[list(all_preds)[0]] + all_preds[list(all_preds)[1]])

print("\nB4 - WITHIN-SELECTION bias gradient on sim-val (positive bias rising toward")
print("the low-SNR edge = selection-survivor signature):")
edges = [(0.7, 1.0, "0.7-1.0 (floor edge)"), (1.0, 2.0, "1.0-2.0"),
         (2.0, 4.0, "2.0-4.0"), (4.0, np.inf, ">4.0 (bright)")]
for name, pred in all_preds.items():
    frac = (pred - theta) / theta
    print("  %s: overall bias %+.2f%%  MAE %.3f\"" %
          (name, 100 * np.median(frac), np.abs(pred - theta).mean()))
    for lo, hi, tag in edges:
        m = (snr >= lo) & (snr < hi)
        if m.sum() < 20:
            continue
        print("    snr %-18s N=%5d  median frac %+5.1f%%  fail %4.1f%%"
              % (tag, m.sum(), 100 * np.median(frac[m]),
                 100 * (np.abs(frac[m]) > 0.15).mean()))
    rho, p = spearmanr(snr, frac)
    print("    Spearman rho(arc_snr, SIGNED frac) = %+.2f (p=%.1e)" % (rho, p))
    for lo, hi in [(0.45, 0.9), (0.9, 1.2), (1.2, 1.5), (1.5, 2.3)]:
        m = (theta >= lo) & (theta < hi)
        print("    theta [%0.2f,%0.2f): N=%5d  median frac %+5.1f%%"
              % (lo, hi, m.sum(), 100 * np.median(frac[m])))

out = os.path.expanduser("~/einstein_cnn/l0_simval_bias.npz")
np.savez(out, theta=theta, snr=snr,
         **{("pred_" + k): v for k, v in all_preds.items()})
print("\nsaved %s" % out)
