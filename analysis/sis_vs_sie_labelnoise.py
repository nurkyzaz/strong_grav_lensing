#!/usr/bin/env python3
"""E1 - label-noise floor (reviewer concern R1). How accurately does the measured
SDSS velocity dispersion predict the true SIE Einstein radius b_SIE on the SLACS
benchmark? This is the ceiling on any sigma_v->theta_E self-consistent scheme:
the CNN cannot beat the scatter of the labels it is trained on.

theta_E^SIS = 4*pi*(sigma_v/c)^2 * (D_ls/D_s), flat LCDM (Om=0.3), compared to
b_SIE (Bolton et al. 2008). Data: tables/slacs_benchmark_kinematics.csv
(sigma_v, z_l, z_s from Bolton 2008 table4 [VizieR J/ApJ/682/964] joined to
table5 b_SIE).
"""
import csv
import numpy as np

C_KMS = 299792.458
OM, OL = 0.3, 0.7
ARCSEC = 206264.806  # rad -> arcsec

def E(z):
    return np.sqrt(OM * (1 + z) ** 3 + OL)

def Dc(z, n=2000):
    zg = np.linspace(0, z, n)
    y = 1.0 / E(zg)
    return np.sum((y[1:] + y[:-1]) * 0.5 * np.diff(zg))  # comoving dist, c/H0 units

def theta_sis(sigma, zl, zs):
    Dls_Ds = 1.0 - Dc(zl) / Dc(zs)       # flat-universe D_ls/D_s
    return 4 * np.pi * (sigma / C_KMS) ** 2 * Dls_Ds * ARCSEC

def r2(pred, true):
    return 1 - np.sum((pred - true) ** 2) / np.sum((true - true.mean()) ** 2)

def nmad(x):
    return 1.4826 * np.median(np.abs(x - np.median(x)))

rows = list(csv.DictReader(open("tables/slacs_benchmark_kinematics.csv")))
sig = np.array([float(r["sigma_v_kms"]) for r in rows])
zl = np.array([float(r["z_l"]) for r in rows])
zs = np.array([float(r["z_s"]) for r in rows])
bsie = np.array([float(r["b_SIE_arcsec"]) for r in rows])

tsis = np.array([theta_sis(s, l, u) for s, l, u in zip(sig, zl, zs)])
resid = tsis - bsie
frac = resid / bsie

print(f"E1 label-noise floor: theta_E^SIS(sigma_v) vs b_SIE   N={len(rows)} SLACS")
print(f"  cosmology: flat LCDM Om={OM}")
print(f"  bias  (mean, median)  = {resid.mean():+.3f}, {np.median(resid):+.3f} arcsec")
print(f"  scatter (std, NMAD)   = {resid.std(ddof=1):.3f}, {nmad(resid):.3f} arcsec")
print(f"  fractional (std, NMAD)= {frac.std(ddof=1)*100:.1f}%, {nmad(frac)*100:.1f}%")
print(f"  R^2(theta_SIS vs b_SIE) = {r2(tsis, bsie):+.3f}")
print(f"  Pearson r             = {np.corrcoef(tsis, bsie)[0,1]:+.3f}")
print(f"  median |frac err| > 15% failure rate = {np.mean(np.abs(frac)>0.15)*100:.0f}%")
print()
print("  Compare to the CNN on the SAME benchmark (SLACS): NMAD 0.047 arcsec, R2 0.64.")
print("  If the CNN scatter ~ this floor, the network has saturated the label physics.")
