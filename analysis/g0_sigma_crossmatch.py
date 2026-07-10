#!/usr/bin/env python
"""GEN4-G0 item 1: SDSS spectroscopic crossmatch for the LRGDEFL deflector
targets (84 SLACS-extension non-lens LRGs) -> velocity dispersion + redshift
per stamp, and the implied SIS theta_E range for the SLACS source population.
Writes g0_stamp_kinematics.csv next to this script.
"""
import csv
import os
import sys
import numpy as np
from astropy import units as u
from astropy.coordinates import SkyCoord
from astropy.cosmology import FlatLambdaCDM
from astroquery.sdss import SDSS

HERE = os.path.dirname(os.path.abspath(__file__))
IN = os.path.join(HERE, "lrg_deflector_labels.csv")
OUT = os.path.join(HERE, "g0_stamp_kinematics.csv")
cosmo = FlatLambdaCDM(H0=70, Om0=0.3)
C_KMS = 299792.458

rows = list(csv.DictReader(open(IN)))
print("targets:", len(rows))
out = []
for i, r in enumerate(rows):
    co = SkyCoord(float(r["ra_deg"]) * u.deg, float(r["dec_deg"]) * u.deg)
    rec = dict(name=r["name"], ra=r["ra_deg"], dec=r["dec_deg"],
               z=np.nan, velDisp=np.nan, velDispErr=np.nan)
    try:
        t = SDSS.query_region(co, radius=3 * u.arcsec, spectro=True,
                              specobj_fields=["z", "velDisp", "velDispErr",
                                              "class", "zWarning"])
        if t is not None and len(t):
            best = t[0]
            rec.update(z=float(best["z"]), velDisp=float(best["velDisp"]),
                       velDispErr=float(best["velDispErr"]))
    except Exception as e:
        rec["err"] = str(e)[:60]
    out.append(rec)
    if (i + 1) % 20 == 0:
        print("  %d/%d queried" % (i + 1, len(rows)))

with open(OUT, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["name", "ra", "dec", "z", "velDisp",
                                      "velDispErr", "err"], extrasaction="ignore")
    w.writeheader()
    for r in out:
        w.writerow(r)

vd = np.array([r["velDisp"] for r in out])
zl = np.array([r["z"] for r in out])
good = np.isfinite(vd) & (vd > 50) & (vd < 500)
print("\nSDSS sigma_v found for %d / %d targets" % (good.sum(), len(out)))
if good.sum():
    print("sigma_v: median %.0f, 16-84%% [%.0f, %.0f], range [%.0f, %.0f] km/s"
          % (np.median(vd[good]), np.percentile(vd[good], 16),
             np.percentile(vd[good], 84), vd[good].min(), vd[good].max()))
    print("z_l: median %.3f, range [%.3f, %.3f]"
          % (np.median(zl[good]), zl[good].min(), zl[good].max()))
    for zs in (0.6, 0.8):
        ok = good & (zl < zs - 0.05)
        Ds = cosmo.angular_diameter_distance(zs)
        Dls = cosmo.angular_diameter_distance_z1z2(zl[ok], zs)
        thE = (4 * np.pi * (vd[ok] / C_KMS) ** 2 * (Dls / Ds).value
               * u.rad).to(u.arcsec).value
        print("implied SIS theta_E @ z_s=%.1f: median %.2f\", 16-84%% [%.2f, %.2f], "
              "range [%.2f, %.2f]  (N=%d)"
              % (zs, np.median(thE), np.percentile(thE, 16),
                 np.percentile(thE, 84), thE.min(), thE.max(), ok.sum()))
print("wrote", OUT)
