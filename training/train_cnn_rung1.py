#!/usr/bin/env python
"""Roman Data Challenge Rung 1: binary classifier for CDM subhalo presence.

Rung 1 is a DIFFERENT task from our Rung 0 theta_E work: instead of regressing
the Einstein radius, we output P(subhalos present) per lens. The organizers
provide a labeled training set + an unlabeled test set (Zenodo
doi:10.5281/zenodo.20249305 / .20249307), so there is NO data generation here
-- no paltas, no mejiro, no romanisim. We train directly on the provided
native-Roman, 3-band (F106/F129/F158) images.

This reuses the backbones and augmentation from train_cnn_paltas.py unchanged
(resnet50 / convnextv2 are the only archs that take >1 input channel). The only
new pieces are:
  * multi-band per-channel normalization (theta_E code was single-band),
  * a binary label read from the challenge HDF5 (key auto-detected; confirm
    with inspect_rung1_h5.py),
  * BCEWithLogits loss on the out_dim=1 logit (no theta clamps, no NLL),
  * ROC-AUC / accuracy model selection (no MAE),
  * a self-made STRATIFIED train/val split (Rung 1 ships one labeled file).

The scale-conditioning scalar the backbones expect is fed as 0 (the challenge
FOV is fixed, so pixel scale is constant and its normalized value is 0 -- the
same degenerate-scale handling train_cnn_paltas.py uses for fixed-FOV data).

Run inspect_rung1_h5.py FIRST to get --image_key / --label_key. Example:
    python train_cnn_rung1.py \
        --train_file roman_data_challenge_rung_1_v_3_0.h5 \
        --image_key lensed --label_key label \
        --arch resnet50 --in_chans 3 --seed 0 --out_ckpt rung1_r50_s0.pt
"""
import argparse
import os
import sys

import h5py
import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from sklearn.metrics import roc_auc_score

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from train_cnn_paltas import build_model, augment_batch  # noqa: E402

IMAGE_KEYS = ["lensed", "images", "image", "data", "cutouts", "x"]
LABEL_KEYS = ["label", "labels", "subhalo", "subhalos", "has_subhalos",
              "substructure", "y", "cdm", "class"]


def autodetect_key(f, want, candidates):
    for k in candidates:
        if k in f:
            return k
    raise KeyError(f"could not find a {want} dataset in {list(f.keys())}; "
                   f"pass --{want}_key explicitly (see inspect_rung1_h5.py)")


def to_nchw(arr):
    """Coerce a challenge image cube to (N, C, H, W) float32."""
    arr = arr.astype("float32")
    if arr.ndim == 3:                       # (N, H, W) single band
        return arr[:, None]
    if arr.ndim == 4 and arr.shape[1] in (1, 3, 4):   # already (N, C, H, W)
        return arr
    if arr.ndim == 4 and arr.shape[-1] in (1, 3, 4):  # (N, H, W, C)
        return np.transpose(arr, (0, 3, 1, 2))
    raise ValueError(f"unexpected image shape {arr.shape}")


def normalize_stack(images, norm, asinh_a):
    """Per-image, PER-CHANNEL normalization for an (N, C, H, W) cube.
    asinh compresses the bright lens centre while keeping faint arc/subhalo
    residuals; then standardize each channel of each image to zero mean/unit
    std so the three Roman bands are on a common footing."""
    if norm == "asinh":
        x = np.arcsinh(images / asinh_a)
    elif norm == "minmax":
        mn = images.min(axis=(2, 3), keepdims=True)
        mx = images.max(axis=(2, 3), keepdims=True)
        return ((images - mn) / (mx - mn + 1e-8)).astype("float32")
    else:
        raise ValueError(f"unknown norm {norm}")
    mn = x.mean(axis=(2, 3), keepdims=True)
    sd = x.std(axis=(2, 3), keepdims=True) + 1e-8
    return ((x - mn) / sd).astype("float32")


class Rung1Dataset(Dataset):
    def __init__(self, images, labels, norm="asinh", asinh_a=1.0):
        self.images = normalize_stack(images, norm, asinh_a)
        self.labels = labels.astype("float32")

    def __len__(self):
        return len(self.images)

    def __getitem__(self, i):
        img = torch.from_numpy(self.images[i])            # (C, H, W)
        s = torch.zeros(1, dtype=torch.float32)           # degenerate scale
        y = torch.tensor(self.labels[i], dtype=torch.float32)
        return img, s, y


def stratified_split(n, labels, val_frac, seed):
    rng = np.random.default_rng(seed)
    idx = np.arange(n)
    val = []
    for c in np.unique(labels):
        ci = idx[labels == c]
        rng.shuffle(ci)
        val.append(ci[:int(round(val_frac * len(ci)))])
    val_idx = np.concatenate(val)
    mask = np.ones(n, dtype=bool)
    mask[val_idx] = False
    return idx[mask], val_idx


