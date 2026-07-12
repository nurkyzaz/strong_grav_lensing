#!/usr/bin/env python
"""GEN4-G1b: SECOND-ROUND library-expansion target list (Nurkyz 2026-07-12:
"increase library size"). Four levers over the G1a builder:

  L1  Wider PI/program net: the full SLACS-lineage snapshot family
      (adds Auger, Shu, Marshall, Gavazzi, Sonnenfeld, Moustakas, Newton)
      and WFC3/UVIS F814W alongside ACS/WFC (UVIS 0.04"/px -> flagged for a
      resample step in the fetch builder).
  L2  BULK FOOTPRINT crossmatch: G1a matched SDSS galaxies to pointing
      CENTERS within 5"; an ACS/WFC field is ~3.4'x3.4', so every clean-sigma_v
      SDSS galaxy ANYWHERE in an archival F814W frame is harvestable. One
      bulk MAST query + one paged SDSS query + a cKDTree match replaces the
      per-target loop that made the general archive look like a dead end
      (new method, not a re-litigation: G0 tested per-target queries).
  L3  Tiered sigma_v quality (generator jitters sigma_v within sigma_err, so
      noisy measurements are usable with honest label noise):
        tier A: velDispErr < velDisp/5   (G1a "clean")
        tier B: velDispErr < velDisp/2.5 (noisy but usable)
  L4  Priority: sigma_v >= 250 first (the theta_E>1.5" tail is stamp-thin),
      then tier, then exposure time.

Exclusions: frozen benchmark + LRGDEFL1 (real_lens_labels.csv), the G1a
targets (lrgdefl2_labels.csv), and pairwise dedupe at 5".
Output: lrgdefl2b_labels.csv in the fetch driver's format + a summary table.

Run on the Mac (network-heavy):  .venv_epsf/bin/python g1b_build_targets.py
"""
import csv
import os
import time

import numpy as np
from astropy import units as u
from astropy.coordinates import SkyCoord
from astroquery.mast import Observations
from astroquery.sdss import SDSS

PROJ = "/Users/nurkyz/Desktop/LensFusion"
OUT = os.path.join(PROJ, "lrgdefl2b_labels.csv")
FIELD_R_ARCMIN = 1.55   # stay inside an ACS/WFC frame with margin
MIN_SEP_EXCL = 5.0      # arcsec
Z_RANGE = (0.05, 0.55)
VDISP_RANGE = (120, 450)

# ---------- exclusions ----------
excl = []
for fn in ("real_lens_labels.csv", "lrgdefl2_labels.csv"):
    p = os.path.join(PROJ, fn)
    for r in csv.DictReader(open(p)):
        excl.append((float(r["ra_deg"]), float(r["dec_deg"])))
excl_cat = SkyCoord([e[0] for e in excl] * u.deg, [e[1] for e in excl] * u.deg)
print("exclusion coords: %d (benchmark + LRGDEFL1 + G1a targets)" % len(excl))

# ---------- L1+L2: bulk MAST footprint inventory ----------
print("\n=== MAST bulk inventory: public F814W frames (ACS/WFC + WFC3/UVIS) ===")
frames = []   # (ra, dec, instrument, exptime, proposal_id, pi)
for instr in ("ACS/WFC", "WFC3/UVIS"):
    try:
        obs = Observations.query_criteria(
            obs_collection="HST", instrument_name=instr, filters="F814W",
            dataproduct_type="image", calib_level=3, dataRights="PUBLIC",
            t_exptime=[100, 20000])
        n0 = len(frames)
        for o in obs:
            try:
                frames.append((float(o["s_ra"]), float(o["s_dec"]), instr,
                               float(o["t_exptime"]), str(o["proposal_id"]),
                               str(o["proposal_pi"])))
            except Exception:
                continue
        print("  %s: %d usable frames" % (instr, len(frames) - n0))
    except Exception as e:
        print("  %s query failed: %s" % (instr, str(e)[:100]))
print("total frames: %d" % len(frames))
fra = np.array([f[0] for f in frames])
fdec = np.array([f[1] for f in frames])

