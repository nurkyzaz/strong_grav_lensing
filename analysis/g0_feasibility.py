#!/usr/bin/env python
"""GEN4-G0 item 3: library-expansion feasibility.
(a) Size of the SDSS spectroscopic parent pool (sigma_v 120-350, clean errors).
(b) HST-archival imaging of SDSS-parent targets via the Bolton/SLACS-lineage
    snapshot programs (PI search) — these imaged SDSS spectroscopic candidates,
    most of which are NON-lenses = exactly our stamp source.
(c) Sample-based estimate of general HST-archive coverage of the pool.
Best-effort: each part guarded; partial results still useful.
"""
import numpy as np
from astropy import units as u
from astropy.coordinates import SkyCoord
from astroquery.sdss import SDSS

print("=== (a) SDSS spectroscopic parent pool ===")
try:
    q = ("SELECT COUNT(*) AS n FROM SpecObj WHERE class='GALAXY' "
         "AND zWarning=0 AND z BETWEEN 0.05 AND 0.5 "
         "AND velDisp BETWEEN 120 AND 350 AND velDispErr > 0 "
         "AND velDispErr < velDisp/5")
    t = SDSS.query_sql(q, timeout=120)
    print("galaxies with clean sigma_v in [120,350], z in [0.05,0.5]: %d" % t["n"][0])
except Exception as e:
    print("SDSS SQL failed:", str(e)[:100])

print("\n=== (b) SLACS-lineage HST snapshot programs (PI Bolton/Treu/Koopmans) ===")
try:
    from astroquery.mast import Observations
    n_by_pi = {}
    for pi in ("Bolton", "Treu", "Koopmans", "Brownstein"):
        try:
            obs = Observations.query_criteria(
                obs_collection="HST",
                instrument_name=["ACS/WFC", "WFC3/UVIS"],
                proposal_pi="*%s*" % pi)
            if len(obs):
                tgt = set(zip(np.round(obs["s_ra"], 3), np.round(obs["s_dec"], 3)))
                n_by_pi[pi] = (len(obs), len(tgt))
                print("  PI *%s*: %d observations, ~%d distinct pointings"
                      % (pi, len(obs), len(tgt)))
        except Exception as e:
            print("  PI %s query failed: %s" % (pi, str(e)[:80]))
except Exception as e:
    print("MAST unavailable:", str(e)[:100])

print("\n=== (c) sample-based general-archive coverage of the pool ===")
try:
    from astroquery.mast import Observations
    q = ("SELECT TOP 120 s.ra, s.dec FROM SpecObj s WHERE s.class='GALAXY' "
         "AND s.zWarning=0 AND s.z BETWEEN 0.05 AND 0.5 "
         "AND s.velDisp BETWEEN 120 AND 350 AND s.velDispErr > 0 "
         "AND s.velDispErr < s.velDisp/5 ORDER BY NEWID()")
    t = SDSS.query_sql(q, timeout=120)
    hits = 0
    for i, row in enumerate(t):
        try:
            co = SkyCoord(float(row["ra"]) * u.deg, float(row["dec"]) * u.deg)
            obs = Observations.query_criteria(
                coordinates=co, radius="0.5 arcmin",
                obs_collection="HST", dataproduct_type="image",
                instrument_name=["ACS/WFC", "WFC3/UVIS", "WFPC2/WFC"])
            if len(obs):
                hits += 1
        except Exception:
            pass
        if (i + 1) % 30 == 0:
            print("  %d/%d checked, hits so far %d" % (i + 1, len(t), hits))
    print("HST high-res imaging coverage: %d / %d = %.1f%% of random pool members"
          % (hits, len(t), 100 * hits / max(len(t), 1)))
except Exception as e:
    print("sample estimate failed:", str(e)[:100])
