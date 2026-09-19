#!/usr/bin/env python
"""Roman Data Challenge Rung 1: score the unlabeled set, write the submission.

Loads one or more checkpoints from train_cnn_rung1.py (pass several to ensemble
across seeds), runs 8-view dihedral TTA, averages the sigmoid probabilities, and
writes `ID,<prob_col>` keyed by each lens's `uid`.

The unlabeled HDF5 has the same per-lens group layout as the labeled one, minus
the 'substructure' attr:
    images/strong_lens_<uid>/exposure_<uid>_{F106,F129,F158}

    python predict_rung1.py \
        --test_file roman_data_challenge_rung_1_unlabeled_v_3_0.h5 \
        --ckpt rung1_resnet50_s0.pt rung1_resnet50_s1.pt rung1_resnet50_s2.pt \
        --out submission_rung1.csv

CONFIRM the required submission column name + metric with the challenge
organizers (the view_* notebooks are dataset viewers and don't specify it);
set --prob_col / --hard_label accordingly. Default column: `prob`.
"""
import argparse
import os
import sys

import numpy as np
import torch
from torch.utils.data import DataLoader

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from train_cnn_paltas import build_model                               # noqa: E402
from train_cnn_rung1 import index_dataset, Rung1H5Dataset              # noqa: E402


def dihedral(x, k, flip):
    """One of the 8 dihedral views (matches augment_batch's group)."""
    if flip:
        x = torch.flip(x, dims=[-1])
    if k:
        x = torch.rot90(x, k, dims=[-2, -1])
    return x


@torch.no_grad()
def predict_one(ckpt_path, dataset, loader, device, tta):
    # weights_only=False: our own trusted checkpoints carry non-tensor metadata
    # (arch/norm/val_auc) that the torch>=2.6 default would reject.
    ck = torch.load(ckpt_path, map_location=device, weights_only=False)
    model = build_model(ck["arch"], out_dim=1, in_chans=ck["in_chans"]).to(device)
    model.load_state_dict(ck["state_dict"])
    model.eval()
    dataset.norm, dataset.asinh_a = ck["norm"], ck["asinh_a"]
    dataset.bands = ck.get("bands", dataset.bands)
    # match the checkpoint's residual-imaging preprocessing (Tier 1)
    dataset.input_mode = ck.get("input_mode", "raw")
    dataset.hp_sigma = ck.get("hp_sigma", 4.0)
    dataset.residual_type = ck.get("residual_type", "highpass")
    dataset.arc_lo = ck.get("arc_lo", 0.4)
    dataset.arc_hi = ck.get("arc_hi", 1.6)
    views = [(k, fl) for fl in (False, True) for k in range(4)] if tta else [(0, False)]
    probs = np.zeros(len(dataset), dtype="float64")
    pos = 0
    for img, s, _ in loader:
        img, s = img.to(device), s.to(device)
        acc = torch.zeros(img.size(0), device=device)
        for k, fl in views:
            acc += torch.sigmoid(model(dihedral(img, k, fl), s).reshape(-1))
        b = img.size(0)
        probs[pos:pos + b] = (acc / len(views)).cpu().numpy()
        pos += b
    print(f"[ckpt] {ckpt_path} (val_auc {ck.get('val_auc', float('nan')):.4f}) "
          f"scored {len(dataset)} with {len(views)} views")
    return probs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--test_file", required=True, help="UNLABELED Rung 1 HDF5")
    ap.add_argument("--ckpt", nargs="+", required=True, help="one or more checkpoints")
    ap.add_argument("--out", default="submission_rung1.csv")
    ap.add_argument("--prob_col", default="prob",
                    help="submission value column name (CONFIRM with organizers)")
    ap.add_argument("--hard_label", action="store_true",
                    help="write 0/1 at --threshold instead of the probability")
    ap.add_argument("--threshold", type=float, default=0.5)
    ap.add_argument("--batch_size", type=int, default=128)
    ap.add_argument("--num_workers", type=int, default=4)
    ap.add_argument("--no_tta", action="store_true")
    ap.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    args = ap.parse_args()

    device = torch.device(args.device)
    group_names, uids, _ = index_dataset(args.test_file, with_labels=False)
    print(f"[data] {args.test_file}: {len(uids)} systems")
    # norm/asinh_a get overwritten per-ckpt inside predict_one
    dataset = Rung1H5Dataset(args.test_file, group_names, uids, None,
                             norm="asinh", asinh_a=1.0)
    loader = DataLoader(dataset, batch_size=args.batch_size, shuffle=False,
                        num_workers=args.num_workers)

    probs = np.mean([predict_one(c, dataset, loader, device, not args.no_tta)
                     for c in args.ckpt], axis=0)

    with open(args.out, "w") as fout:
        fout.write(f"ID,{args.prob_col}\n")
        for uid, p in zip(uids, probs):
            v = int(p >= args.threshold) if args.hard_label else round(float(p), 6)
            fout.write(f"{uid},{v}\n")
    print(f"[done] {len(uids)} rows -> {args.out} "
          f"(mean prob {probs.mean():.3f}, frac>=0.5 {float((probs>=0.5).mean()):.3f})")


if __name__ == "__main__":
    main()
