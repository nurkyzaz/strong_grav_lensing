#!/usr/bin/env python
"""Figure 2 for the paper draft: predicted vs. true theta_E for the m3
baseline and hybrid v2 model on both real-lens samples, with Cao et al.
2025's CLAIMED ~5% deviation band drawn as a reference (not their actual
per-lens data -- that matched comparison is a separate, not-yet-done
ablation; the band here is only the literature deviation threshold)."""
import argparse
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def load(path, exclude=None):
    d = pd.read_csv(path)
    if exclude and "name" in d.columns:
        d = d[~d["name"].isin(exclude)]
    P = d["theta_E_pred_arcsec"].to_numpy(float)
    T = d["theta_E_pub_arcsec"].to_numpy(float)
    ok = T > 0
    return P[ok], T[ok]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="figure2_pred_vs_true.png")
    args = ap.parse_args()

    P_m3_slacs, T_m3_slacs = load("brian_run/theta_E_slacs_m3_baseline.csv", ["J0955+0101"])
    P_m3_s4tm, T_m3_s4tm = load("brian_run/theta_E_s4tm_m3_baseline.csv")
    P_v2_slacs, T_v2_slacs = load("brian_run/theta_E_slacs_paltas_v2.csv", ["J0955+0101"])
    P_v2_s4tm, T_v2_s4tm = load("brian_run/theta_E_s4tm_paltas_v2.csv")

    fig, ax = plt.subplots(figsize=(6, 6))
    lim = np.array([0.4, 2.4])
    ax.plot(lim, lim, "k--", lw=1, zorder=1, label="1:1")

    # Cao et al. 2025 claimed ~5% deviation band (reference threshold, NOT
    # their actual per-lens data -- that matched comparison is a separate
    # planned ablation, see paper Sec. 4.5)
    x = np.linspace(*lim, 100)
    ax.fill_between(x, x * 0.95, x * 1.05, color="green", alpha=0.15, zorder=0,
                    label="Cao et al. 2025 claimed $\\lesssim$5% band")

    ax.scatter(T_m3_slacs, P_m3_slacs, marker="o", s=28, color="tab:gray",
              alpha=0.75, label="m3 baseline, SLACS", zorder=2)
    ax.scatter(T_m3_s4tm, P_m3_s4tm, marker="^", s=28, color="tab:gray",
              alpha=0.75, label="m3 baseline, S4TM", zorder=2)
    ax.scatter(T_v2_slacs, P_v2_slacs, marker="o", s=28, color="tab:orange",
              alpha=0.85, label="hybrid v2, SLACS", zorder=3)
    ax.scatter(T_v2_s4tm, P_v2_s4tm, marker="^", s=28, color="tab:red",
              alpha=0.85, label="hybrid v2, S4TM", zorder=3)

    ax.set_xlim(lim); ax.set_ylim(lim)
    ax.set_xlabel("published SIE $\\theta_E$ ($b_{\\rm SIE}$) [arcsec]")
    ax.set_ylabel("CNN predicted $\\theta_E$ [arcsec]")
    ax.set_title("Predicted vs. true $\\theta_E$: baseline vs. hybrid v2")
    ax.legend(fontsize=8, loc="upper left")
    ax.set_aspect("equal")
    fig.tight_layout()
    fig.savefig(args.out, dpi=150)
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
