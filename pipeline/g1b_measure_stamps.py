#!/usr/bin/env python
"""C5: G1b per-stamp measurements INCLUDING isophote a3/a4 (feeds AR3).

Extends g1_measure_stamps.py (same base schema, drop-in for g2_merge_libs /
g2_make_manifest) with an isophote Fourier analysis:

  * per semi-major axis a on a log grid spanning ~[0.35, 1.6] Re, fit the
    ellipse (x0, y0, q, PA) that NULLS the 1st+2nd azimuthal harmonics of
    I(phi) sampled along it (Jedrzejewski 1987 fixpoint, found here by
    direct Nelder-Mead minimisation instead of the classical iteration);
  * on the fitted ellipse, measure 3rd/4th harmonics A3,B3,A4,B4 of I(phi)
    and convert to RELATIVE geometric deviations a_k = A_k / (|dI/da| * a)
    (Bender & Moellenhoff 1987 convention; a4 > 0 = disky, < 0 = boxy;
    phi measured from the major axis, so the sign convention is standard);
  * aggregate over gradient-significant annuli: median a3/b3/a4/b4,
    m3/m4 moduli, residual 1+2 harmonic power (blend diagnostic),
    centre drift across annuli (close-pair diagnostic).

sigma_v source: --labels src_table field, BOTH formats supported:
  old  'prop####_vd###_ve##_z0.###'
  g1b  'tierA|vd=251+-11|z=0.223|ACSWFC|2433s|P--'

Usage:
  g1b_measure_stamps.py --stamps S.h5 --src SRC.h5 --labels L.csv --out OUT.csv
      [--limit N] [--preview P.png] [--iso_preview I.png]
"""
import argparse
import csv
import re

import numpy as np
import h5py
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Ellipse as MplEllipse
from scipy.ndimage import gaussian_filter, label, map_coordinates
from scipy.optimize import minimize

PIX = 0.05
ZP = 25.94
NPHI = 128


def prominence(img):
    n = img.shape[0]
    c = n // 2
    yy, xx = np.mgrid[0:n, 0:n]
    rr = np.hypot(yy - c, xx - c)
    rbin = rr.astype(int)
    s = gaussian_filter(img.astype("float64"), 1.5)
    prof = np.zeros(rbin.max() + 1)
    for k in range(rbin.max() + 1):
        m = rbin == k
        if m.any():
            prof[k] = np.median(s[m])
    resid = s - prof[rbin]
    ann = (rr >= 0.4 / PIX) & (rr <= 2.6 / PIX)
    out = rr > 2.6 / PIX
    mad = np.median(np.abs(resid[out] - np.median(resid[out]))) * 1.4826
    if mad <= 0:
        return 0.0
    det = (resid > 3.0 * mad) & ann
    lab, nl = label(det)
    best = 0.0
    for i in range(1, nl + 1):
        m = lab == i
        if m.sum() >= 150:
            best = max(best, float(resid[m].max() / mad))
    return best


def measure_base(st):
    """mag, Re, moment q/PA — identical to g1_measure_stamps.py."""
    n = st.shape[0]
    c = (n - 1) / 2.0
    yy, xx = np.mgrid[0:n, 0:n]
    rr = np.hypot(yy - c, xx - c)
    pos = np.clip(st.astype("float64"), 0, None)
    tot = pos.sum()
    mag = ZP - 2.5 * np.log10(max(tot, 1e-12))
    order = np.argsort(rr.ravel())
    cum = np.cumsum(pos.ravel()[order])
    re_as = rr.ravel()[order][np.searchsorted(cum, 0.5 * tot)] * PIX
    ap = rr < 3.0 / PIX
    w = pos * ap
    ws = w.sum()
    mx = (w * xx).sum() / ws - c
    my = (w * yy).sum() / ws - c
    x2 = (w * (xx - c - mx) ** 2).sum() / ws
    y2 = (w * (yy - c - my) ** 2).sum() / ws
    xy = (w * (xx - c - mx) * (yy - c - my)).sum() / ws
    tr, det = x2 + y2, x2 * y2 - xy ** 2
    disc = max(tr ** 2 / 4 - det, 0.0)
    l1 = tr / 2 + np.sqrt(disc)
    l2 = max(tr / 2 - np.sqrt(disc), 1e-9)
    q = float(np.sqrt(l2 / l1))
    pa = float(0.5 * np.arctan2(2 * xy, x2 - y2))
    return mag, float(re_as), q, pa, (c + mx, c + my)


