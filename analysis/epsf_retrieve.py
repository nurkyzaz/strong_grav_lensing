#!/usr/bin/env python
"""
epsf_retrieve.py -- retrieve STScI focus-diverse ACS/WFC F814W ePSFs
(ACS ISR 2018-08 / ISR 2023-06, acspsf.stsci.edu) for two pools:

  --mode benchmark : ePSFs matched to the actual exposures of the frozen
                     real-lens benchmark (rootnames resolved from MAST by the
                     coordinates in real_lens_labels.csv).
  --mode broad     : a pool of public archival ACS/WFC F814W exposures that
                     EXCLUDES the benchmark (any obs within --excl-radius of a
                     benchmark target is dropped). For the PSF-source ablation:
                     "benchmark-matched PSFs" vs "broad real-PSF pool".

Design rationale (logged in PAPER_PLAN.md / DECISIONS_LOG.md 2026-07-05):
benchmark-matched ePSFs are focus-matched to the test images (best realism,
but open to a circularity criticism -- the PSF is instrument state, not label
information, yet a referee may still ask); the broad pool proves the result
does not depend on having seen the benchmark exposures' instrument state.

Run from the project folder on the Mac (NOT the cluster):
  .venv_epsf/bin/python epsf_retrieve.py --mode benchmark --limit 3   # smoke
  .venv_epsf/bin/python epsf_retrieve.py --mode benchmark
  .venv_epsf/bin/python epsf_retrieve.py --mode broad --n 60

Output: epsf_library/<mode>/<rootname>-STDPBF_*.fits + manifest_<mode>.csv
(one row per exposure: rootname, source target/window, ra, dec, date, exptime,
proposal, status). Re-runs skip already-downloaded rootnames.
"""
import argparse
import glob
import os
import sys
import warnings

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

HERE = os.path.dirname(os.path.abspath(__file__))
LABELS = os.path.join(HERE, "real_lens_labels.csv")
OUTROOT = os.path.join(HERE, "epsf_library")


def flc_rootnames_for_coord(ra, dec, radius_arcsec=15.0):
    """All ACS/WFC F814W FLC exposure rootnames covering (ra, dec)."""
    from astroquery.mast import Observations
    from astropy.coordinates import SkyCoord
    import astropy.units as u

    coord = SkyCoord(ra, dec, unit="deg")
    try:
        obs = Observations.query_criteria(
            coordinates=coord, radius=radius_arcsec * u.arcsec,
            obs_collection="HST", instrument_name="ACS/WFC",
            filters="F814W", dataproduct_type="image")
    except Exception as e:
        print(f"    [query failed: {e}]")
        return []
    if len(obs) == 0:
        return []
    rows = []
    try:
        prods = Observations.get_product_list(obs)
    except Exception as e:
        print(f"    [product list failed: {e}]")
        return []
    m = prods["productSubGroupDescription"] == "FLC"
    for fn in prods["productFilename"][m]:
        root = str(fn).split("_")[0].lower()
        if len(root) == 9 and root[0] == "j":
            rows.append(root)
    # attach obs metadata (date/exptime/proposal) by matching obs_id prefix
    meta = {}
    for o in obs:
        oid = str(o["obs_id"]).lower()
        meta[oid] = dict(t_min=float(o["t_min"]) if o["t_min"] else np.nan,
                         exptime=float(o["t_exptime"]) if o["t_exptime"] else np.nan,
                         proposal=str(o["proposal_id"]))
    out = []
    for r in sorted(set(rows)):
        # obs_id for HST is usually the association (first 6 chars shared)
        match = next((v for k, v in meta.items() if k[:6] == r[:6]), {})
        out.append((r, match.get("t_min", np.nan), match.get("exptime", np.nan),
                    match.get("proposal", "")))
    return out


