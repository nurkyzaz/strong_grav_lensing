#!/usr/bin/env python
"""Phase 0: characterize real Euclid Q1 (322 frozen eval lenses) and, with
the SAME estimator, GEN5 v4 — turns Nurkyz's qualitative review into targets.

Per lens:
  deflector: center (px from frame center), half-light Re (px, arcsec)
  companions: n field sources (>=3sig blobs beyond the arc annulus)
  arc (in the annulus [0.55,1.5] r_E, on the azimuthal-median-subtracted
       residual): azimuthal coverage (fraction of 24 sectors lit),
       n_knots (connected sig components), arc radius (peak-resid radius, px),
       arc/deflector flux ratio, arc contrast (peak resid / sky rms)
  quality flags: off_center (bright peak far from frame centre),
       theta_mismatch (on-image arc radius vs theta_E_pub),
       no_arc (coverage + contrast both low), two_light (2 comparable central
       peaks, no arc), tiny_theta (theta_E_pub < 0.1")
"""
import csv
import os
import sys

import h5py
import numpy as np
from scipy.ndimage import gaussian_filter, label

PIX = 0.05


def robust_sky(img, s=12):
    c = np.concatenate([img[:s, :s].ravel(), img[:s, -s:].ravel(),
                        img[-s:, :s].ravel(), img[-s:, -s:].ravel()])
    return np.median(c), max(1.4826 * np.median(np.abs(c - np.median(c))), 1e-9)


