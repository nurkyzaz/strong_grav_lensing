#!/usr/bin/env python
"""Roman Data Challenge Rung 1: score the unlabeled test set and write the
submission CSV.

Loads one or more checkpoints from train_cnn_rung1.py (pass several to
ensemble across seeds), runs 8-view dihedral test-time augmentation (the same
label-preserving flips/rotations used in training), averages the sigmoid
probabilities, and writes `ID,<prob_col>`.

    python predict_rung1.py --test_file unlabeled_rung_1.h5 \
        --ckpt rung1_r50_s0.pt rung1_r50_s1.pt rung1_r50_s2.pt \
        --out submission_rung1.csv

CONFIRM before submitting: open view_rung_1_dataset.ipynb and check the exact
submission column name (default here: `prob`) and whether the metric wants a
probability or a hard 0/1 label. Set --prob_col / --hard_label accordingly.
"""
import argparse
import os
import sys

import h5py
import numpy as np
import torch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from train_cnn_paltas import build_model                       # noqa: E402
from train_cnn_rung1 import to_nchw, normalize_stack, autodetect_key, IMAGE_KEYS  # noqa: E402

ID_KEYS = ["ID", "id", "ids", "obj_id", "object_id", "index"]


def dihedral(x, k, flip):
    """One of the 8 dihedral views (matches augment_batch's group)."""
    if flip:
        x = torch.flip(x, dims=[-1])
    if k:
        x = torch.rot90(x, k, dims=[-2, -1])
    return x


@torch.no_grad()
def predict_one(ckpt_path, images, device, batch_size, tta):
    # weights_only=False: these are our own trusted checkpoints, and they carry
    # non-tensor metadata (arch/norm/val_auc); the torch>=2.6 default would reject them.
    ck = torch.load(ckpt_path, map_location=device, weights_only=False)
    model = build_model(ck["arch"], out_dim=1, in_chans=ck["in_chans"]).to(device)
    model.load_state_dict(ck["state_dict"])
    model.eval()
    x = normalize_stack(images, ck["norm"], ck["asinh_a"])
    views = [(k, fl) for fl in (False, True) for k in range(4)] if tta else [(0, False)]
    n = len(x)
    probs = np.zeros(n, dtype="float64")
    for start in range(0, n, batch_size):
        xb = torch.from_numpy(x[start:start + batch_size]).to(device)
        s = torch.zeros(xb.size(0), 1, device=device)
        acc = torch.zeros(xb.size(0), device=device)
        for k, fl in views:
            logit = model(dihedral(xb, k, fl), s).reshape(-1)
            acc += torch.sigmoid(logit)
        probs[start:start + batch_size] = (acc / len(views)).cpu().numpy()
    print(f"[ckpt] {ckpt_path} (val_auc {ck.get('val_auc', float('nan')):.4f}) "
          f"scored {n} with {len(views)} views")
    return probs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--test_file", required=True, help="UNLABELED Rung 1 HDF5")
    ap.add_argument("--ckpt", nargs="+", required=True, help="one or more checkpoints")
    ap.add_argument("--out", default="submission_rung1.csv")
    ap.add_argument("--image_key", default=None)
    ap.add_argument("--id_key", default=None,
                    help="ID column; if omitted, use the row index zero-padded to 8")
    ap.add_argument("--prob_col", default="prob",
                    help="submission value column name (CONFIRM in the notebook)")
    ap.add_argument("--hard_label", action="store_true",
                    help="write 0/1 at --threshold instead of the probability")
    ap.add_argument("--threshold", type=float, default=0.5)
    ap.add_argument("--batch_size", type=int, default=128)
    ap.add_argument("--no_tta", action="store_true")
    ap.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    args = ap.parse_args()

    device = torch.device(args.device)
    with h5py.File(args.test_file, "r") as f:
        ik = args.image_key or autodetect_key(f, "image", IMAGE_KEYS)
        images = to_nchw(f[ik][:])
        if args.id_key and args.id_key in f:
            ids = [f"{int(v):08d}" for v in f[args.id_key][:]]
        else:
            ids = [f"{i:08d}" for i in range(len(images))]
    print(f"[data] {args.test_file}: {ik}={images.shape}, {len(ids)} systems")

    probs = np.mean([predict_one(c, images, device, args.batch_size, not args.no_tta)
                     for c in args.ckpt], axis=0)

    with open(args.out, "w") as fout:
        fout.write(f"ID,{args.prob_col}\n")
        for i, p in zip(ids, probs):
            v = int(p >= args.threshold) if args.hard_label else round(float(p), 6)
            fout.write(f"{i},{v}\n")
    print(f"[done] {len(ids)} rows -> {args.out} "
          f"(mean prob {probs.mean():.3f}, frac>=0.5 {float((probs>=0.5).mean()):.3f})")


if __name__ == "__main__":
    main()
