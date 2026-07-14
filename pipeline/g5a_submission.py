#!/usr/bin/env python
"""G5 Path A OFFICIAL SUBMISSION RUN (Nurkyz go 2026-07-14): the 12 trained
members on the UNLABELED Rung 0 test set — the exactly-once model contact.
Outputs grader-format CSVs (ID, theta_E, theta_E_sigma):
  rung0_submission_3band_all6.csv  (PRIMARY)
  rung0_submission_f106_all6.csv   (secondary)
sigma is pre-scaled by the FROZEN rmsz factors measured on challenge-val
(3band all6 x0.98, f106 all6 x1.11) so chi2(val)=1 by construction — their
TDLMC Goodness ideal. ID = bare uid (their grader strips any strong_lens_
prefix and compares as int). Nurkyz sends the email."""
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
SCALE = {"3band": 0.98, "f106": 1.11}   # frozen rmsz from the val harvest
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


for var, ic in (("3band", 3), ("f106", 1)):
    with h5py.File(os.path.join(EC, "eval_rung0_unlabeled_%s.h5" % var), "r") as f:
        x = f["lensed"][:]
        names = [n.decode() if isinstance(n, bytes) else str(n) for n in f["names"][:]]
    x = normalize_images(x.astype("float32"), "asinh", 1.0)
    xt = torch.from_numpy(x)
    if xt.ndim == 3:
        xt = xt.unsqueeze(1)
    mems = []
    for short, arch in ARCHS.items():
        for sd in (1, 2, 3):
            ck = torch.load(os.path.join(EC, "rung0_%s_%s_s%d.pt" % (var, short, sd)),
                            map_location="cpu")
            model = build_model(arch, ck["out_dim"], in_chans=ic).to(DEV)
            model.load_state_dict(ck["state_dict"])
            model.eval()
            mems.append(tta_predict(model, xt))
            print("  %s %s_s%d done" % (var, short, sd), flush=True)
    M = np.array([m[0] for m in mems])
    S = np.array([m[1] for m in mems])
    mu = M.mean(0)
    sig = np.sqrt(np.maximum((S ** 2 + M ** 2).mean(0) - mu ** 2, 1e-12)) * SCALE[var]
    fn = os.path.join(OUT, "rung0_submission_%s_all6.csv" % var)
    with open(fn, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["ID", "theta_E", "theta_E_sigma"])
        for i, n in enumerate(names):
            w.writerow([n, "%.5f" % mu[i], "%.5f" % sig[i]])
    print("wrote %s  N=%d  theta med %.3f  sigma med %.3f (frozen scale x%.2f)"
          % (fn, len(names), np.median(mu), np.median(sig), SCALE[var]))
print("G5A_SUBMISSION_DONE")
