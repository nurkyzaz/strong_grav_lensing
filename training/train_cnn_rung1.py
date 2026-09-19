#!/usr/bin/env python
"""Roman Data Challenge Rung 1: binary classifier for CDM subhalo presence.

Rung 1 is a DIFFERENT task from our Rung 0 theta_E work: instead of regressing
the Einstein radius, we output P(subhalos present) per lens. The organizers
provide a labeled training set + an unlabeled test set (Zenodo
doi:10.5281/zenodo.20249305 / .20249307), so there is NO data generation here.

The challenge HDF5 (confirmed from view_rung_1_dataset.ipynb) is a per-lens
GROUP hierarchy, not a flat cube:

    images/strong_lens_<uid>/            attrs: substructure, uid, theta_e, ...
        exposure_<uid>_F106  (91,91) float MJy/sr
        exposure_<uid>_F129
        exposure_<uid>_F158

  label = attrs['substructure'][0] ('True'/'False');  id = attrs['uid'][0].

This reuses the resnet50 / convnextv2 timm backbones + augmentation from
train_cnn_paltas.py unchanged (they take in_chans=3 and any HxW). New here:
  * a lazy group Dataset (labels/uids read up front, the 3 exposures stacked
    on demand -> no 10 GB preload; workers each open their own h5 handle),
  * per-channel asinh+standardize normalization,
  * BCE-with-logits (pos_weight) on the out_dim=1 logit,
  * ROC-AUC model selection, stratified train/val split.

The backbones expect a scale scalar; we feed 0 (fixed 10.01" FOV -> constant
pixel scale, same degenerate-scale handling as train_cnn_paltas.py).

    python train_cnn_rung1.py \
        --train_file roman_data_challenge_rung_1_v_3_0.h5 \
        --arch resnet50 --seed 0 --out_ckpt rung1_resnet50_s0.pt
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

IMAGES_GROUP = "images"
BANDS = ["F106", "F129", "F158"]
LABEL_ATTR = "substructure"
UID_ATTR = "uid"
TRUE_STRINGS = {"True", "true", "1", "1.0", "TRUE"}


def attr0(group, name, default=None):
    """mejiro stores each attr as [value, description]; return the value."""
    if name not in group.attrs:
        return default
    v = group.attrs[name]
    v = v[0] if np.ndim(v) > 0 else v
    if isinstance(v, bytes):
        v = v.decode()
    return v


def index_dataset(h5_path, with_labels=True, limit=None, label_attr=LABEL_ATTR):
    """One pass over images/* reading only attrs: returns (group_names, uids,
    labels|None). label_attr='substructure' -> binary True/False; any other attr
    (e.g. 'theta_e') -> median-split binary, used for DIAGNOSTICS (verify the
    whole pipeline can learn a label we know is visible in the image)."""
    group_names, uids, vals = [], [], []
    with h5py.File(h5_path, "r") as f:
        g = f[IMAGES_GROUP]
        names = list(g.keys())
        if limit is not None:
            names = names[:limit]
        for nm in names:
            grp = g[nm]
            group_names.append(nm)
            uids.append(str(attr0(grp, UID_ATTR)))
            if with_labels:
                if label_attr == LABEL_ATTR:
                    vals.append(1.0 if str(attr0(grp, LABEL_ATTR)) in TRUE_STRINGS
                                else 0.0)
                else:
                    vals.append(float(attr0(grp, label_attr)))
    if not with_labels:
        return group_names, uids, None
    labels = np.asarray(vals, dtype="float32")
    if label_attr != LABEL_ATTR:               # numeric attr -> median split
        labels = (labels > np.median(labels)).astype("float32")
    return group_names, uids, labels


def standardize(x):
    """(C,H,W) -> per-channel zero-mean/unit-std float32 (no asinh; for the
    ~zero-mean bipolar residual channels)."""
    mn = x.mean(axis=(1, 2), keepdims=True)
    sd = x.std(axis=(1, 2), keepdims=True) + 1e-8
    return ((x - mn) / sd).astype("float32")


def normalize_one(img, norm, asinh_a):
    """(C,H,W) -> per-channel normalized float32 (raw bands)."""
    if norm == "asinh":
        return standardize(np.arcsinh(img / asinh_a))
    if norm == "minmax":
        mn = img.min(axis=(1, 2), keepdims=True)
        mx = img.max(axis=(1, 2), keepdims=True)
        return ((img - mn) / (mx - mn + 1e-8)).astype("float32")
    raise ValueError(f"unknown norm {norm}")


def _gauss_kernel(sigma):
    r = max(1, int(round(3 * sigma)))
    x = np.arange(-r, r + 1, dtype="float32")
    k = np.exp(-(x ** 2) / (2.0 * sigma * sigma))
    return (k / k.sum()).astype("float32")


def gaussian_blur(img, sigma):
    """Separable Gaussian blur of an (C,H,W) stack, reflect-padded. Pure numpy
    (no scipy dependency) — cheap at 91x91."""
    k = _gauss_kernel(sigma)
    r = len(k) // 2
    p = np.pad(img, ((0, 0), (r, r), (0, 0)), mode="reflect")
    out = sum(k[j] * p[:, j:j + img.shape[1], :] for j in range(len(k)))
    p = np.pad(out, ((0, 0), (0, 0), (r, r)), mode="reflect")
    out = sum(k[j] * p[:, :, j:j + img.shape[2]] for j in range(len(k)))
    return out.astype("float32")


def highpass(img, sigma):
    """Residual = raw - smooth. Removes the extended deflector light + smooth
    arc envelope, leaving the small-scale structure where subhalo perturbations
    live. (C,H,W) -> (C,H,W)."""
    return (img - gaussian_blur(img, sigma)).astype("float32")


_RADIUS_CACHE = {}


def _radius_index(H, W):
    key = (H, W)
    if key not in _RADIUS_CACHE:
        yy, xx = np.mgrid[0:H, 0:W]
        cy, cx = (H - 1) / 2.0, (W - 1) / 2.0
        _RADIUS_CACHE[key] = np.round(np.sqrt((yy - cy) ** 2 +
                                              (xx - cx) ** 2)).astype(np.int64)
    return _RADIUS_CACHE[key]


def radial_residual(img):
    """(C,H,W) -> img minus its per-channel azimuthally-averaged radial profile.
    A fit-free, TARGETED deflector removal: the centered ~radially-symmetric lens
    galaxy is captured by the radial profile and subtracted, while the
    azimuthally-localized arc (where subhalos act) survives. Contrast highpass(),
    which removes all smooth flux and amplifies noise."""
    C, H, W = img.shape
    r = _radius_index(H, W)
    rflat = r.ravel()
    nb = int(rflat.max()) + 1
    counts = np.maximum(np.bincount(rflat, minlength=nb), 1).astype("float32")
    out = np.empty_like(img)
    for c in range(C):
        prof = (np.bincount(rflat, weights=img[c].ravel(),
                            minlength=nb) / counts).astype("float32")
        out[c] = img[c] - prof[r]
    return out.astype("float32")


def residual_of(img, residual_type, hp_sigma):
    return radial_residual(img) if residual_type == "radial" else highpass(img, hp_sigma)


class Rung1H5Dataset(Dataset):
    """Lazy per-lens reader. group_names/uids/labels are precomputed subsets;
    the h5 file is (re)opened inside each worker on first access so DataLoader
    multiprocessing is safe (never hold an open handle across a fork)."""

    def __init__(self, h5_path, group_names, uids, labels, norm, asinh_a,
                 input_mode="raw", hp_sigma=4.0, residual_type="highpass",
                 bands=BANDS):
        self.h5_path = h5_path
        self.group_names = group_names
        self.uids = uids
        self.labels = labels  # np array or None (predict)
        self.norm, self.asinh_a, self.bands = norm, asinh_a, bands
        self.input_mode = input_mode          # raw | residual | stack
        self.hp_sigma = hp_sigma
        self.residual_type = residual_type    # highpass | radial
        self._f = None

    def _file(self):
        if self._f is None:
            self._f = h5py.File(self.h5_path, "r")
        return self._f

    def __len__(self):
        return len(self.group_names)

    def read_image(self, i):
        grp = self._file()[IMAGES_GROUP][self.group_names[i]]
        uid = self.uids[i]
        img = np.stack([grp[f"exposure_{uid}_{b}"][:] for b in self.bands]
                       ).astype("float32")          # (C,H,W) raw MJy/sr
        if self.input_mode == "raw":
            return normalize_one(img, self.norm, self.asinh_a)
        res = standardize(residual_of(img, self.residual_type, self.hp_sigma))
        if self.input_mode == "residual":
            return res
        if self.input_mode == "stack":                    # raw(3) + residual(3)
            return np.concatenate([normalize_one(img, self.norm, self.asinh_a),
                                   res], axis=0)
        raise ValueError(f"unknown input_mode {self.input_mode}")

    @staticmethod
    def n_channels(input_mode, n_bands=len(BANDS)):
        return n_bands * (2 if input_mode == "stack" else 1)

    def __getitem__(self, i):
        img = torch.from_numpy(self.read_image(i))
        s = torch.zeros(1, dtype=torch.float32)      # degenerate fixed-FOV scale
        y = torch.tensor(0.0 if self.labels is None else self.labels[i],
                         dtype=torch.float32)
        return img, s, y


def stratified_split(labels, val_frac, seed):
    rng = np.random.default_rng(seed)
    idx = np.arange(len(labels))
    val = []
    for c in np.unique(labels):
        ci = idx[labels == c]
        rng.shuffle(ci)
        val.append(ci[:int(round(val_frac * len(ci)))])
    val_idx = np.concatenate(val)
    mask = np.ones(len(labels), dtype=bool)
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


def subset(group_names, uids, labels, idx):
    return ([group_names[i] for i in idx], [uids[i] for i in idx], labels[idx])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--train_file", required=True,
                    help="labeled Rung 1 HDF5 (roman_data_challenge_rung_1_v_3_0.h5)")
    ap.add_argument("--val_frac", type=float, default=0.15)
    ap.add_argument("--epochs", type=int, default=40)
    ap.add_argument("--batch_size", type=int, default=64)
    ap.add_argument("--lr", type=float, default=1e-3)
    ap.add_argument("--weight_decay", type=float, default=1e-4)
    ap.add_argument("--num_workers", type=int, default=4)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    ap.add_argument("--out_ckpt", default="rung1_resnet50_s0.pt")
    ap.add_argument("--arch", choices=["resnet50", "convnextv2"], default="resnet50",
                    help="only timm archs take in_chans>1 (Roman 3-band)")
    ap.add_argument("--norm", choices=["asinh", "minmax"], default="asinh")
    ap.add_argument("--asinh_a", type=float, default=1.0)
    ap.add_argument("--input_mode", choices=["raw", "residual", "stack"],
                    default="raw",
                    help="raw bands (3ch); residual = high-pass only (3ch); "
                         "stack = raw+residual (6ch) [Tier-1 residual imaging]")
    ap.add_argument("--hp_sigma", type=float, default=4.0,
                    help="Gaussian sigma (px) for the high-pass residual")
    ap.add_argument("--residual_type", choices=["highpass", "radial"],
                    default="highpass",
                    help="how residual/stack channels remove the smooth part: "
                         "highpass (Gaussian) or radial (subtract azimuthal "
                         "profile -> targeted deflector removal) [Phase 1a]")
    ap.add_argument("--augment", dest="augment", action="store_true", default=True)
    ap.add_argument("--no_augment", dest="augment", action="store_false",
                    help="disable flip/rot augmentation (e.g. for overfit sanity tests)")
    ap.add_argument("--limit", type=int, default=None, help="first N lenses (smoke test)")
    ap.add_argument("--label_attr", default="substructure",
                    help="DIAGNOSTIC: label from another attr via median split "
                         "(e.g. theta_e) to verify the pipeline can learn a "
                         "known-visible target; default = the real substructure label")
    args = ap.parse_args()

    torch.manual_seed(args.seed)
    np.random.seed(args.seed)
    device = torch.device(args.device)

    group_names, uids, labels = index_dataset(args.train_file, with_labels=True,
                                              limit=args.limit,
                                              label_attr=args.label_attr)
    print(f"[data] {args.train_file}: {len(labels)} lenses | label='{args.label_attr}' "
          f"| {int((labels == 1).sum())} pos / {int((labels == 0).sum())} neg")

    tr_idx, va_idx = stratified_split(labels, args.val_frac, args.seed)
    tr = subset(group_names, uids, labels, tr_idx)
    va = subset(group_names, uids, labels, va_idx)
    train_set = Rung1H5Dataset(args.train_file, *tr, args.norm, args.asinh_a,
                               args.input_mode, args.hp_sigma, args.residual_type)
    val_set = Rung1H5Dataset(args.train_file, *va, args.norm, args.asinh_a,
                             args.input_mode, args.hp_sigma, args.residual_type)
    train_loader = DataLoader(train_set, batch_size=args.batch_size, shuffle=True,
                              num_workers=args.num_workers, drop_last=True,
                              persistent_workers=args.num_workers > 0)
    val_loader = DataLoader(val_set, batch_size=args.batch_size, shuffle=False,
                            num_workers=args.num_workers,
                            persistent_workers=args.num_workers > 0)
    print(f"[data] train={len(train_set)} val={len(val_set)} device={device}")

    in_chans = Rung1H5Dataset.n_channels(args.input_mode)
    model = build_model(args.arch, out_dim=1, in_chans=in_chans).to(device)
    print(f"[model] arch={args.arch} input_mode={args.input_mode} "
          f"in_chans={in_chans} hp_sigma={args.hp_sigma} "
          f"params={sum(p.numel() for p in model.parameters())/1e6:.2f}M | BCE head")

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
            loss = loss_fn(model(img, s).reshape(-1), y)
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
                        "in_chans": in_chans, "out_dim": 1,
                        "norm": args.norm, "asinh_a": args.asinh_a,
                        "input_mode": args.input_mode, "hp_sigma": args.hp_sigma,
                        "residual_type": args.residual_type,
                        "bands": BANDS, "val_auc": float(auc), "seed": args.seed,
                        "train_file": args.train_file}, args.out_ckpt)
    print(f"\n[done] best val AUC = {best:.4f} -> {args.out_ckpt}")


if __name__ == "__main__":
    main()
