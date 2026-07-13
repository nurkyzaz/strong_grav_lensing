#!/usr/bin/env python
"""
inspect_flagged.py
Triage flagged cutouts: is it a BROKEN cutout (drop) or a hard/faint-arc lens (keep)?

For each named lens it renders 3 stretches (linear / asinh / aggressive percentile)
and reports whether the light is actually centred. A galaxy sitting under the cross
=> KEEP (faint arc is buried, that's the benchmark's job). Blank centre or light
pushed to an edge => DROP (bad coordinate / off-footprint / artifact).

Usage:
  python inspect_flagged.py SDSSJ0324-0110 J0955+0101 J1016+3859 J1403+0006
  python inspect_flagged.py --files real_slacs_images.h5 real_s4tm_images.h5 J1016+3859
"""
import sys, os, argparse, glob
import numpy as np
import h5py
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.ndimage import gaussian_filter


def find_in_files(name, files):
    for fp in files:
        with h5py.File(fp, "r") as f:
            names = [n.decode() if isinstance(n, bytes) else str(n) for n in f["names"][:]]
            if name in names:
                i = names.index(name)
                img = np.asarray(f["images"][i, 0], np.float32)
                px = float(f.attrs.get("pixscale_arcsec", 0.05))
                th = float(f["theta_E_pub"][i]) if "theta_E_pub" in f else np.nan
                return img, px, th, fp
    return None, None, None, None


def centering(img, px):
    """Return (offset_arcsec, center_to_edge_ratio). Brightest smoothed blob vs centre."""
    s = gaussian_filter(img, 3.0)
    n = img.shape[0]
    cy, cx = n / 2, n / 2
    yy, xx = np.unravel_index(np.argmax(s), s.shape)
    offset = np.hypot(yy - cy, xx - cx) * px
    r = n // 6
    center_med = np.median(img[int(cy)-r:int(cy)+r, int(cx)-r:int(cx)+r])
    edge_med = np.median(np.concatenate([img[:r].ravel(), img[-r:].ravel()]))
    ratio = (center_med - edge_med) / (abs(edge_med) + 1e-6)
    return offset, ratio


def stretch(img, mode):
    v = img - np.median(img)
    if mode == "linear":
        lo, hi = np.percentile(v, [1, 99])
        return np.clip((v - lo) / (hi - lo + 1e-8), 0, 1)
    if mode == "asinh":
        return np.arcsinh(v / (np.std(v) + 1e-8))
    lo, hi = np.percentile(v, [40, 99.7])     # aggressive: reveal faint arcs
    return np.clip((v - lo) / (hi - lo + 1e-8), 0, 1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("names", nargs="+")
    ap.add_argument("--files", nargs="+",
                    default=sorted(glob.glob("real_*images.h5")))
    ap.add_argument("--out", default="flagged_triage.png")
    args = ap.parse_args()
    if not args.files:
        sys.exit("no real_*images.h5 found; pass --files")

    rows = []
    for nm in args.names:
        img, px, th, fp = find_in_files(nm, args.files)
        if img is None:
            print(f"  {nm:16s} NOT FOUND in {args.files}")
            continue
        off, ratio = centering(img, px)
        verdict = ("centre blank/off -> likely DROP" if (off > 1.0 or ratio < 0.3)
                   else "galaxy centred -> likely KEEP (faint/buried arc)")
        print(f"  {nm:16s} [{os.path.basename(fp):22s}] theta_E_pub={th:.2f}\"  "
              f"light offset={off:.2f}\"  centre/edge={ratio:5.1f}  -> {verdict}")
        rows.append((nm, img, off, ratio))

    if not rows:
        sys.exit("nothing to plot")
    fig, ax = plt.subplots(len(rows), 3, figsize=(9, 3 * len(rows)))
    ax = np.atleast_2d(ax)
    for j, (nm, img, off, ratio) in enumerate(rows):
        for k, mode in enumerate(("linear", "asinh", "percentile")):
            a = ax[j, k]
            a.imshow(stretch(img, mode), origin="lower", cmap="gray")
            n = img.shape[0]
            a.plot(n/2, n/2, "+", color="red", ms=12, mew=1.5)
            a.set_xticks([]); a.set_yticks([])
            if j == 0:
                a.set_title(mode, fontsize=10)
        ax[j, 0].set_ylabel(f"{nm}\noff={off:.2f}\"", fontsize=9)
    plt.tight_layout()
    plt.savefig(args.out, dpi=110, bbox_inches="tight")
    print(f"\nwrote {args.out} -- the 'percentile' column reveals faint arcs; "
          f"if a galaxy is centred there, KEEP it.")


if __name__ == "__main__":
    main()
