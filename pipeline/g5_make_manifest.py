#!/usr/bin/env python
"""GEN5 (C21): z-MIGRATION population manifest + AR3 isophote-anchored
multipoles — one row per render attempt, extending g2_make_manifest.py.

Each row: a real G1b library galaxy (stamp = light; measured sigma_v = mass,
C15-corrected) MIGRATED to a target-population redshift z_new drawn from the
Rung 0 deflector distribution (measured 2026-07-14: z_l q05/50/95 =
0.39/0.79/1.38; lognormal med 0.79, sigma_ln 0.36, clipped [0.30, 1.50],
forced >= z_orig + 0.02). The stamp paste then shrinks by the angular-
diameter ratio and dims by Tolman surface-brightness dimming:

    mig_scale = D_A(z_orig) / D_A(z_new)          (zoom factor < 1)
    mig_sb    = ((1 + z_orig) / (1 + z_new))**4   (per-pixel SB factor)

(zoom preserves per-pixel SB, so total flux transforms by mig_scale^2 *
mig_sb = (D_L(z_orig)/D_L(z_new))^2 — exactly the luminosity-distance flux
ratio. sigma_v is intrinsic -> the FJ channel survives; F814W rest-frame
band proxy DISCLOSED, improves toward z~0.8.)

theta_E is computed at (z_new, z_s_new) with z_s ~ N(2.0, 0.6) truncated to
[z_new + 0.20, 3.5] (Rung 0 source redshifts unpublished — DISCLOSED draw).

AR3 multipoles (isophote-anchored, the novelty): for stamps with clean
isophote fits (flag_pair = flag_iso_bad = 0 in g1b_kinematics_v1.csv), the
lenstronomy MULTIPOLE amplitude is set so the CONVERGENCE contour deviation
equals the MEASURED light-isophote deviation. For SIS kappa = theta_E/(2r)
plus kappa_m = a_m cos(m(phi-phi_m))/(2r) (Xu+2013 B12, lenstronomy conv.),
the iso-convergence contour perturbation is delta_r/r = a_m/theta_E, so

    mult{m}_a   = iso_m{m} * theta_E        (clipped at 0.10 * theta_E)
    mult{m}_phi = PA_light_eff(dihedral) + phase_m,
    phase_m     = atan2(b_m, a_m)/m         (negated under flips, k>=4)

(the measured a_k/b_k are harmonic coefficients around the ellipse
parametrisation, used as the polar-contour phase — second-order difference
at q~0.86, disclosed). Flagged stamps get mult a = 0 (pure PEMD+shear).

Usage: g5_make_manifest.py --kine g1b_kinematics_v1.csv --n 1400 --seed 950
       [--tmin 0.15 --tmax 3.70] [--couple_shear] --out m.csv
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
ap.add_argument("--seed", type=int, default=950)
ap.add_argument("--out", required=True)
ap.add_argument("--tmin", type=float, default=0.15)
ap.add_argument("--tmax", type=float, default=3.70)
ap.add_argument("--nbin", type=int, default=37)
ap.add_argument("--zl_med", type=float, default=0.79,
                help="target z_l lognormal median (Rung 0 measured)")
ap.add_argument("--zl_sln", type=float, default=0.36,
                help="target z_l lognormal sigma_ln")
ap.add_argument("--zl_max", type=float, default=1.50)
ap.add_argument("--zl_min", type=float, default=0.30)
ap.add_argument("--mult_cap", type=float, default=0.10,
                help="cap on mult_a as a fraction of theta_E")
ap.add_argument("--evo_q", type=float, default=1.2,
                help="passive luminosity evolution of the deflector, mag per "
                     "unit z (Faber+2007 red sequence ~1.2): the migrated "
                     "stamp BRIGHTENS by Q*(z_new-z_orig) mag on top of the "
                     "cosmological dimming — LRGs at z~0.8 are younger and "
                     "intrinsically brighter. Set 0 to disable. PHYSICS "
                     "PENDING CONFIRMATION (Nurkyz/Brian), gate-arbitrated")
ap.add_argument("--couple_shear", action="store_true",
                help="AR2: gamma_ext coupled to |dPA| (C1); default OFF")
ap.add_argument("--src_off_lo", type=float, default=0.0,
                help="C41: source-plane offset as a fraction of theta_E, lower "
                     "bound. Emits per-row source_cx/source_cy = beta*(cos,sin)phi "
                     "with beta = theta_E*U(src_off_lo,src_off_hi). Scaling the "
                     "offset WITH theta_E makes arcs partial at every theta_E (a "
                     "fixed 0.25\" offset left large-theta systems near-aligned -> "
                     "full rings). 0/0 (default) => columns emitted as 0 (GEN4/prior "
                     "behaviour: the config's fixed U(+-0.25) offset still applies).")
ap.add_argument("--src_off_hi", type=float, default=0.0,
                help="C41: upper bound of the theta_E-fraction source offset. "
                     "Real Q1 arcs are typically partial (~25-50%% of a ring); "
                     "~0.35-0.75 of theta_E reproduces that. See --src_off_lo.")
ap.add_argument("--match_theta", default="",
                help="path to a .npy of TARGET theta_E values (e.g. real Q1 "
                     "theta_E_pub). Reweight the theta_E distribution to MATCH the "
                     "observed one instead of tempering toward flat (Nurkyz "
                     "2026-08-02: our upper tail was too heavy vs real Q1).")
a = ap.parse_args()
rng = np.random.default_rng(a.seed)

gal = []
for fn in a.kine:
    for r in csv.DictReader(open(fn)):
        try:
            vd, ve, z = float(r["sigma_v"]), float(r["sigma_err"]), float(r["z_l"])
            if not (50 < vd < 500 and z > 0.02):
                continue
            iso_ok = (r.get("flag_iso_bad", "1") == "0"
                      and r.get("flag_pair", "1") == "0"
                      and r.get("iso_m3", "") != "")
            g = dict(stamp_id=int(r["stamp_id"]), lib=fn, sigma_v=vd,
                     sigma_err=min(ve, vd * 0.2), z_l=z,
                     mag=float(r["mag"]), q=float(r["q"]),
                     pa=float(r["pa_deg"]), iso_ok=iso_ok)
            if iso_ok:
                g.update(m3=float(r["iso_m3"]), m4=float(r["iso_m4"]),
                         ph3=float(np.arctan2(float(r["iso_b3"]),
                                              float(r["iso_a3"]))) / 3.0,
                         ph4=float(np.arctan2(float(r["iso_b4"]),
                                              float(r["iso_a4"]))) / 4.0)
            else:
                g.update(m3=0.0, m4=0.0, ph3=0.0, ph4=0.0)
            gal.append(g)
        except (ValueError, KeyError):
            pass
n_iso = sum(g["iso_ok"] for g in gal)
print("library galaxies usable: %d (multipole-anchored %d, zeroed %d)"
      % (len(gal), n_iso, len(gal) - n_iso))


def dihedral_pa(pa, k):
    p = pa + 90.0 * (k % 4)
    if k >= 4:
        p = 180.0 - p
    return p % 180.0


# --- flat-LCDM distance machinery on a fine grid (z_l AND z_s both vary
# per draw now, so the per-galaxy Dls/Ds precompute of g2 doesn't apply;
# for a flat universe D_ls = (D_C(zs) - D_C(zl))/(1+zs) exactly) ---
ZG = np.arange(0.0, 3.51, 0.005)
DC = cosmo.comoving_distance(ZG).value
DA = DC / (1.0 + ZG)


def zidx(z):
    return np.clip(np.round(np.asarray(z) / 0.005).astype(int), 0, len(ZG) - 1)


prefac = np.degrees(4 * np.pi / C_KMS ** 2) * 3600.0
RHO_REQ = -0.15
F_SIS = 0.948   # C15a
SIG_INT = 0.07  # C15b

zl_arr = np.array([g["z_l"] for g in gal])
vd_arr = np.array([g["sigma_v"] for g in gal])
ve_arr = np.array([g["sigma_err"] for g in gal])
mag_all = np.array([g["mag"] for g in gal])


def sample_physical(nb):
    gi = rng.integers(0, len(gal), nb)
    zl0 = zl_arr[gi]
    # target z_l: lognormal(med, sln) clipped; forced above the stamp's own z
    zl_new = np.exp(np.log(a.zl_med) + rng.normal(0, a.zl_sln, nb))
    zl_new = np.clip(zl_new, a.zl_min, a.zl_max)
    zl_new = np.maximum(zl_new, zl0 + 0.02)
    # source z: N(2.0,0.6) truncated above zl_new+0.2 (vector truncnorm)
    lo = (np.maximum(zl_new + 0.20, 0.7) - 2.0) / 0.6
    hi = (3.5 - 2.0) / 0.6
    zs = truncnorm.rvs(lo, hi, loc=2.0, scale=0.6,
                       random_state=rng.integers(1 << 31))
    vd = vd_arr[gi] + rng.normal(0, 1, nb) * ve_arr[gi]
    vd = (vd / F_SIS) * (1.0 + rng.normal(0, SIG_INT, nb))  # C15a + C15b
    il, isrc = zidx(zl_new), zidx(zs)
    Dls = (DC[isrc] - DC[il]) / (1.0 + ZG[isrc])
    Ds = DA[isrc]
    th = prefac * vd ** 2 * np.where(Dls > 0, Dls / Ds, np.nan)
    ok = np.isfinite(th) & (th >= a.tmin) & (th < a.tmax) & (vd > 50)
    return gi[ok], zl_new[ok], zs[ok], vd[ok], th[ok]


edges = np.linspace(a.tmin, a.tmax, a.nbin + 1)
cap = int(np.ceil(a.n / a.nbin))
fill = np.zeros(a.nbin, int)
rows = []
attempts = 0

gi0, zl0_, zs0_, vd0, th0 = sample_physical(2000000)
hist, _ = np.histogram(th0, bins=edges)
dens = np.maximum(hist / hist.sum(), 1e-5)

from scipy.stats import spearmanr as _sp
if a.match_theta:
    # Nurkyz 2026-08-02: match the OBSERVED theta_E distribution (real Q1) rather
    # than tempering toward flat. Reweight the physical density to the target hist.
    tgt = np.load(a.match_theta)
    tgt = tgt[np.isfinite(tgt) & (tgt >= a.tmin) & (tgt < a.tmax)]
    th_hist, _ = np.histogram(tgt, bins=edges)
    th_hist = th_hist / max(th_hist.sum(), 1)
    wbin = th_hist / dens                          # physical -> observed
    wbin = wbin / wbin.max()
    b0 = np.clip(((th0 - a.tmin) / (a.tmax - a.tmin) * a.nbin).astype(int),
                 0, a.nbin - 1)
    keep = rng.random(len(th0)) < wbin[b0]
    rho_a, _ = _sp(mag_all[gi0[keep][:20000]], th0[keep][:20000])
    alpha = 0.0
    print("MATCH_THETA: reweighting theta_E to %s (target N=%d); "
          "rho(mag,theta)=%+.2f  P(theta>1.5)=%.3f"
          % (a.match_theta, len(tgt), rho_a, (th0[keep] > 1.5).mean()))
else:
    alpha_pick = 0.0
    for alpha in (0.8, 0.7, 0.6, 0.5, 0.4, 0.3):
        w = (1.0 / dens) ** alpha
        b0 = np.clip(((th0 - a.tmin) / (a.tmax - a.tmin) * a.nbin).astype(int),
                     0, a.nbin - 1)
        keep = rng.random(len(th0)) < (w[b0] / w.max())
        rho_a, _ = _sp(mag_all[gi0[keep][:20000]], th0[keep][:20000])
        print("alpha %.1f: rho %+0.2f  P(theta>1.5)=%.3f  P(theta<0.8)=%.3f"
              % (alpha, rho_a, (th0[keep] > 1.5).mean(), (th0[keep] < 0.8).mean()))
        if rho_a <= RHO_REQ and alpha_pick == 0.0:
            alpha_pick = alpha
    alpha = alpha_pick if alpha_pick > 0 else 0.3
    print("ALPHA CHOSEN: %.1f" % alpha)
    wbin = (1.0 / dens) ** alpha
    wbin = wbin / wbin.max()

B = 200000
while len(rows) < a.n and attempts < a.n * 2000:
    gi, zln, zs, vd, th = sample_physical(B)
    attempts += B
    b_all = np.clip(((th - a.tmin) / (a.tmax - a.tmin) * a.nbin).astype(int),
                    0, a.nbin - 1)
    acc = rng.random(len(th)) < wbin[b_all]
    for j in np.where(acc)[0]:
        if len(rows) >= a.n:
            break
        fill[b_all[j]] += 1
        g = gal[int(gi[j])]
        k = int(rng.integers(8))
        pa_l = dihedral_pa(g["pa"], k)
        dpa = float(np.clip(rng.normal(0, 10.0), -30, 30))
        extra = {}
        if a.couple_shear:
            gam = float(min(rng.rayleigh(0.03) + 0.0012 * abs(dpa), 0.25))
            phig = float(rng.uniform(0, np.pi))
            extra = dict(gamma1=round(gam * np.cos(2 * phig), 6),
                         gamma2=round(gam * np.sin(2 * phig), 6))
        qm = float(np.clip(g["q"] + rng.normal(0, 0.08), 0.35, 0.95))
        em = (1 - qm) / (1 + qm)
        phi = np.radians(pa_l + dpa)
        thj = float(th[j])
        sgn = -1.0 if k >= 4 else 1.0
        pa_rad = np.radians(pa_l)
        # iso_m3/iso_m4 are moduli (>=0); orientation incl. boxy-vs-disky is
        # carried entirely by the atan2(b,a)/m phases
        m3a = min(g["m3"] * thj, a.mult_cap * thj)
        m4a = min(g["m4"] * thj, a.mult_cap * thj)
        ph4 = g["ph4"]
        # C41: theta_E-scaled source offset -> partial arcs at every theta_E
        if a.src_off_hi > 0:
            beta = thj * float(rng.uniform(a.src_off_lo, a.src_off_hi))
            phib = float(rng.uniform(0, 2 * np.pi))
            src_cx = round(beta * np.cos(phib), 6)
            src_cy = round(beta * np.sin(phib), 6)
        else:
            src_cx = src_cy = 0.0
        il0, iln = zidx(g["z_l"]), zidx(float(zln[j]))
        mig_scale = float(DA[il0] / DA[iln])
        mig_sb = float(((1.0 + g["z_l"]) / (1.0 + float(zln[j]))) ** 4
                       * 10.0 ** (0.4 * a.evo_q * (float(zln[j]) - g["z_l"])))
        rows.append(dict(row=0, stamp_id=g["stamp_id"], lib=g["lib"],
                         dihedral_k=k, theta_E=round(thj, 6),
                         mass_e1=round(em * np.cos(2 * phi), 6),
                         mass_e2=round(em * np.sin(2 * phi), 6),
                         z_source=round(float(zs[j]), 5),
                         sigma_v_used=round(float(vd[j]), 2),
                         z_l=g["z_l"], z_l_new=round(float(zln[j]), 4),
                         mig_scale=round(mig_scale, 5),
                         mig_sb=round(mig_sb, 6),
                         mult3_a=round(m3a, 6),
                         mult3_phi=round(float(pa_rad + sgn * g["ph3"]), 6),
                         mult4_a=round(m4a, 6),
                         mult4_phi=round(float(pa_rad + sgn * ph4), 6),
                         stamp_mag=g["mag"],
                         stamp_mag_mig=round(g["mag"] - 2.5 * np.log10(
                             mig_scale ** 2 * mig_sb), 3),
                         q_light=g["q"],
                         source_cx=src_cx, source_cy=src_cy,
                         pa_light_eff=round(pa_l, 2), dpa=round(dpa, 2),
                         **extra))

order = rng.permutation(len(rows))
rows = [rows[i] for i in order]
for i, r in enumerate(rows):
    r["row"] = i

with open(a.out, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    w.writeheader()
    for r in rows:
        w.writerow(r)
print("manifest: %d rows (%d attempts, acc %.4f)"
      % (len(rows), attempts, len(rows) / max(attempts, 1)))
print("per-bin fill (cap %d): min %d  median %d — bins <50%% cap: %d of %d"
      % (cap, fill.min(), int(np.median(fill)), (fill < 0.5 * cap).sum(), a.nbin))
th = np.array([r["theta_E"] for r in rows])
mg = np.array([r["stamp_mag"] for r in rows])
zn = np.array([r["z_l_new"] for r in rows])
sc = np.array([r["mig_scale"] for r in rows])
m3 = np.array([r["mult3_a"] for r in rows])
m4 = np.array([r["mult4_a"] for r in rows])
from scipy.stats import spearmanr
rho, _ = spearmanr(mg, th)
mgm = np.array([r["stamp_mag_mig"] for r in rows])
rho_mig, _ = spearmanr(mgm, th)
print("manifest rho(ORIG mag, theta_E) = %+.2f (bookkeeping only)" % rho)
print("manifest rho(MIGRATED mag, theta_E) = %+.2f (the FJ channel the "
      "renders carry; real SLACS ~ -0.3..-0.5)" % rho_mig)
print("z_l_new q05/50/95 = %s (target 0.39/0.79/1.38)"
      % np.percentile(zn, [5, 50, 95]).round(2))
print("mig_scale q05/50/95 = %s | theta q05/50/95 = %s"
      % (np.percentile(sc, [5, 50, 95]).round(3),
         np.percentile(th, [5, 50, 95]).round(2)))
print("multipoles: nonzero %d/%d | mult4_a med %.4f (of theta med %.2f)"
      % (int((m4 > 0).sum()), len(rows), float(np.median(m4[m4 > 0]))
         if (m4 > 0).any() else 0.0, float(np.median(th))))

import json as _json
SPEC = dict(
    spec_version="C10v3-gen5",
    fj_channel="ON (measured sigma_v -> theta_E, SIS)",
    c15a_sigma_norm="ON (sigma_SIS = sigma_fiber/%.3f)" % F_SIS,
    c15b_intrinsic_scatter="ON (%.0f%% multiplicative)" % (100 * SIG_INT),
    misalignment="ON (dPA ~ N(0,10deg), clip +-30)",
    q_scatter=("AD-HOC (q_light + N(0,0.08); C2 data source RESOLVED "
               "Zenodo 6104823 — FIT REQUIRED before full generation)"),
    gamma_coupling=("ON (AR2: rayleigh(0.03) + 0.0012|dPA|, cap 0.25)"
                    if a.couple_shear else "OFF"),
    multipoles=("ON (AR3: isophote-anchored m=3,4; a_m = iso_amp*theta_E, "
                "cap %.2f*theta_E; anchored %d/%d galaxies, rest zeroed)"
                % (a.mult_cap, n_iso, len(gal))),
    z_migration=("ON (C21: z_l -> lognormal(med %.2f, sln %.2f) clip "
                 "[%.2f,%.2f]; shrink D_A ratio, dim (1+z)^4 x passive-evo "
                 "brightening Q=%.1f mag/z [Faber+2007, PENDING CONFIRM]; "
                 "z_s ~ N(2.0,0.6) trunc [zl+0.2, 3.5] DISCLOSED)"
                 % (a.zl_med, a.zl_sln, a.zl_min, a.zl_max, a.evo_q)),
    arc_poisson="COMBINE-STAGE (AR1 via hybrid_combine --arc_poisson)",
    source_dimming="CONFIG-STAGE (Gen5HighZSource: Newton mags + DL/K dimming z_ref 0.65 -> row z_s; sbatch greps the ACTIVE banner)",
    companion_dimming="COMBINE-STAGE (inject_companions dim = row mig_sb)",
    slope_sigma_coupling="OFF (AR6 not implemented)",
    los_structure="OFF (AR7 deferred, C6 ruling needed)",
    theta_range=[a.tmin, a.tmax],
    tempered_alpha=float(alpha), manifest_rho_mag_theta=float(round(rho, 3)),
    manifest_rho_migmag_theta=float(round(rho_mig, 3)),
    n_rows=len(rows), seed=int(a.seed), kine_files=list(a.kine),
)
spec_fn = a.out + ".physics_spec.json"
with open(spec_fn, "w") as f:
    _json.dump(SPEC, f, indent=1)
print("PHYSICS SPEC (C10, sidecar %s):" % spec_fn)
for k, v in SPEC.items():
    print("  %-24s %s" % (k, v))