def sample_ellipse(img, x0, y0, a, q, pa):
    phi = np.linspace(0, 2 * np.pi, NPHI, endpoint=False)
    ct, st_ = np.cos(pa), np.sin(pa)
    X, Y = a * np.cos(phi), a * q * np.sin(phi)
    xs = x0 + X * ct - Y * st_
    ys = y0 + X * st_ + Y * ct
    return map_coordinates(img, [ys, xs], order=1, mode="nearest"), phi


_PHI = np.linspace(0, 2 * np.pi, NPHI, endpoint=False)
_DESIGN = np.vstack([np.ones(NPHI)] +
                    [f(k * _PHI) for k in range(1, 5) for f in (np.cos, np.sin)]).T
_D12 = _DESIGN[:, :5]


def harmonics(I, kmax):
    A = _DESIGN if kmax == 4 else _D12
    coef, _, _, _ = np.linalg.lstsq(A, I, rcond=None)
    return coef  # [c0, C1,S1, C2,S2, (C3,S3, C4,S4)]


def fit_annulus(img, x0, y0, a, q0, pa0):
    """Ellipse at fixed a that nulls harmonics 1+2; returns params + coefs."""
    def cost(p):
        dx, dy, dq, dpa = p
        qq = np.clip(q0 + dq, 0.25, 1.0)
        pen = 0.0
        if abs(dx) > 4 or abs(dy) > 4:
            pen += (abs(dx) + abs(dy)) * 1e3
        I, _ = sample_ellipse(img, x0 + np.clip(dx, -4, 4),
                              y0 + np.clip(dy, -4, 4), a, qq,
                              pa0 + np.clip(dpa, -0.5, 0.5))
        c = harmonics(I, 2)
        scale = max(abs(c[0]), 1e-9)
        return (np.hypot(c[1], c[2]) + np.hypot(c[3], c[4])) / scale + pen
    res = minimize(cost, np.zeros(4), method="Nelder-Mead",
                   options=dict(maxiter=200, xatol=5e-3, fatol=1e-7))
    dx, dy, dq, dpa = res.x
    x0f, y0f = x0 + np.clip(dx, -4, 4), y0 + np.clip(dy, -4, 4)
    qf = float(np.clip(q0 + dq, 0.25, 1.0))
    paf = pa0 + float(np.clip(dpa, -0.5, 0.5))
    I, _ = sample_ellipse(img, x0f, y0f, a, qf, paf)
    c = harmonics(I, 4)
    return (x0f, y0f, qf, paf), c


