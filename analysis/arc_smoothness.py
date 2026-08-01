#!/usr/bin/env python
"""GEN5 Phase 1 — the ARC-SMOOTHNESS / beadiness metric that Phase 0 said was
needed before touching the 'too-perfect ellipse' complaint.

Coverage (fraction of ring lit) cannot tell a smooth continuous band from a
real arc's '3-4 dots'. Both can light the same sectors. This measures the
AZIMUTHAL structure of the arc itself, on the azimuthal-median-subtracted
residual in the arc annulus:

  n_beads      : # of distinct azimuthal peaks along the arc (prominence-gated,
                 circular). Smooth band -> 1; beaded real arc -> 3-4.
  roughness    : std/mean of the azimuthal profile over the LIT arc sectors
                 (how bumpy the band is). Smooth -> low; beaded -> high.
  duty_cycle   : within the arc's angular span, fraction of sectors above
                 half the arc's peak. Smooth band -> ~1; beaded (bright dots +
                 dark gaps) -> lower.

Same deflector-centering + annulus as analysis/phase0_characterize.py, so the
numbers are comparable to the Phase 0 characterization.
"""
import csv
import os

import h5py
import numpy as np
from scipy.ndimage import gaussian_filter, label
from scipy.signal import find_peaks

PIX = 0.05
NSECT = 60  # 6 deg sectors


def robust_sky(img, s=12):
    c = np.concatenate([img[:s, :s].ravel(), img[:s, -s:].ravel(),
                        img[-s:, :s].ravel(), img[-s:, -s:].ravel()])
    return np.median(c), max(1.4826 * np.median(np.abs(c - np.median(c))), 1e-9)


def defl_center(gs, rms, n):
    cframe = (n - 1) / 2.0
    det = gs > 4 * rms
    lab, nlab = label(det)
    yy, xx = np.mgrid[0:n, 0:n]
    best = None
    for i in range(1, nlab + 1):
        m = lab == i
        if m.sum() < 5:
            continue
        cy, cx = yy[m].mean(), xx[m].mean()
        r = np.hypot(cy - cframe, cx - cframe)
        peak = gs[m].max()
        cand = (peak, cy, cx, r)
        if best is None:
            best = cand
        # brightest-of-3-nearest-centre proxy: prefer central bright blob
        if r < best[3] and peak > 0.35 * best[0]:
            best = cand
    return (best[1], best[2]) if best else (cframe, cframe)


def azimuthal_profile(resid, rr, phi, ann, rms):
    """Return per-sector arc intensity (clipped >=0 residual mean) over annulus."""
    prof = np.zeros(NSECT)
    lit = np.zeros(NSECT, bool)
    sect = (phi // (360.0 / NSECT)).astype(int) % NSECT
    for s in range(NSECT):
        m = ann & (sect == s)
        if m.any():
            v = np.clip(resid[m], 0, None)
            prof[s] = v.mean()
            lit[s] = (resid[m] > 3 * rms).any()
    return prof, lit


def smoothness(img, theta_pub):
    n = img.shape[0]
    sky, rms = robust_sky(img)
    g = img.astype(float) - sky
    gs = gaussian_filter(g, 1.2)
    cy, cx = defl_center(gs, rms, n)
    yy, xx = np.mgrid[0:n, 0:n]
    rr = np.hypot(yy - cy, xx - cx)
    phi = (np.degrees(np.arctan2(yy - cy, xx - cx)) + 360) % 360

    rbin = rr.astype(int)
    prof_r = np.zeros(rbin.max() + 1)
    for k in range(rbin.max() + 1):
        mk = rbin == k
        if mk.any():
            prof_r[k] = np.median(gs[mk])
    resid = gs - prof_r[rbin]

    rE = theta_pub / PIX
    if not (2.0 < rE < 0.48 * n):
        radii = np.arange(6, int(0.45 * n))
        pw = [np.clip(resid[(rbin == int(r))], 0, None).sum() for r in radii]
        rE = float(radii[int(np.argmax(pw))]) if pw else 0.3 * n
    ann = (rr >= 0.55 * rE) & (rr <= 1.5 * rE)

    prof, lit = azimuthal_profile(resid, rr, phi, ann, rms)
    coverage = lit.mean()
    if lit.sum() < 2 or prof.max() <= 0:
        return dict(coverage=round(coverage, 3), n_beads="", roughness="",
                    duty_cycle="", arc_span="")

    # circular peak count (bead count) on the smoothed profile
    pk = prof / prof.max()
    ext = np.concatenate([pk, pk, pk])
    peaks, _ = find_peaks(ext, height=0.40, prominence=0.25, distance=2)
    peaks = [p - NSECT for p in peaks if NSECT <= p < 2 * NSECT]
    n_beads = len(peaks)

    litv = prof[lit]
    roughness = float(litv.std() / litv.mean()) if litv.mean() > 0 else 0.0

    # duty cycle within the arc's angular span (contiguous run containing peak)
    span = int(lit.sum())
    above_half = int((prof[lit] > 0.5 * prof.max()).sum())
    duty = above_half / span if span else 0.0

    return dict(coverage=round(coverage, 3), n_beads=n_beads,
                roughness=round(roughness, 3), duty_cycle=round(duty, 3),
                arc_span=span)


def run(path, key, tkey, out_csv):
    f = h5py.File(path, "r")
    ims = f[key][:]
    thetas = f[tkey][:] if tkey in f else np.full(len(ims), np.nan)
    rows = []
    for i, im in enumerate(ims):
        r = smoothness(np.asarray(im, float), float(thetas[i]))
        r["i"] = i
        rows.append(r)
    with open(out_csv, "w", newline="") as fo:
        w = csv.DictWriter(fo, fieldnames=["i", "coverage", "n_beads",
                                           "roughness", "duty_cycle", "arc_span"])
        w.writeheader()
        w.writerows(rows)
    return rows


def summ(rows, tag):
    def arr(k):
        return np.array([r[k] for r in rows if r[k] != ""], float)
    nb, rg, dc = arr("n_beads"), arr("roughness"), arr("duty_cycle")
    print("\n== %s (N=%d, arcs measured=%d) ==" % (tag, len(rows), len(nb)))
    print("  n_beads      q25/50/75 = %s | frac 1-bead (smooth) = %d%%"
          % (np.percentile(nb, [25, 50, 75]).round(1), int(100 * (nb <= 1).mean())))
    print("  roughness    q25/50/75 = %s" % np.percentile(rg, [25, 50, 75]).round(2))
    print("  duty_cycle   q25/50/75 = %s | frac>0.8 (near-solid band) = %d%%"
          % (np.percentile(dc, [25, 50, 75]).round(2), int(100 * (dc > 0.8).mean())))


if __name__ == "__main__":
    HERE = "/Users/nurkyz/code/LensFusion/_local/reviews"
    real = run(os.path.join(HERE, "q1_real_review/raw/q1_slde_eval_f2p85_zoom.h5"),
               "images", "theta_E_pub",
               os.path.join(HERE, "q1_real_review/real_q1_smoothness.csv"))
    gen5 = run(os.path.join(HERE, "g5_c21_pilot_review/raw/euclid_v4.h5"),
               "lensed", "theta_E",
               os.path.join(HERE, "g5_c21_pilot_review/gen5_v4_smoothness.csv"))
    summ(real, "REAL Q1")
    summ(gen5, "GEN5 v4")