# ---------- SDSS sigma_v pool, paged by dec stripes, both tiers ----------
print("\n=== SDSS sigma_v pool (tiers A/B), paged ===")
pool = []   # (ra, dec, z, vd, ve, tier)
dec_edges = np.arange(-15, 75.1, 5.0)
for lo, hi in zip(dec_edges[:-1], dec_edges[1:]):
    q = ("SELECT ra, dec, z, velDisp, velDispErr FROM SpecObj "
         "WHERE class='GALAXY' AND zWarning=0 "
         "AND z BETWEEN %.2f AND %.2f "
         "AND velDisp BETWEEN %d AND %d AND velDispErr > 0 "
         "AND velDispErr < velDisp/2.5 "
         "AND dec BETWEEN %.1f AND %.1f"
         % (Z_RANGE[0], Z_RANGE[1], VDISP_RANGE[0], VDISP_RANGE[1], lo, hi))
    for attempt in range(3):
        try:
            t = SDSS.query_sql(q, timeout=180)
            if t is not None:
                for r in t:
                    vd, ve = float(r["velDisp"]), float(r["velDispErr"])
                    tier = "A" if ve < vd / 5.0 else "B"
                    pool.append((float(r["ra"]), float(r["dec"]),
                                 float(r["z"]), vd, ve, tier))
            break
        except Exception as e:
            if attempt == 2:
                print("  dec [%.0f,%.0f] failed: %s" % (lo, hi, str(e)[:80]))
            time.sleep(5)
    print("  dec [%+.0f,%+.0f]: pool now %d" % (lo, hi, len(pool)), flush=True)
print("sigma_v pool: %d galaxies (tier A %d / tier B %d)"
      % (len(pool), sum(1 for p in pool if p[5] == "A"),
         sum(1 for p in pool if p[5] == "B")))

# ---------- footprint crossmatch (cKDTree on unit sphere) ----------
print("\n=== footprint crossmatch ===")
from scipy.spatial import cKDTree


def unit(ra, dec):
    ra, dec = np.radians(ra), np.radians(dec)
    return np.column_stack([np.cos(dec) * np.cos(ra),
                            np.cos(dec) * np.sin(ra), np.sin(dec)])


tree = cKDTree(unit(fra, fdec))
gxyz = unit(np.array([p[0] for p in pool]), np.array([p[1] for p in pool]))
chord = 2 * np.sin(np.radians(FIELD_R_ARCMIN / 60.0) / 2)
hits = tree.query_ball_point(gxyz, chord)

cand = []
for gi, fr_idx in enumerate(hits):
    if not fr_idx:
        continue
    best = max(fr_idx, key=lambda i: frames[i][3])   # deepest frame
    ra, dec, z, vd, ve, tier = pool[gi]
    cand.append(dict(ra=ra, dec=dec, z=z, vd=vd, ve=ve, tier=tier,
                     instr=frames[best][2], expt=frames[best][3],
                     prop=frames[best][4], pi=frames[best][5]))
print("galaxies inside >=1 usable F814W frame: %d" % len(cand))

# ---------- exclusions + self-dedupe ----------
if cand:
    cc = SkyCoord([c["ra"] for c in cand] * u.deg, [c["dec"] for c in cand] * u.deg)
    dmin = np.array([cc[i].separation(excl_cat).arcsec.min() for i in range(len(cand))])
    cand = [c for c, d in zip(cand, dmin) if d > MIN_SEP_EXCL]
    print("after benchmark/LRGDEFL/G1a exclusions: %d" % len(cand))
    cc = SkyCoord([c["ra"] for c in cand] * u.deg, [c["dec"] for c in cand] * u.deg)
    keep, used = [], np.zeros(len(cand), bool)
    order = np.argsort([-c["vd"] for c in cand])
    for i in order:
        if used[i]:
            continue
        used[cc[i].separation(cc).arcsec < MIN_SEP_EXCL] = True
        keep.append(cand[i])
    cand = keep
    print("after 5\" self-dedupe: %d" % len(cand))

# ---------- L4 priority + output ----------
cand.sort(key=lambda c: (-(c["vd"] >= 250), c["tier"], -c["expt"]))
with open(OUT, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["name", "ra_deg", "dec_deg", "theta_E_pub",
                                      "q_pub", "survey", "src_table"])
    w.writeheader()
    for i, c in enumerate(cand):
        w.writerow(dict(name="G4B_%05d" % i, ra_deg="%.5f" % c["ra"],
                        dec_deg="%.5f" % c["dec"], theta_E_pub="0.0", q_pub="0.0",
                        survey="LRGDEFL2B",
                        src_table="tier%s|vd=%.0f+-%.0f|z=%.3f|%s|%ss|P%s"
                                  % (c["tier"], c["vd"], c["ve"], c["z"],
                                     c["instr"].replace("/", ""), int(c["expt"]),
                                     c["prop"])))
print("\nwrote %s: %d targets" % (OUT, len(cand)))
vds = np.array([c["vd"] for c in cand])
print("sigma_v: median %.0f  >=250: %d  >=300: %d" % (np.median(vds) if len(vds) else 0,
      (vds >= 250).sum(), (vds >= 300).sum()))
for tier in "AB":
    print("tier %s: %d" % (tier, sum(1 for c in cand if c["tier"] == tier)))
print("WFC3/UVIS (needs 0.04->0.05 resample in builder): %d"
      % sum(1 for c in cand if "UVIS" in c["instr"]))