def isophote_multipoles(st, center, q0, pa0, re_px, sky_sig):
    """Fit annuli across [0.35,1.6] Re; return aggregated a3/a4 + diagnostics."""
    n = st.shape[0]
    img = gaussian_filter(st.astype("float64"), 1.0)  # tame pixel noise
    a_lo = max(3.0, 0.35 * re_px)
    a_hi = min(1.6 * re_px, 0.45 * n)
    if a_hi <= a_lo * 1.1:
        return None
    grid = np.exp(np.linspace(np.log(a_lo), np.log(a_hi), 10))
    x0, y0 = center
    rows = []
    for a in grid:
        (x0f, y0f, qf, paf), c = fit_annulus(img, x0, y0, a, q0, pa0)
        # local radial gradient of the mean isophote intensity
        Ii, _ = sample_ellipse(img, x0f, y0f, a * 0.92, qf, paf)
        Io, _ = sample_ellipse(img, x0f, y0f, a * 1.08, qf, paf)
        grad = (np.mean(Io) - np.mean(Ii)) / (0.16 * a)
        rows.append(dict(a=a, x0=x0f, y0=y0f, q=qf, pa=paf, c=c, grad=grad))
        x0, y0, q0, pa0 = x0f, y0f, qf, paf  # warm-start next annulus
    out = []
    for r in rows:
        denom = abs(r["grad"]) * r["a"]
        # harmonic-coefficient noise ~ sky_sig*sqrt(2/NPHI); relative-amplitude
        # noise = that / denom -> demand < 0.5%
        if denom < sky_sig * np.sqrt(2.0 / NPHI) / 0.005:
            continue
        c = r["c"]
        out.append(dict(a=r["a"],
                        a3=c[5] / denom, b3=c[6] / denom,
                        a4=c[7] / denom, b4=c[8] / denom,
                        h12=(np.hypot(c[1], c[2]) + np.hypot(c[3], c[4])) / denom,
                        x0=r["x0"], y0=r["y0"], q=r["q"], pa=r["pa"]))
    if len(out) < 3:
        return None
    med = lambda k: float(np.median([o[k] for o in out]))
    xs = np.array([o["x0"] for o in out])
    ys = np.array([o["y0"] for o in out])
    drift = float(np.hypot(xs - xs.mean(), ys - ys.mean()).max())
    return dict(iso_a3=med("a3"), iso_b3=med("b3"),
                iso_a4=med("a4"), iso_b4=med("b4"),
                iso_m3=float(np.median([np.hypot(o["a3"], o["b3"]) for o in out])),
                iso_m4=float(np.median([np.hypot(o["a4"], o["b4"]) for o in out])),
                iso_harm12=med("h12"), iso_nann=len(out),
                iso_drift_px=drift,
                iso_q=med("q"), iso_pa_deg=float(np.degrees(med("pa"))),
                rings=[(o["x0"], o["y0"], o["a"], o["q"], o["pa"]) for o in out])


ap = argparse.ArgumentParser()
ap.add_argument("--stamps", required=True)
ap.add_argument("--src", required=True)
ap.add_argument("--labels", default=None)
ap.add_argument("--kine", default=None)
ap.add_argument("--out", required=True)
ap.add_argument("--limit", type=int, default=0, help="pilot: first N stamps only")
ap.add_argument("--preview", default=None)
ap.add_argument("--iso_preview", default=None)
a = ap.parse_args()

with h5py.File(a.stamps, "r") as f:
    stamps = f["stamps"][:]
    src_idx = f["src_index"][:]
with h5py.File(a.src, "r") as f:
    names = [x.decode() if hasattr(x, "decode") else str(x) for x in f["names"][:]]

kin = {}
if a.labels:
    for r in csv.DictReader(open(a.labels)):
        s = r["src_table"]
        m = (re.search(r"vd(\d+)_ve(\d+)_z([\d.]+)", s) or
             re.search(r"vd=(\d+)\+-(\d+)\|z=([\d.]+)", s))
        if m:
            kin[r["name"]] = (float(m.group(1)), float(m.group(2)), float(m.group(3)))
if a.kine:
    for r in csv.DictReader(open(a.kine)):
        try:
            kin[r["name"]] = (float(r["velDisp"]), float(r["velDispErr"]), float(r["z"]))
        except (ValueError, KeyError):
            pass

if a.limit:
    stamps, src_idx = stamps[:a.limit], src_idx[:a.limit]

