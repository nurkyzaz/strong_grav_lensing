#!/usr/bin/env python
"""
metrics_real.py
Compute the benchmark metrics from predict_real_lenses.py output CSVs
(columns: name, theta_E_pred_arcsec, theta_E_pub_arcsec).

Reports, per file: N, median fractional error, 16-84% interval, R2, MAE,
and failure rate |dtheta/theta| > 15% (LensFusion's own bar). Writes a scatter PNG.

Usage:
  python metrics_real.py brian_run/theta_E_slacs.csv brian_run/theta_E_s4tm.csv
  python metrics_real.py brian_run/theta_E_slacs.csv --exclude J0955+0101
"""
import sys, os, argparse
import numpy as np
import pandas as pd
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt


def metrics(P, T):
    fr = 100 * (P - T) / T
    R2 = 1 - np.sum((T - P) ** 2) / (np.sum((T - T.mean()) ** 2) + 1e-12)
    return dict(N=len(P), med=np.median(fr),
                p16=np.percentile(fr, 16), p84=np.percentile(fr, 84),
                R2=R2, MAE=np.mean(np.abs(P - T)),
                fail=100 * np.mean(np.abs(fr) > 15))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("csvs", nargs="+")
    ap.add_argument("--exclude", nargs="*", default=[], help="lens names to drop")
    ap.add_argument("--out", default="real_benchmark_scatter.png")
    args = ap.parse_args()

    plt.figure(figsize=(5.5, 5.5))
    lim = [0.4, 2.6]
    plt.plot(lim, lim, "k--", lw=1)
    colors = plt.cm.tab10.colors

    for ci, path in enumerate(args.csvs):
        d = pd.read_csv(path)
        if "theta_E_pub_arcsec" not in d.columns:
            print(f"  {path}: no theta_E_pub_arcsec column -- skipping"); continue
        if args.exclude and "name" in d.columns:
            before = len(d)
            d = d[~d["name"].isin(args.exclude)]
            if len(d) < before:
                print(f"  excluded {before-len(d)} lens(es) from {os.path.basename(path)}")
        P = d["theta_E_pred_arcsec"].to_numpy(float)
        T = d["theta_E_pub_arcsec"].to_numpy(float)
        ok = T > 0
        P, T = P[ok], T[ok]
        m = metrics(P, T)
        tag = os.path.splitext(os.path.basename(path))[0]
        print(f"{tag:24s} N={m['N']:3d} | median {m['med']:+5.1f}% | "
              f"16-84 [{m['p16']:+5.1f},{m['p84']:+5.1f}] | R2 {m['R2']:+.2f} | "
              f"MAE {m['MAE']:.3f}\" | fail>15% {m['fail']:.0f}%")
        plt.scatter(T, P, s=20, color=colors[ci % 10],
                    label=f"{tag} (R2={m['R2']:+.2f})", alpha=0.8)

    plt.xlim(lim); plt.ylim(lim)
    plt.xlabel("published SIE theta_E (b_SIE) [\"]")
    plt.ylabel("CNN theta_E [\"]")
    plt.title("m3 zero-shot on real lenses\ncaveat: kappa_bar=1 vs SIE -> partly definitional offset")
    plt.legend(fontsize=8)
    plt.tight_layout(); plt.savefig(args.out, dpi=120)
    print(f"\nwrote {args.out}")


if __name__ == "__main__":
    main()
