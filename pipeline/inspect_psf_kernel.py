#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
inspect_psf_kernel.py -- READ-ONLY inspector for a pixel PSF kernel (.npy).

Required pre-step before fix_psf_kernel.py (see DECISIONS_LOG 2026-07-03):
prints the per-ring radial profile, per-ring zero/positive fractions, a noise
estimate for the clipped stamp, the last signal-dominated radius (the
data-driven --r0), and a wing power-law fit over the signal-dominated annulus
(the data-driven --alpha). Also checks centering and FWHM.

Usage (from ~/cosmos_acs/tiles):
    python inspect_psf_kernel.py acs_psf.npy [--png psf_kernel_profile.png]

Notes on the noise estimate: the stamp was background-subtracted with
negatives clipped to zero (edge zero-fraction ~0.5 or higher). For clipped
zero-mean Gaussian noise, mean(positive pixels) = sigma*sqrt(2/pi), so
sigma ~= mean(positive edge pixels) / 0.7979. Rings whose MEDIAN clears
3*sigma and whose positive fraction >= 0.6 are called signal-dominated
(same criterion family as fix_psf_kernel.py's adaptive r0).
"""
import argparse
import numpy as np


def main():
    p = argparse.ArgumentParser()
    p.add_argument("kernel")
    p.add_argument("--png", default=None,
                   help="optional output PNG of profile + zero fraction")
    p.add_argument("--nsigma", type=float, default=3.0,
                   help="signal threshold in sigma for the ring median")
    p.add_argument("--posfrac", type=float, default=0.6,
                   help="min positive fraction for a signal-dominated ring")
    a = p.parse_args()

    k = np.load(a.kernel).astype(np.float64)
    n = k.shape[0]
    half = n // 2
    peak = k.max()
    cy, cx = np.unravel_index(np.argmax(k), k.shape)
    print("=" * 72)
    print(f"kernel: {a.kernel}")
    print(f"shape={k.shape}  sum={k.sum():.6f}  peak={peak:.4e}  "
          f"negatives={int((k < 0).sum())}  zeros={int((k == 0).sum())}")
    print(f"geometric center=({half},{half})  peak pixel=({cy},{cx})  "
          f"offset=({cy - half:+d},{cx - half:+d}) px"
          + ("   <-- OFF-CENTER, note for the fixer" if (cy, cx) != (half, half) else ""))

    # radii measured from the GEOMETRIC center (what convolution cares about)
    yy, xx = np.mgrid[0:n, 0:n]
    r = np.hypot(yy - half, xx - half)

    # ---- noise estimate from the outermost 2-px shell (clipped-Gaussian model)
    shell = k[r >= half - 1.0]
    pos = shell[shell > 0]
    zero_frac_shell = (shell == 0).mean()
    sigma = pos.mean() / 0.7979 if len(pos) else 0.0
    print(f"noise shell (r>={half-1}): zero_frac={zero_frac_shell:.2f}  "
          f"sigma~{sigma:.3e}  sigma/peak={sigma/peak:.3e}")
    if zero_frac_shell < 0.3:
        print("  [warn] low zero fraction: clipped-noise model may not apply; "
              "treat sigma as approximate")

    # ---- FWHM from the azimuthal-mean profile about the PEAK pixel
    rp = np.hypot(yy - cy, xx - cx).ravel()
    vp = k.ravel()
    o = np.argsort(rp)
    rp, vp = rp[o], vp[o]
    bins = np.arange(0, rp.max() + 0.25, 0.25)
    ib = np.digitize(rp, bins)
    pr, pv = [], []
    for i in range(1, len(bins)):
        m = ib == i
        if m.any():
            pr.append(rp[m].mean())
            pv.append(vp[m].mean())
    pr, pv = np.array(pr), np.array(pv)
    below = np.where(pv < peak / 2.0)[0]
    fwhm = np.nan
    if len(below):
        j = below[0]
        r_hi, v_hi = pr[j - 1], pv[j - 1]
        r_lo, v_lo = pr[j], pv[j]
        fwhm = 2.0 * (r_hi + (v_hi - peak / 2.0) / (v_hi - v_lo) * (r_lo - r_hi))
    print(f"FWHM ~ {fwhm:.2f} px  -> {fwhm*0.05:.3f} arcsec at 0.05\"/px "
          f"(ACS F814W truth ~0.09-0.10\")")

    # ---- per-ring table (1-px annuli, geometric center)
    print("-" * 72)
    print(f"{'ring':>4} {'r_mid':>5} {'npix':>5} {'mean/peak':>10} "
          f"{'median/peak':>11} {'pos_frac':>8} {'zero_frac':>9} {'med>3sig':>8}")
    r0_data = None
    ring_r, ring_med, ring_zero = [], [], []
    for i in range(half + 1):
        m = (r >= i - 0.5) & (r < i + 0.5)
        vals = k[m]
        if len(vals) == 0:
            continue
        med = np.median(vals)
        posf = (vals > 0).mean()
        zf = (vals == 0).mean()
        sig = (med > a.nsigma * sigma) and (posf >= a.posfrac)
        ring_r.append(i)
        ring_med.append(med)
        ring_zero.append(zf)
        print(f"{i:>4} {i:>5} {len(vals):>5} {vals.mean()/peak:>10.3e} "
              f"{med/peak:>11.3e} {posf:>8.2f} {zf:>9.2f} {'YES' if sig else 'no':>8}")
        if sig:
            r0_data = i
    print("-" * 72)

    if r0_data is None:
        print("NO signal-dominated ring found -- kernel is noise beyond the core; "
              "extension would model noise. Get a better stamp instead.")
        return

    # ---- power-law alpha over the signal-dominated annulus [0.55*r0, r0]
    sel = (r > 0.55 * r0_data) & (r <= r0_data) & (k > 0)
    alpha = np.nan
    if sel.sum() >= 10:
        lr, lf = np.log(r[sel]), np.log(k[sel])
        A = np.vstack([lr, np.ones_like(lr)]).T
        alpha = float(np.linalg.lstsq(A, lf, rcond=None)[0][0])
    flag = ""
    if not np.isnan(alpha) and alpha > -2.0:
        flag = "  [warn] shallower than -2: fit may be noise-contaminated"
    print(f"last signal-dominated radius (data-driven --r0): {r0_data} px "
          f"(kernel half-width {half})")
    print(f"wing power-law alpha over [{0.55*r0_data:.1f},{r0_data}] px: "
          f"{alpha:.2f}{flag}")
    print()
    print("suggested next step (do NOT run without checking the table above):")
    print(f"  python fix_psf_kernel.py {a.kernel} --factor 2.0 "
          f"--r0 {r0_data} --alpha {min(alpha, -2.0):.2f}")

    if a.png:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots(1, 2, figsize=(10, 4))
        ax[0].semilogy(ring_r, np.array(ring_med) / peak, "o-", label="ring median")
        ax[0].axhline(a.nsigma * sigma / peak, ls="--", c="r",
                      label=f"{a.nsigma:g} sigma")
        ax[0].axvline(r0_data, ls=":", c="k", label=f"r0={r0_data}")
        ax[0].set_xlabel("r [px]"); ax[0].set_ylabel("median / peak")
        ax[0].legend(); ax[0].set_title("radial profile")
        ax[1].plot(ring_r, ring_zero, "o-")
        ax[1].axvline(r0_data, ls=":", c="k")
        ax[1].set_xlabel("r [px]"); ax[1].set_ylabel("zero fraction")
        ax[1].set_title("zero-clipped fraction per ring")
        fig.tight_layout()
        fig.savefig(a.png, dpi=120)
        print(f"wrote {a.png}")


if __name__ == "__main__":
    main()
