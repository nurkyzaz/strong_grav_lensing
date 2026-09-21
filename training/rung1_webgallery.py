#!/usr/bin/env python
"""Render example galleries (PNG) of the Rung 1 images for a webpage:
labeled training (with yes/no) and unlabeled test (no labels).
    python rung1_webgallery.py <h5> <out.png> <labeled|unlabeled> <n>
"""
import sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import h5py
from astropy.visualization import make_lupton_rgb

BANDS = ["F106", "F129", "F158"]
TRUE = {"True", "true", "1", "1.0"}


def a0(g, k):
    v = g.attrs[k]
    v = v[0] if np.ndim(v) > 0 else v
    return v.decode() if isinstance(v, bytes) else v


def norm01(x):
    lo, hi = np.percentile(x, 1), np.percentile(x, 99.5)
    return np.clip((x - lo) / (hi - lo + 1e-9), 0, 1)


def rgb(im):
    return make_lupton_rgb(norm01(im[2]), norm01(im[1]), norm01(im[0]),
                           stretch=0.5, Q=6)


def load(g, nm):
    grp = g[nm]; uid = a0(grp, "uid")
    return np.stack([grp[f"exposure_{uid}_{b}"][:] for b in BANDS]).astype("float32"), uid


def main():
    h5, out, mode, n = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4])
    with h5py.File(h5, "r") as f:
        g = f["images"]; names = list(g.keys())
        if mode == "labeled":
            scan = names[:4000]
            yes = [nm for nm in scan if str(a0(g[nm], "substructure")) in TRUE][:n // 2]
            no = [nm for nm in scan if str(a0(g[nm], "substructure")) not in TRUE][:n // 2]
            picks = [(nm, "SUBHALOS (yes)") for nm in yes] + [(nm, "SMOOTH (no)") for nm in no]
        else:
            picks = [(nm, "unlabeled") for nm in names[:n]]
        cols = min(n, 8)
        rows = (len(picks) + cols - 1) // cols
        fig, ax = plt.subplots(rows, cols, figsize=(2.0 * cols, 2.4 * rows))
        ax = np.atleast_2d(ax)
        for k in range(rows * cols):
            r, c = divmod(k, cols); a = ax[r, c]; a.axis("off")
            if k < len(picks):
                nm, lab = picks[k]; im, uid = load(g, nm)
                a.imshow(rgb(im)); a.set_title(f"{lab}\n#{uid}", fontsize=8)
        fig.tight_layout()
        fig.savefig(out, dpi=120, bbox_inches="tight")
        print(f"wrote {out} ({len(picks)} images)")


if __name__ == "__main__":
    main()
