#!/usr/bin/env python
"""Rung 1 data sanity: is there ANY class-discriminative signal in the pixels,
and are images/labels aligned? Uses only h5py/numpy/sklearn (no torch), so it
runs on the login node. Builds simple per-band features (moments + gradient
energy + a central-vs-arc contrast) for N lenses and checks whether a plain
logistic regression separates substructure True/False on a held-out split.

If even this gets AUC > ~0.55, signal exists and the CNN setup is the problem.
If it's ~0.5, the substructure signal is genuinely subtle at the pixel level.

    python rung1_sanity.py <labeled.h5> --n 2000
"""
import argparse
import h5py
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import cross_val_score

BANDS = ["F106", "F129", "F158"]
TRUE = {"True", "true", "1", "1.0", "TRUE"}


def attr0(g, name):
    v = g.attrs[name]
    v = v[0] if np.ndim(v) > 0 else v
    return v.decode() if isinstance(v, bytes) else v


def feats(img):
    """img: (C,H,W) -> feature vector."""
    f = []
    for c in range(img.shape[0]):
        a = img[c]
        gx = np.diff(a, axis=0); gy = np.diff(a, axis=1)
        grad = float(np.mean(gx**2) + np.mean(gy**2))     # high-freq energy
        cen = a[a.shape[0]//2-8:a.shape[0]//2+8, a.shape[1]//2-8:a.shape[1]//2+8]
        f += [float(a.mean()), float(a.std()), float(a.max()),
              float(np.percentile(a, 99)), grad, float(cen.mean())]
    return f


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("h5_path")
    ap.add_argument("--n", type=int, default=2000)
    args = ap.parse_args()

    X, y = [], []
    with h5py.File(args.h5_path, "r") as h:
        g = h["images"]
        names = list(g.keys())[:args.n]
        for nm in names:
            grp = g[nm]
            uid = attr0(grp, "uid")
            img = np.stack([grp[f"exposure_{uid}_{b}"][:] for b in BANDS]).astype("float32")
            X.append(feats(img))
            y.append(1 if str(attr0(grp, "substructure")) in TRUE else 0)
    X = np.array(X); y = np.array(y)
    print(f"n={len(y)}  pos={int(y.sum())} neg={int((y==0).sum())}  feat_dim={X.shape[1]}")

    # are the two classes separable at all by simple features?
    Xs = StandardScaler().fit_transform(X)
    clf = LogisticRegression(max_iter=2000, C=1.0)
    auc = cross_val_score(clf, Xs, y, cv=5, scoring="roc_auc")
    acc = cross_val_score(clf, Xs, y, cv=5, scoring="accuracy")
    print(f"logistic-regression 5-fold AUC = {auc.mean():.4f} +/- {auc.std():.4f}")
    print(f"logistic-regression 5-fold ACC = {acc.mean():.4f}")

    # per-class feature means (are they different at all?)
    print("feature class-mean |diff|/std (top 6):")
    d = np.abs(X[y == 1].mean(0) - X[y == 0].mean(0)) / (X.std(0) + 1e-9)
    order = np.argsort(d)[::-1][:6]
    print("  ", np.round(d[order], 3).tolist())


if __name__ == "__main__":
    main()