@torch.no_grad()
def evaluate(model, loader, device):
    model.eval()
    probs, trues = [], []
    for img, s, y in loader:
        logit = model(img.to(device), s.to(device)).reshape(-1)
        probs.append(torch.sigmoid(logit).cpu().numpy())
        trues.append(y.numpy())
    probs = np.concatenate(probs)
    trues = np.concatenate(trues)
    auc = roc_auc_score(trues, probs) if len(np.unique(trues)) > 1 else float("nan")
    acc = float(((probs >= 0.5).astype("float32") == trues).mean())
    return auc, acc


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--train_file", required=True,
                    help="labeled Rung 1 HDF5 (roman_data_challenge_rung_1_v_3_0.h5)")
    ap.add_argument("--image_key", default=None, help="auto-detected if omitted")
    ap.add_argument("--label_key", default=None, help="auto-detected if omitted")
    ap.add_argument("--val_frac", type=float, default=0.15)
    ap.add_argument("--epochs", type=int, default=40)
    ap.add_argument("--batch_size", type=int, default=64)
    ap.add_argument("--lr", type=float, default=1e-3)
    ap.add_argument("--weight_decay", type=float, default=1e-4)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    ap.add_argument("--out_ckpt", default="rung1_r50_s0.pt")
    ap.add_argument("--arch", choices=["resnet50", "convnextv2"], default="resnet50",
                    help="only timm archs take in_chans>1 (Roman 3-band)")
    ap.add_argument("--in_chans", type=int, default=3)
    ap.add_argument("--norm", choices=["asinh", "minmax"], default="asinh")
    ap.add_argument("--asinh_a", type=float, default=1.0)
    ap.add_argument("--augment", action="store_true", default=True)
    ap.add_argument("--limit", type=int, default=None, help="first N rows (smoke test)")
    args = ap.parse_args()

    torch.manual_seed(args.seed)
    np.random.seed(args.seed)
    device = torch.device(args.device)

    with h5py.File(args.train_file, "r") as f:
        ik = args.image_key or autodetect_key(f, "image", IMAGE_KEYS)
        lk = args.label_key or autodetect_key(f, "label", LABEL_KEYS)
        n_avail = f[ik].shape[0]
        n = n_avail if args.limit is None else min(args.limit, n_avail)
        images = to_nchw(f[ik][:n])
        labels = f[lk][:n].astype("float32")
    print(f"[data] {args.train_file}: {ik}={images.shape} {lk}: "
          f"{int((labels == 1).sum())} pos / {int((labels == 0).sum())} neg")

    tr_idx, va_idx = stratified_split(len(images), labels, args.val_frac, args.seed)
    train_set = Rung1Dataset(images[tr_idx], labels[tr_idx], args.norm, args.asinh_a)
    val_set = Rung1Dataset(images[va_idx], labels[va_idx], args.norm, args.asinh_a)
    train_loader = DataLoader(train_set, batch_size=args.batch_size, shuffle=True,
                              num_workers=2, drop_last=True)
    val_loader = DataLoader(val_set, batch_size=args.batch_size, shuffle=False,
                            num_workers=2)
    print(f"[data] train={len(train_set)} val={len(val_set)} device={device}")

    model = build_model(args.arch, out_dim=1, in_chans=args.in_chans).to(device)
    print(f"[model] arch={args.arch} in_chans={args.in_chans} "
          f"params={sum(p.numel() for p in model.parameters())/1e6:.2f}M | BCE head")

    # class-imbalance-safe: pos_weight = n_neg / n_pos on the TRAIN split
    n_pos = float((labels[tr_idx] == 1).sum())
    n_neg = float((labels[tr_idx] == 0).sum())
    pos_weight = torch.tensor([n_neg / max(n_pos, 1.0)], device=device)
    loss_fn = nn.BCEWithLogitsLoss(pos_weight=pos_weight)
    opt = torch.optim.AdamW(model.parameters(), lr=args.lr,
                            weight_decay=args.weight_decay)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=args.epochs)

    best = -1.0
    for epoch in range(1, args.epochs + 1):
        model.train()
        running = 0.0
        for img, s, y in train_loader:
            if args.augment:
                img = augment_batch(img)   # flips + 90deg rots preserve the label
            img, s, y = img.to(device), s.to(device), y.to(device)
            opt.zero_grad()
            logit = model(img, s).reshape(-1)
            loss = loss_fn(logit, y)
            loss.backward()
            opt.step()
            running += loss.item() * img.size(0)
        sched.step()
        auc, acc = evaluate(model, val_loader, device)
        print(f"epoch {epoch:3d} | train_bce {running/len(train_set):.4f} | "
              f"val_AUC {auc:.4f} | val_acc {acc:.4f}", flush=True)
        if auc > best:
            best = auc
            torch.save({"state_dict": model.state_dict(), "arch": args.arch,
                        "in_chans": args.in_chans, "out_dim": 1,
                        "norm": args.norm, "asinh_a": args.asinh_a,
                        "image_key": ik, "label_key": lk,
                        "val_auc": float(auc), "seed": args.seed,
                        "train_file": args.train_file}, args.out_ckpt)
    print(f"\n[done] best val AUC = {best:.4f} -> {args.out_ckpt}")


if __name__ == "__main__":
    main()