def analyze(img, theta_pub):
    n = img.shape[0]
    cframe = (n - 1) / 2.0
    sky, rms = robust_sky(img)
    g = img.astype(float) - sky
    gs = gaussian_filter(g, 1.2)

    # --- deflector center = brightest blob nearest frame centre ---
    det = gs > 4 * rms
    lab, nlab = label(det)
    blobs = []
    yy, xx = np.mgrid[0:n, 0:n]
    for i in range(1, nlab + 1):
        m = lab == i
        if m.sum() < 5:
            continue
        peak = gs[m].max()
        cy, cx = yy[m].mean(), xx[m].mean()
        blobs.append(dict(area=int(m.sum()), peak=float(peak), cy=cy, cx=cx,
                          r=float(np.hypot(cy - cframe, cx - cframe))))
    if not blobs:
        return None
    bright = sorted(blobs, key=lambda b: -b["peak"])
    defl = min(bright[:3], key=lambda b: b["r"])
    cy, cx = defl["cy"], defl["cx"]
    off_center = defl["r"]

    rr = np.hypot(yy - cy, xx - cx)

    # deflector Re (half-light within r<30px of its own centre)
    within = rr < 30
    f = np.clip(g, 0, None) * within
    order = np.argsort(rr[within])
    fv = f[within][order]
    cum = np.cumsum(fv)
    tot = cum[-1]
    re_px = float(rr[within][order][np.searchsorted(cum, 0.5 * tot)]) if tot > 0 else np.nan

    # azimuthal-median subtraction -> residual (removes smooth deflector+sky)
    rbin = rr.astype(int)
    prof = np.zeros(rbin.max() + 1)
    for k in range(rbin.max() + 1):
        mk = rbin == k
        if mk.any():
            prof[k] = np.median(gs[mk])
    resid = gs - prof[rbin]

    # arc annulus around theta_E_pub (fallback: scan 0.3-2.4" if theta invalid)
    rE = theta_pub / PIX
    if not (2.0 < rE < 0.48 * n):
        # scan for the radius of max azimuthally-summed residual
        radii = np.arange(6, int(0.45 * n))
        pw = [np.clip(resid[(rbin == int(r))], 0, None).sum() for r in radii]
        rE = float(radii[int(np.argmax(pw))]) if pw else 0.5 * n * 0.3
    r_in, r_out = 0.55 * rE, 1.5 * rE
    ann = (rr >= r_in) & (rr <= r_out)

    sig = (resid > 3 * rms) & ann
    # azimuthal coverage: 24 sectors, lit if any sig pixel
    phi = (np.degrees(np.arctan2(yy - cy, xx - cx)) + 360) % 360
    sect = (phi[sig] // 15).astype(int) if sig.any() else np.array([], int)
    coverage = len(set(sect.tolist())) / 24.0

    labA, nA = label(sig)
    n_knots = sum(1 for i in range(1, nA + 1) if (labA == i).sum() >= 4)

    arc_flux = float(np.clip(resid[sig], 0, None).sum())
    defl_flux = float(np.clip(g, 0, None)[rr < 0.5 * rE].sum()) if rE > 0 else np.nan
    arc_defl = arc_flux / defl_flux if defl_flux and defl_flux > 0 else np.nan
    arc_contrast = float(resid[ann].max() / rms) if ann.any() else 0.0

    # on-image arc radius = flux-weighted mean radius of sig arc pixels
    arc_r = float(rr[sig].mean()) if sig.any() else np.nan

    # field companions: sig blobs OUTSIDE the arc annulus and off-centre
    ncomp = 0
    for b in blobs:
        if b is defl:
            continue
        br = np.hypot(b["cy"] - cy, b["cx"] - cx)
        if br > r_out or br < r_in * 0.5:  # not part of the arc ring
            ncomp += 1

    # two-light: 2+ central blobs of comparable peak within 0.4n, weak arc
    central = [b for b in blobs if b["r"] < 0.32 * n]
    comparable = [b for b in central if b["peak"] > 0.35 * defl["peak"]]
    two_light = int(len(comparable) >= 2 and coverage < 0.30)

    theta_mismatch = 0
    if np.isfinite(arc_r) and rE > 0:
        ratio = arc_r / rE
        theta_mismatch = int(coverage > 0.15 and (ratio < 0.6 or ratio > 1.7))

    return dict(
        off_center=round(off_center, 1), defl_re_px=round(re_px, 1),
        defl_re_as=round(re_px * PIX, 3), n_field_comp=ncomp,
        arc_coverage=round(coverage, 3), n_knots=n_knots,
        arc_radius_px=round(arc_r, 1) if np.isfinite(arc_r) else "",
        arc_defl_flux=round(arc_defl, 4) if np.isfinite(arc_defl) else "",
        arc_contrast=round(arc_contrast, 1),
        flag_off_center=int(off_center > 22),
        flag_no_arc=int(coverage < 0.13 and arc_contrast < 4.5),
        flag_two_light=two_light,
        flag_theta_mismatch=theta_mismatch,
        flag_tiny_theta=int(theta_pub < 0.10),
    )


def run(path, key, theta_key, out_csv, names_key="names"):
    f = h5py.File(path, "r")
    ims = f[key][:]
    thetas = f[theta_key][:] if theta_key in f else np.full(len(ims), np.nan)
    names = ([x.decode() if hasattr(x, "decode") else str(x) for x in f[names_key][:]]
             if names_key in f else [str(i) for i in range(len(ims))])
    rows = []
    for i, im in enumerate(ims):
        r = analyze(np.asarray(im, float), float(thetas[i]))
        if r is None:
            r = dict(off_center="", defl_re_px="", defl_re_as="", n_field_comp="",
                     arc_coverage="", n_knots="", arc_radius_px="", arc_defl_flux="",
                     arc_contrast="", flag_off_center=1, flag_no_arc=1,
                     flag_two_light=0, flag_theta_mismatch=0, flag_tiny_theta=0)
        r["i"] = i
        r["name"] = names[i]
        r["theta_E_pub"] = round(float(thetas[i]), 3)
        rows.append(r)
    cols = ["i", "name", "theta_E_pub", "off_center", "defl_re_px", "defl_re_as",
            "n_field_comp", "arc_coverage", "n_knots", "arc_radius_px",
            "arc_defl_flux", "arc_contrast", "flag_off_center", "flag_no_arc",
            "flag_two_light", "flag_theta_mismatch", "flag_tiny_theta"]
    with open(out_csv, "w", newline="") as fo:
        w = csv.DictWriter(fo, fieldnames=cols)
        w.writeheader()
        for r in rows:
            w.writerow(r)
    return rows


def summ(rows, tag):
    def arr(k):
        return np.array([r[k] for r in rows if r[k] != ""], float)
    cov = arr("arc_coverage")
    print("\n== %s (N=%d) ==" % (tag, len(rows)))
    print("  arc coverage (frac of ring lit): q10/50/90 = %s | full-ring(>0.8): %d%% | partial(0.2-0.6): %d%%"
          % (np.percentile(cov, [10, 50, 90]).round(2), int(100 * (cov > 0.8).mean()),
             int(100 * ((cov >= 0.2) & (cov <= 0.6)).mean())))
    print("  n_knots: q10/50/90 = %s" % np.percentile(arr("n_knots"), [10, 50, 90]).astype(int))
    print("  n_field_comp: q10/50/90 = %s | frac>4 = %d%%"
          % (np.percentile(arr("n_field_comp"), [10, 50, 90]).astype(int),
             int(100 * (arr("n_field_comp") > 4).mean())))
    print("  defl Re: med %.2f\" | arc/defl flux: med %.3f | arc contrast: med %.1f"
          % (np.nanmedian(arr("defl_re_as")), np.nanmedian(arr("arc_defl_flux")),
             np.nanmedian(arr("arc_contrast"))))
    for fl in ("flag_off_center", "flag_no_arc", "flag_two_light",
               "flag_theta_mismatch", "flag_tiny_theta"):
        print("  %s: %d" % (fl, sum(int(r[fl]) for r in rows)))


HERE = "/Users/nurkyz/Desktop/LensFusion"
real = run(os.path.join(HERE, "q1_real_review/raw/q1_slde_eval_f2p85_zoom.h5"),
           "images", "theta_E_pub",
           os.path.join(HERE, "q1_real_review/real_q1_characterization.csv"))
gen5 = run(os.path.join(HERE, "g5_c21_pilot_review/raw/euclid_v4.h5"),
           "lensed", "theta_E",
           os.path.join(HERE, "g5_c21_pilot_review/gen5_v4_characterization.csv"))
summ(real, "REAL Q1")
summ(gen5, "GEN5 v4")

print("\n== Nurkyz flagged real lenses ==")
by_i = {r["i"]: r for r in real}
for idx in (4, 13, 86, 143, 155, 161, 166, 215, 287, 320, 79):
    r = by_i.get(idx)
    if r:
        fl = [k.replace("flag_", "") for k in r if k.startswith("flag_") and r[k]]
        print("  #%-3d theta=%.3f cov=%s knots=%s field_comp=%s contrast=%s  flags:%s"
              % (idx, r["theta_E_pub"], r["arc_coverage"], r["n_knots"],
                 r["n_field_comp"], r["arc_contrast"], ",".join(fl) or "none"))
