#!/usr/bin/env python
"""
definitional_offset.py  -  quantify how much of the SLACS '+18% bias' is just a
label-definition difference (your training label kappa_bar(<r)=1 vs an SIE/SIS-like
theta_E), measured on the SIM kappa maps where you have the truth.

Landmarks, per azimuthally-averaged kappa profile about the map centre:
  r1 = radius where kappa_bar(<r) crosses 1   <- YOUR label definition (einstein_radius_hard)
  r2 = radius where kappa(r) crosses 0.5       <- the isothermal landmark (SIS: kappa(theta_E)=0.5)
For a pure SIS, r1 == r2. The ratio r1/r2 - 1 is the per-lens definitional offset.
If its MEDIAN ~ +0.15..+0.20, the SLACS '+18%' is mostly definitional (not model error).
If it also CORRELATES with theta_E, the definition difference flattens the slope too.

Usage:
  python definitional_offset.py --kappa <kappa_file.h5> [--key kappa] [--pixscale 0.0605] [--n 800]
Caveat: r2 is a PROXY for the SIE fit, not Bolton's actual image-plane SIE fit. It bounds
the effect; the exact number needs an SIE fit (PyAutoLens) on the same systems.
"""
import argparse
import numpy as np
import h5py


def azimuthal_profile(kmap):
    H, W = kmap.shape
    cy, cx = (H - 1) / 2.0, (W - 1) / 2.0
    yy, xx = np.mgrid[0:H, 0:W]
    r = np.hypot(xx - cx, yy - cy).ravel()
    k = kmap.ravel()
    rbin = np.floor(r).astype(int)
    nb = rbin.max() + 1
    ksum = np.bincount(rbin, weights=k, minlength=nb)
    kcnt = np.bincount(rbin, minlength=nb).astype(float)
    kprof = ksum / np.maximum(kcnt, 1)          # mean kappa in annulus r..r+1  -> kappa(r)
    # cumulative mean within radius r (area-weighted by pixel counts)
    cum_k = np.cumsum(ksum)
    cum_n = np.cumsum(kcnt)
    kbar = cum_k / np.maximum(cum_n, 1)         # kappa_bar(<r)
    radii = np.arange(nb)
    return radii, kprof, kbar


def first_cross(radii, y, level, descending=True):
    # outermost crossing of y(level), linear-interpolated, scanning outward
    above = y >= level
    idx = None
    for i in range(1, len(y)):
        if above[i - 1] and not above[i]:       # crosses downward
            idx = i
            break
    if idx is None:
        return np.nan
    y0, y1 = y[idx - 1], y[idx]
    if y1 == y0:
        return float(radii[idx])
    f = (y0 - level) / (y0 - y1)
    return float(radii[idx - 1] + f)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--kappa", required=True)
    ap.add_argument("--key", default="kappa")
    ap.add_argument("--pixscale", type=float, default=0.0605)
    ap.add_argument("--n", type=int, default=800)
    args = ap.parse_args()

    with h5py.File(args.kappa, "r") as h:
        key = args.key if args.key in h else list(h.keys())[0]
        K = h[key]
        N = min(args.n, K.shape[0])
        sel = np.linspace(0, K.shape[0] - 1, N).astype(int)
        maps = K[sel]
    if maps.ndim == 4:
        maps = maps[:, 0]

    r1s, r2s = [], []
    for km in maps:
        km = np.asarray(km, float)
        radii, kprof, kbar = azimuthal_profile(km)
        r1 = first_cross(radii, kbar, 1.0)      # kappa_bar=1  (your label)
        r2 = first_cross(radii, kprof, 0.5)     # kappa=0.5    (SIS landmark)
        r1s.append(r1)
        r2s.append(r2)

    r1 = np.array(r1s) * args.pixscale
    r2 = np.array(r2s) * args.pixscale
    ok = np.isfinite(r1) & np.isfinite(r2) & (r2 > 0)
    r1, r2 = r1[ok], r2[ok]
    offset = 100.0 * (r1 - r2) / r2

    print(f"\nN usable = {ok.sum()} / {len(ok)}   pixscale={args.pixscale}\"/px")
    print(f"  theta_E(kappa_bar=1)  median = {np.median(r1):.3f}\"  [your training label]")
    print(f"  theta_E(kappa=0.5)    median = {np.median(r2):.3f}\"  [SIS landmark proxy for SIE]")
    print(f"\n  DEFINITIONAL OFFSET  (kappa_bar=1 vs kappa=0.5):")
    print(f"     median = {np.median(offset):+.1f}%   16-84% = "
          f"[{np.percentile(offset,16):+.1f},{np.percentile(offset,84):+.1f}]%")
    rho = np.corrcoef(r1, offset)[0, 1]
    print(f"     corr(offset, theta_E) = {rho:+.2f}   "
          f"(strong => the offset is theta_E-dependent => it flattens the slope, not just shifts)")
    print("\n  Read against your SLACS result (+17.9% median, slope 0.34):")
    print("   - if median offset is ~+15..+20%, most of the SLACS BIAS is definitional, not model error")
    print("   - if corr(offset, theta_E) is strongly negative, part of the LOW SLOPE is definitional too")
    print("   - whatever is left over is the real sim->real tracking gap (arc realism), NOT craters\n")


if __name__ == "__main__":
    main()