rows, ring_store = [], {}
for i, (st, si) in enumerate(zip(stamps, src_idx)):
    name = names[int(si)]
    mag, re_as, q, pa_rad, center = measure_base(st)
    prom = float(prominence(st))
    s16 = 16
    corners = np.concatenate([st[:s16, :s16].ravel(), st[:s16, -s16:].ravel(),
                              st[-s16:, :s16].ravel(), st[-s16:, -s16:].ravel()])
    sky_sig = float(np.median(np.abs(corners - np.median(corners))) * 1.4826) + 1e-12
    iso = isophote_multipoles(st, center, q, pa_rad, re_as / PIX, sky_sig)
    vd, ve, z = kin.get(name, (np.nan, np.nan, np.nan))
    row = dict(stamp_id=i, name=name, src_index=int(si), sigma_v=vd,
               sigma_err=ve, z_l=z, mag=round(mag, 3), re_arcsec=round(re_as, 3),
               q=round(q, 3), pa_deg=round(np.degrees(pa_rad), 1),
               prom=round(prom, 1), flag_arcy=int(prom > 25.0))
    if iso is None:
        row.update(iso_a3="", iso_b3="", iso_a4="", iso_b4="", iso_m3="",
                   iso_m4="", iso_harm12="", iso_nann=0, iso_drift_px="",
                   iso_q="", iso_pa_deg="", flag_iso_bad=1, flag_pair=0)
    else:
        rings = iso.pop("rings")
        ring_store[i] = rings
        flag_pair = int(iso["iso_drift_px"] > 4.0 or iso["iso_harm12"] > 0.08)
        row.update({k: (round(v, 5) if isinstance(v, float) else v)
                    for k, v in iso.items()},
                   flag_iso_bad=int(iso["iso_nann"] < 5), flag_pair=flag_pair)
    rows.append(row)
    if (i + 1) % 50 == 0:
        print("  ... %d/%d" % (i + 1, len(stamps)), flush=True)

with open(a.out, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    w.writeheader()
    for r in rows:
        w.writerow(r)

vd = np.array([r["sigma_v"] for r in rows], float)
m4 = np.array([r["iso_a4"] if r["iso_a4"] != "" else np.nan for r in rows], float)
good = np.array([r["flag_iso_bad"] == 0 for r in rows])
print("%s: %d stamps | sigma_v known %d | iso OK %d | pair-flagged %d | "
      "arc-y %d | median a4 %+.4f | disky(a4>0.5%%) %d | boxy(a4<-0.5%%) %d"
      % (a.out, len(rows), np.isfinite(vd).sum(), good.sum(),
         sum(r["flag_pair"] == 1 for r in rows),
         sum(r["flag_arcy"] for r in rows), np.nanmedian(m4),
         int(np.nansum(m4 > 0.005)), int(np.nansum(m4 < -0.005))))

if a.preview:
    k = min(len(stamps), 64)
    fig, axes = plt.subplots(8, 8, figsize=(17, 17))
    for axi, i in zip(axes.ravel(), range(k)):
        st = stamps[i]
        sky = np.median(np.abs(st - np.median(st))) * 1.4826
        axi.imshow(np.arcsinh(st / max(sky, 1e-9)), cmap="gray", origin="lower")
        r = rows[i]
        axi.set_title("%d vd%.0f m%.1f%s" % (i, r["sigma_v"], r["mag"],
                                             " ARC?" if r["flag_arcy"] else ""),
                      fontsize=7)
        axi.axis("off")
    for axi in axes.ravel()[k:]:
        axi.axis("off")
    fig.tight_layout()
    fig.savefig(a.preview, dpi=110)
    print("preview:", a.preview)

if a.iso_preview:
    ids = [i for i in range(len(rows)) if rows[i]["flag_iso_bad"] == 0][:16]
    fig, axes = plt.subplots(4, 4, figsize=(14, 14))
    for axi, i in zip(axes.ravel(), ids):
        st = stamps[i]
        sky = np.median(np.abs(st - np.median(st))) * 1.4826
        axi.imshow(np.arcsinh(st / max(sky, 1e-9)), cmap="gray", origin="lower")
        for (x0, y0, aa, qq, pp) in ring_store.get(i, [])[::3]:
            axi.add_patch(MplEllipse((x0, y0), 2 * aa, 2 * aa * qq,
                                     angle=np.degrees(pp), fill=False,
                                     edgecolor="cyan", lw=0.7))
        r = rows[i]
        axi.set_title("%s a4=%+.3f%% m3=%.3f%%" %
                      (r["name"], 100 * r["iso_a4"], 100 * r["iso_m3"]),
                      fontsize=8)
        axi.axis("off")
    for axi in axes.ravel()[len(ids):]:
        axi.axis("off")
    fig.tight_layout()
    fig.savefig(a.iso_preview, dpi=110)
    print("iso preview:", a.iso_preview)