def broad_pool(n, bench_coords, excl_radius_arcmin=2.0, seed=0):
    """Random public ACS/WFC F814W exposures, excluding benchmark fields."""
    from astroquery.mast import Observations
    from astropy.coordinates import SkyCoord
    import astropy.units as u
    from astropy.time import Time

    rng = np.random.default_rng(seed)
    bench = SkyCoord([c[0] for c in bench_coords],
                     [c[1] for c in bench_coords], unit="deg")
    picked = []
    tried_windows = 0
    # sample random 30-day windows across the ACS/WFC F814W archive era
    while len(picked) < n and tried_windows < 40:
        tried_windows += 1
        year = rng.integers(2003, 2023)
        doy = rng.integers(1, 335)
        t0 = Time(f"{year}:{int(doy):03d}:00:00:00", format="yday").mjd
        try:
            obs = Observations.query_criteria(
                obs_collection="HST", instrument_name="ACS/WFC",
                filters="F814W", dataproduct_type="image",
                t_min=[t0, t0 + 30])
        except Exception as e:
            print(f"  [window {year}-{doy} query failed: {e}]")
            continue
        if len(obs) == 0:
            continue
        idx = rng.permutation(len(obs))
        for i in idx[:8]:  # a few per window -> diversity across epochs
            o = obs[int(i)]
            try:
                c = SkyCoord(float(o["s_ra"]), float(o["s_dec"]), unit="deg")
            except Exception:
                continue
            if bench.separation(c).arcmin.min() < excl_radius_arcmin:
                continue  # too close to a benchmark lens -> excluded
            try:
                prods = Observations.get_product_list(o)
            except Exception:
                continue
            m = prods["productSubGroupDescription"] == "FLC"
            roots = sorted({str(fn).split("_")[0].lower()
                            for fn in prods["productFilename"][m]})
            roots = [r for r in roots if len(r) == 9 and r[0] == "j"]
            if not roots:
                continue
            r = roots[int(rng.integers(len(roots)))]  # one exposure per obs
            picked.append((r, f"window_{year}_{int(doy):03d}",
                           float(o["s_ra"]), float(o["s_dec"]),
                           float(o["t_min"]) if o["t_min"] else np.nan,
                           float(o["t_exptime"]) if o["t_exptime"] else np.nan,
                           str(o["proposal_id"])))
            if len(picked) >= n:
                break
        print(f"  window {year}-{int(doy):03d}: pool now {len(picked)}/{n}")
    return picked


def retrieve(rootnames_meta, outdir, manifest_path):
    from acstools.focus_diverse_epsfs import psf_retriever

    os.makedirs(outdir, exist_ok=True)
    rows = []
    have = {os.path.basename(p).split("-")[0].lower()
            for p in glob.glob(os.path.join(outdir, "*.fits"))}
    for rec in rootnames_meta:
        root = rec["rootname"]
        if root in have:
            rec["status"] = "already_present"
            rows.append(rec)
            continue
        try:
            path = psf_retriever(root, outdir)
            rec["status"] = "ok" if path else "no_epsf_returned"
        except Exception as e:
            rec["status"] = f"failed: {type(e).__name__}: {e}"
        print(f"  {root}: {rec['status']}")
        rows.append(rec)
    df = pd.DataFrame(rows)
    df.to_csv(manifest_path, index=False)
    ok = (df["status"].isin(["ok", "already_present"])).sum()
    print(f"\nmanifest -> {manifest_path}")
    print(f"retrieved/present: {ok}/{len(df)}")
    return df


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--mode", choices=["benchmark", "broad"], required=True)
    p.add_argument("--n", type=int, default=60, help="broad-pool size")
    p.add_argument("--limit", type=int, default=None,
                   help="benchmark: only first N targets (smoke test)")
    p.add_argument("--excl-radius", type=float, default=2.0,
                   help="broad: exclusion radius around benchmark targets [arcmin]")
    p.add_argument("--seed", type=int, default=0)
    args = p.parse_args()

    labels = pd.read_csv(LABELS)
    bench_coords = list(zip(labels["ra_deg"], labels["dec_deg"]))

    if args.mode == "benchmark":
        targets = labels if args.limit is None else labels.head(args.limit)
        meta = []
        for _, row in targets.iterrows():
            print(f"{row['name']} ({row['survey']}):")
            found = flc_rootnames_for_coord(row["ra_deg"], row["dec_deg"])
            for root, tmin, expt, prop in found:
                print(f"    {root}  exptime={expt}  prop={prop}")
                meta.append(dict(rootname=root, source=row["name"],
                                 ra=row["ra_deg"], dec=row["dec_deg"],
                                 t_min=tmin, exptime=expt, proposal=prop))
        # dedup rootnames (adjacent lenses can share exposures)
        seen, uniq = set(), []
        for m in meta:
            if m["rootname"] not in seen:
                seen.add(m["rootname"])
                uniq.append(m)
        outdir = os.path.join(OUTROOT, "benchmark")
        retrieve(uniq, outdir, os.path.join(OUTROOT, "manifest_benchmark.csv"))
    else:
        picked = broad_pool(args.n, bench_coords, args.excl_radius, args.seed)
        meta = [dict(rootname=r, source=src, ra=ra, dec=dec,
                     t_min=tmin, exptime=expt, proposal=prop)
                for r, src, ra, dec, tmin, expt, prop in picked]
        outdir = os.path.join(OUTROOT, "broad")
        retrieve(meta, outdir, os.path.join(OUTROOT, "manifest_broad.csv"))


if __name__ == "__main__":
    main()
