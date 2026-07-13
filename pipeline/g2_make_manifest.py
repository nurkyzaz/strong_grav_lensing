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
ap.add_argument("--couple_shear", action="store_true",
                help="AR2: gamma_ext coupled to |dPA| (C1); default OFF")
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

# --- vectorized batch sampling with a precomputed D_ls/D_s grid (the naive
# per-draw astropy loop ran at ~1% acceptance = hours at G4 scale) ---
zgrid = np.arange(zs_lo, zs_hi + 1e-9, 0.005)
zl_arr = np.array([g["z_l"] for g in gal])
vd_arr = np.array([g["sigma_v"] for g in gal])
ve_arr = np.array([g["sigma_err"] for g in gal])
Ds = cosmo.angular_diameter_distance(zgrid).value
ratio = np.zeros((len(gal), len(zgrid)))
for gi, zl in enumerate(zl_arr):
    Dls = cosmo.angular_diameter_distance_z1z2(zl, zgrid).value
    ratio[gi] = np.where(zgrid > zl + 0.05, Dls / Ds, np.nan)
prefac = np.degrees(4 * np.pi / C_KMS ** 2) * 3600.0

# --- TEMPERED prior (pilot v3 lesson): hard bin-flattening exploits the z_s
# lever (D_ls/D_s ~3x) to fill tails, DECOUPLING theta_E from sigma_v and
# killing the FJ correlation (rho -> -0.00, gate FAIL). Instead: accept draws
# with weight (1/physical_density(theta))^alpha. alpha=1 = flat (kills FJ);
# alpha=0 = physical (peaked ~0.9", prior-pull risk). Sweep alpha and pick the
# LARGEST (flattest) whose manifest rho(mag, theta) <= RHO_REQ — eval #16
# proved exact flatness buys nothing on the real benchmark; the light channel
# is what was missing.
RHO_REQ = -0.15

# C15a/b (2026-07-13): sigma_v -> theta_E mapping corrections.
# (a) SLACS-measured normalization: sigma_fiber = 0.948 sigma_SIE (Bolton+08)
#     -> sigma_SIS = sigma_fiber / F_SIS; theta_E rises ~11% at fixed light.
# (b) 7% intrinsic stellar-vs-lensing dispersion scatter (beyond measurement
#     error), applied multiplicatively -> ~14% honest theta_E label noise.
F_SIS = 0.948
SIG_INT = 0.07


def sample_physical(nb):
    gi = rng.integers(0, len(gal), nb)
    zi = rng.integers(0, len(zgrid), nb)
    zdens = np.exp(-0.5 * ((zgrid[zi] - 0.65) / 0.15) ** 2)
    keepz = rng.random(nb) < zdens
    vd = vd_arr[gi] + rng.normal(0, 1, nb) * ve_arr[gi]
    vd = (vd / F_SIS) * (1.0 + rng.normal(0, SIG_INT, nb))  # C15a + C15b
    th = prefac * vd ** 2 * ratio[gi, zi]
    ok = keepz & np.isfinite(th) & (th >= a.tmin) & (th < a.tmax) & (vd > 50)
    return gi[ok], zi[ok], vd[ok], th[ok]


# physical theta density from a large unweighted sample
gi0, zi0, vd0, th0 = sample_physical(2000000)
hist, _ = np.histogram(th0, bins=edges)
dens = np.maximum(hist / hist.sum(), 1e-5)
mag_all = np.array([g["mag"] for g in gal])

from scipy.stats import spearmanr as _sp
alpha_pick = 0.0
for alpha in (0.8, 0.7, 0.6, 0.5, 0.4, 0.3):
    w = (1.0 / dens) ** alpha
    b0 = np.clip(((th0 - a.tmin) / (a.tmax - a.tmin) * a.nbin).astype(int), 0, a.nbin - 1)
    keep = rng.random(len(th0)) < (w[b0] / w.max())
    rho_a, _ = _sp(mag_all[gi0[keep][:20000]], th0[keep][:20000])
    frac_hi = (th0[keep] > 1.5).mean()
    frac_lo = (th0[keep] < 0.8).mean()
    print("alpha %.1f: rho %+0.2f  P(theta>1.5)=%.03f  P(theta<0.8)=%.3f"
          % (alpha, rho_a, frac_hi, frac_lo))
    if rho_a <= RHO_REQ and alpha_pick == 0.0:
        alpha_pick = alpha
alpha = alpha_pick if alpha_pick > 0 else 0.3
print("ALPHA CHOSEN: %.1f" % alpha)
wbin = ((1.0 / dens) ** alpha)
wbin = wbin / wbin.max()

B = 200000
while len(rows) < a.n and attempts < a.n * 2000:
    gi, zi, vd, th = sample_physical(B)
    attempts += B
    b_all = np.clip(((th - a.tmin) / (a.tmax - a.tmin) * a.nbin).astype(int),
                    0, a.nbin - 1)
    acc = rng.random(len(th)) < wbin[b_all]
    for j in np.where(acc)[0]:
        if len(rows) >= a.n:
            break
        b = b_all[j]
        fill[b] += 1
        g = gal[int(gi[j])]
        k = int(rng.integers(8))
        pa_l = dihedral_pa(g["pa"], k)
        dpa = float(np.clip(rng.normal(0, 10.0), -30, 30))
        if a.couple_shear:
            gam = float(min(rng.rayleigh(0.03) + 0.0012 * abs(dpa), 0.25))
            phig = float(rng.uniform(0, np.pi))
            g1 = round(gam * np.cos(2 * phig), 6)
            g2 = round(gam * np.sin(2 * phig), 6)
        qm = float(np.clip(g["q"] + rng.normal(0, 0.08), 0.35, 0.95))
        em = (1 - qm) / (1 + qm)
        phi = np.radians(pa_l + dpa)
        rows.append(dict(row=0, stamp_id=g["stamp_id"], lib=g["lib"],
                         dihedral_k=k, theta_E=round(float(th[j]), 6),
                         mass_e1=round(em * np.cos(2 * phi), 6),
                         mass_e2=round(em * np.sin(2 * phi), 6),
                         z_source=round(float(zgrid[zi[j]]), 5),
                         sigma_v_used=round(float(vd[j]), 2),
                         z_l=g["z_l"], stamp_mag=g["mag"], q_light=g["q"],
                         pa_light_eff=round(pa_l, 2), dpa=round(dpa, 2),
                         **(dict(gamma1=g1, gamma2=g2)
                            if a.couple_shear else {})))

# SHUFFLE: renders consume rows sequentially and bin-filling appends the
# hard (high-theta) bins LAST — unshuffled, a partial consumption drops the
# tail entirely (pilot v2 lesson: 16/600 renders above 1.7").
order = rng.permutation(len(rows))
rows = [rows[i] for i in order]
for i, r in enumerate(rows):
    r["row"] = i

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
print("PHYSICS SPEC: fj_channel=ON misalignment=ON(N10,clip30) "
      "q_scatter=adhoc0.08(C2-open) gamma_coupling=%s multipoles=OFF(AR3) "
      "tempered_alpha=swept" % ("ON" if a.couple_shear else "OFF(AR2)"))
