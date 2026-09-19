#!/usr/bin/env python
"""Can the PROVIDED per-system parameters (theta_e, sigma_v, mu, snr, z's, ...)
predict substructure yes/no — WITHOUT the image? If a logistic regression on the
metadata scores AUC ~0.5, the parameters carry no label information (substructure
was assigned independently), so feeding them to the CNN cannot help. If it scores
>0.5, there IS exploitable signal (or a leak) and we should add them as inputs.
"""
import sys
import h5py
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import cross_val_score

H5 = sys.argv[1]
N = int(sys.argv[2]) if len(sys.argv) > 2 else 3000
SYS = ["theta_e", "sigma_v", "main_halo_mass", "mu", "z_lens", "z_source"]
EXP = ["snr", "lens_magnitude", "source_magnitude", "lensed_source_magnitude"]
BANDS = ["F106", "F129", "F158"]
TRUE = {"True", "true", "1", "1.0"}


def a0(g, k):
    v = g.attrs[k]
    v = v[0] if np.ndim(v) > 0 else v
    return v.decode() if isinstance(v, bytes) else v


X, y = [], []
with h5py.File(H5, "r") as f:
    g = f["images"]
    for nm in list(g.keys())[:N]:
        grp = g[nm]; uid = a0(grp, "uid")
        row = [float(a0(grp, k)) for k in SYS]
        for b in BANDS:
            e = grp[f"exposure_{uid}_{b}"]
            row += [float(a0(e, k)) for k in EXP]
        X.append(row)
        y.append(1 if str(a0(grp, "substructure")) in TRUE else 0)

X = np.array(X); y = np.array(y)
print(f"N={len(y)}  pos={int(y.sum())}  neg={int((y == 0).sum())}  feats={X.shape[1]}")
Xs = StandardScaler().fit_transform(X)
auc = cross_val_score(LogisticRegression(max_iter=3000), Xs, y, cv=5, scoring="roc_auc")
print(f"METADATA-ONLY (no image) logistic-reg 5-fold AUC = {auc.mean():.4f} +/- {auc.std():.4f}")
print("  (~0.50 => parameters carry NO label info; image is the only signal)")
names = SYS + [f"{b}_{k}" for b in BANDS for k in EXP]
d = np.abs(X[y == 1].mean(0) - X[y == 0].mean(0)) / (X.std(0) + 1e-9)
print("top per-feature class separation |mean(yes)-mean(no)|/std:")
for n, dd in sorted(zip(names, d), key=lambda t: -t[1])[:6]:
    print(f"   {n:26s} {dd:.3f}")
