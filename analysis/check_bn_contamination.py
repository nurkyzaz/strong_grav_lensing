#!/usr/bin/env python
"""Confirm the suspected DA bug: during DA training, target-pool (real) batches
pass through BatchNorm in TRAIN mode, so BN running_mean/running_var drift
toward the real-pool distribution. At benchmark eval the model uses these
CONTAMINATED stats -> the measured 'DA effect' is entangled with a BN-stats
shift (a known DA gotcha; fix = freeze BN or source-only BN, e.g. AdaBN).

Compares BN running stats of the v2 reference vs the DA-v2 checkpoints."""
import os
import sys

import numpy as np
import torch

sys.path.insert(0, os.path.expanduser("~/Desktop/LensFusion"))

EIN = os.path.expanduser("~/Desktop/LensFusion/da_pool_inspection")


def bn_stats(ckpt_path):
    sd = torch.load(ckpt_path, map_location="cpu")["state_dict"]
    means, vars = [], []
    for k, v in sd.items():
        if k.endswith("running_mean"):
            means.append(v.numpy())
        elif k.endswith("running_var"):
            vars.append(v.numpy())
    return np.concatenate(means), np.concatenate(vars)


ck = {
    "v2 (no DA)": "einstein_cnn_paltas_v2.pt",
    "DA-v2 scratch": "einstein_cnn_da2_scratch.pt",
    "DA-v2 finetune": "einstein_cnn_da2_finetune.pt",
}
have = {k: os.path.join(EIN, v) for k, v in ck.items()
        if os.path.exists(os.path.join(EIN, v))}
if "v2 (no DA)" not in have:
    print("need checkpoints locally; run the scp first")
    sys.exit(0)

m0, v0 = bn_stats(have["v2 (no DA)"])
print(f"BN channels compared: {len(m0)}")
for name, p in have.items():
    if name == "v2 (no DA)":
        continue
    m, v = bn_stats(p)
    dm = np.abs(m - m0) / (np.abs(m0) + 1e-6)
    dv = np.abs(v - v0) / (np.abs(v0) + 1e-6)
    print(f"\n{name} vs v2:")
    print(f"  running_mean: median |rel change| {np.median(dm)*100:.1f}%  "
          f"90th pct {np.percentile(dm,90)*100:.1f}%")
    print(f"  running_var:  median |rel change| {np.median(dv)*100:.1f}%  "
          f"90th pct {np.percentile(dv,90)*100:.1f}%")
