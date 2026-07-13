#!/usr/bin/env python
"""
filter_arcs.py
Report the magnification (mu) distribution of an HSTempty file, and optionally write
a filtered copy keeping only mu >= --min_mag (removes the 'blob, not arc' cases).

Report only:   python filter_arcs.py --in lensed_hstempty.h5
Filter + save: python filter_arcs.py --in lensed_hstempty.h5 --min_mag 3.0 --out lensed_hstempty_arc.h5
"""
import argparse, h5py, numpy as np


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="inp", required=True)
    ap.add_argument("--min_mag", type=float, default=None)
    ap.add_argument("--out", default="lensed_hstempty_arc.h5")
    a = ap.parse_args()

    with h5py.File(a.inp, "r") as f:
        if "mag" not in f:
            raise SystemExit("no 'mag' key -- regenerate with the updated generator")
        mag = f["mag"][:]
        keys = [k for k in f.keys()]
        N = len(mag)
        print(f"{a.inp}: N={N}")
        pct = np.percentile(mag, [1, 5, 16, 50, 84, 95, 99])
        print("  mu percentiles [1,5,16,50,84,95,99]:",
              " ".join(f"{p:.2f}" for p in pct))
        # crude text histogram on log10(mu)
        lm = np.log10(np.clip(mag, 1e-3, None))
        hist, edges = np.histogram(lm, bins=20)
        for h, e0, e1 in zip(hist, edges[:-1], edges[1:]):
            print(f"   mu {10**e0:6.2f}-{10**e1:6.2f} | {'#'*int(60*h/hist.max()):60s} {h}")
        for t in (2.0, 3.0, 5.0):
            print(f"  kept if mu>= {t}: {int((mag>=t).sum())} ({100*(mag>=t).mean():.1f}%)")

        if a.min_mag is None:
            print("\n(report only -- pass --min_mag T --out FILE to write the filtered set)")
            return

        keep = mag >= a.min_mag
        print(f"\nwriting {int(keep.sum())}/{N} images with mu>={a.min_mag} -> {a.out}")
        with h5py.File(a.out, "w") as g:
            for k in keys:
                g.create_dataset(k, data=f[k][:][keep])
            for k in f.attrs:
                g.attrs[k] = f.attrs[k]
            g.attrs["min_mag_cut"] = a.min_mag
    print("done")


if __name__ == "__main__":
    main()
