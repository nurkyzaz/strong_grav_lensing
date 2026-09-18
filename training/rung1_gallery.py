#!/usr/bin/env python
"""Eyeball Rung 1: (1) verify image<->label alignment, (2) show YES (subhalo)
vs NO (smooth) example images, (3) show the per-class MEAN image + difference to
reveal whether there is ANY systematic, visible signal. No torch (login-node ok).

    python rung1_gallery.py <labeled.h5> <out_prefix> [--nmean 400]
"""
import argparse
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import h5py
from astropy.visualization import make_lupton_rgb

BANDS = ["F106", "F129", "F158"]          # blue, green, red
TRUE = {"True", "true", "1", "1.0", "TRUE"}


def attr0(g, n):
    v = g.attrs[n]
    v = v[0] if np.ndim(v) > 0 else v
    return v.decode() if isinstance(v, bytes) else v


def load(grp, uid):
    return np.stack([grp[f"exposure_{uid}_{b}"][:] for b in BANDS]).astype("float32")


def norm01(x):
    lo, hi = np.percentile(x, 1), np.percentile(x, 99.5)
    return np.clip((x - lo) / (hi - lo + 1e-9), 0, 1)


def rgb(img):  # img (3,H,W) -> RGB using F158=R, F129=G, F106=B
    return make_lupton_rgb(norm01(img[2]), norm01(img[1]), norm01(img[0]),
                           stretch=0.5, Q=6)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("h5_path")
    ap.add_argument("out_prefix")
    ap.add_argument("--nshow", type=int, default=6)
    ap.add_argument("--nmean", type=int, default=400)
    args = ap.parse_args()

    with h5py.File(args.h5_path, "r") as f:
        g = f["images"]
        names = list(g.keys())
        yes, no = [], []
        for nm in names:
            lab = str(attr0(g[nm], "substructure"))
            (yes if lab in TRUE else no).append(nm)
            if len(yes) >= args.nmean and len(no) >= args.nmean:
                break

        print("=== alignment check: group / uid-attr / substructure / bands-present ===")
        for nm in yes[:3] + no[:3]:
            grp = g[nm]; uid = attr0(grp, "uid")
            ok = all(f"exposure_{uid}_{b}" in grp for b in BANDS)
            # does the group NAME's number match the uid attr?
            name_num = nm.split("_")[-1]
            print(f"  {nm}  uid={uid}  name_matches_uid={name_num == str(uid)}  "
                  f"sub={attr0(grp,'substructure')}  bands_ok={ok}")

        # ---- gallery: YES row vs NO row ----
        fig, ax = plt.subplots(2, args.nshow, figsize=(2.4 * args.nshow, 5.2))
        for j, nm in enumerate(yes[:args.nshow]):
            grp = g[nm]; im = load(grp, attr0(grp, "uid"))
            ax[0, j].imshow(rgb(im)); ax[0, j].set_title(nm.split("_")[-1], fontsize=8)
            ax[0, j].axis("off")
        for j, nm in enumerate(no[:args.nshow]):
            grp = g[nm]; im = load(grp, attr0(grp, "uid"))
            ax[1, j].imshow(rgb(im)); ax[1, j].set_title(nm.split("_")[-1], fontsize=8)
            ax[1, j].axis("off")
        ax[0, 0].set_ylabel("SUBHALOS (yes)", fontsize=11)
        ax[1, 0].set_ylabel("SMOOTH (no)", fontsize=11)
        fig.suptitle("Rung 1 examples — can you tell yes from no by eye?")
        fig.tight_layout()
        fig.savefig(f"{args.out_prefix}_gallery.png", dpi=110)
        print(f"wrote {args.out_prefix}_gallery.png")

        # ---- mean images + difference over nmean each ----
        def stack_mean(nmlist):
            acc = None; k = 0
            for nm in nmlist[:args.nmean]:
                grp = g[nm]; im = load(grp, attr0(grp, "uid"))
                acc = im if acc is None else acc + im
                k += 1
            return acc / k
        my, mn = stack_mean(yes), stack_mean(no)
        diff = my - mn                                   # (3,H,W)
        print(f"\nmean|YES-NO| per band (F106/F129/F158): "
              f"{[round(float(np.mean(np.abs(diff[c]))),5) for c in range(3)]}")
        print(f"max|YES-NO|: {float(np.max(np.abs(diff))):.5f}  "
              f"(typical pixel value ~0.34 MJy/sr, so this is the systematic signal size)")

        fig2, ax2 = plt.subplots(1, 3, figsize=(12, 4.2))
        ax2[0].imshow(rgb(my)); ax2[0].set_title(f"mean of {args.nmean} YES"); ax2[0].axis("off")
        ax2[1].imshow(rgb(mn)); ax2[1].set_title(f"mean of {args.nmean} NO"); ax2[1].axis("off")
        d = diff[1]  # F129 difference map
        vmax = np.percentile(np.abs(d), 99) + 1e-9
        im = ax2[2].imshow(d, cmap="RdBu_r", vmin=-vmax, vmax=vmax)
        ax2[2].set_title("mean(YES)-mean(NO), F129"); ax2[2].axis("off")
        fig2.colorbar(im, ax=ax2[2], fraction=0.046)
        fig2.suptitle("If YES and NO differ systematically, the right panel shows structure")
        fig2.tight_layout()
        fig2.savefig(f"{args.out_prefix}_meandiff.png", dpi=110)
        print(f"wrote {args.out_prefix}_meandiff.png")


if __name__ == "__main__":
    main()
