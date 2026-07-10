#!/usr/bin/env python
"""GEN4-G2: build the population manifest — one row per render attempt.

Each row is ONE physically self-consistent system: a real library galaxy
(stamp = the light; measured sigma_v + z_l = the mass) plus a drawn source
redshift -> theta_E COMPUTED (SIS), mass shape = the stamp's measured light
shape (after the row's dihedral) + N(0,10 deg) misalignment, q_mass =
q_light + N(0,0.08). Importance sampling: bin-filling over theta_E [0.45,2.3]
so the EFFECTIVE prior is flat where the library supports it (per-bin fill
reported honestly; unfillable tails NOT silently padded).

Usage: g2_make_manifest.py --kine A.csv [B.csv ...] --n 1200 --seed 42 --out m.csv
"""
import argparse
import csv
import numpy as np
from astropy.cosmology import FlatLambdaCDM
from scipy.stats import truncnorm

C_KMS = 299792.458
cosmo = FlatLambdaCDM(H0=70, Om0=0.3)

ap = argparse.ArgumentParser()
ap.add_argument("--kine", nargs="+", required=True)
ap.add_argument("--n", type=int, required=True)
ap.add_argument("--seed", type=int, default=42)
ap.add_argument("--out", required=True)
ap.add_argument("--tmin", type=float, default=0.45)
ap.add_argument("--tmax", type=float, default=2.30)
ap.add_argument("--nbin", type=int, default=37)
a = ap.parse_args()
rng = np.random.default_rng(a.seed)

gal = []
for fn in a.kine:
    for r in csv.DictReader(open(fn)):
        try:
            vd, ve, z = float(r["sigma_v"]), float(r["sigma_err"]), float(r["z_l"])
            if not (50 < vd < 500 and z > 0.02):
                continue
            gal.append(dict(stamp_id=int(r["stamp_id"]), lib=fn, sigma_v=vd,
                            sigma_err=min(ve, vd * 0.2), z_l=z,
                            mag=float(r["mag"]), q=float(r["q"]),
                            pa=float(r["pa_deg"])))
        except (ValueError, KeyError):
            pass
print("library galaxies usable: %d (from %s)" % (len(gal), ",".join(a.kine)))

# precompute D_ls/D_s on a z_s grid per z_l (coarse; exact per-draw below)
zs_lo, zs_hi = 0.55, 1.10


def draw_zs(zl):
    lo = max(zs_lo, zl + 0.05)
    aa, bb = (lo - 0.65) / 0.15, (zs_hi - 0.65) / 0.15
    return float(truncnorm.rvs(aa, bb, loc=0.65, scale=0.15,
                               random_state=rng.integers(1 << 31)))


def theta_e(vd, zl, zs):
    Ds = cosmo.angular_diameter_distance(zs).value
    Dls = cosmo.angular_diameter_distance_z1z2(zl, zs).value
    return np.degrees(4 * np.pi * (vd / C_KMS) ** 2 * Dls / Ds) * 3600.0


def dihedral_pa(pa, k):
    """Light PA after dihedral k (0-3: rot90 CCW k times; 4-7: rot then fliplr)."""
    p = pa + 90.0 * (k % 4)
    if k >= 4:
        p = 180.0 - p
    return p % 180.0


edges = np.linspace(a.tmin, a.tmax, a.nbin + 1)
cap = int(np.ceil(a.n / a.nbin))
fill = np.zeros(a.nbin, int)
rows = []
attempts = 0
while len(rows) < a.n and attempts < a.n * 400:
    attempts += 1
    g = gal[int(rng.integers(len(gal)))]
    vd = g["sigma_v"] + rng.normal(0, g["sigma_err"])
    zs = draw_zs(g["z_l"])
    th = theta_e(vd, g["z_l"], zs)
    if not (a.tmin <= th < a.tmax):
        continue
    b = int((th - a.tmin) / (a.tmax - a.tmin) * a.nbin)
    if fill[b] >= cap:
        continue
    fill[b] += 1
    k = int(rng.integers(8))
    pa_l = dihedral_pa(g["pa"], k)
    dpa = float(np.clip(rng.normal(0, 10.0), -30, 30))
    qm = float(np.clip(g["q"] + rng.normal(0, 0.08), 0.35, 0.95))
    em = (1 - qm) / (1 + qm)
    phi = np.radians(pa_l + dpa)
    rows.append(dict(row=len(rows), stamp_id=g["stamp_id"], lib=g["lib"],
                     dihedral_k=k, theta_E=round(th, 6),
                     mass_e1=round(em * np.cos(2 * phi), 6),
                     mass_e2=round(em * np.sin(2 * phi), 6),
                     z_source=round(zs, 5), sigma_v_used=round(vd, 2),
                     z_l=g["z_l"], stamp_mag=g["mag"], q_light=g["q"],
                     pa_light_eff=round(pa_l, 2), dpa=round(dpa, 2)))

with open(a.out, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    w.writeheader()
    for r in rows:
        w.writerow(r)
print("manifest: %d rows (%d attempts, acc %.2f)" % (len(rows), attempts,
                                                     len(rows) / max(attempts, 1)))
print("per-bin fill (cap %d): min %d  median %d — bins <50%% cap: %d of %d"
      % (cap, fill.min(), int(np.median(fill)), (fill < 0.5 * cap).sum(), a.nbin))
th = np.array([r["theta_E"] for r in rows])
mg = np.array([r["stamp_mag"] for r in rows])
from scipy.stats import spearmanr
rho, _ = spearmanr(mg, th)
print("manifest rho(stamp mag, theta_E) = %+.2f (physical FJ channel; real ~ -0.3..-0.5)"
      % rho)
