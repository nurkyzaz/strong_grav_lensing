#!/usr/bin/env python
"""
build_real_lens_labels.py  (v2 -- cross-table merge)
====================================================
Pull published Einstein radii (b_SIE) + sky coordinates for the HST F814W
real-lens benchmark samples into ONE table: real_lens_labels.csv with columns
    name, ra_deg, dec_deg, theta_E_pub, q_pub, survey, src_table

** Why v2 ** In these VizieR catalogs the Einstein radii and the coordinates live
in DIFFERENT sub-tables, joined by the lens name:
    SLACS J/ApJ/682/964 : bSIE in table2, coords (_RA/_DE) in table0  -> join on 'Name'
    S4TM  J/ApJ/851/48  : bSIE in table1, coords (_RA/_DE) in table0  -> join on 'Target'
v2 merges every sub-table of a catalog on the lens-name column, then reads theta_E
and coords from the merged wide table.

theta_E_pub is the published SIE b_SIE [arcsec]. Your CNN labels use kappa_bar(<theta_E)=1
(einstein_radius_hard) -- a UNIFORM offset across all samples. State it in any write-up.

    SLACS  Bolton+2008      VizieR J/ApJ/682/964   bSIE  (63 grade-A)
    S4TM   Shu+2017         VizieR J/ApJ/851/48    bSIE  (40 grade-A)
    BELLS  Brownstein+2012  NOT IN VizieR -> manual_BELLS.csv (from the paper; 25 grade-A)

Usage
-----
  python build_real_lens_labels.py                       # SLACS + S4TM (+ BELLS if manual csv present)
  python build_real_lens_labels.py --surveys SLACS S4TM
  python build_real_lens_labels.py --surveys S4TM --theta_col bSIE   # force a column

BELLS: create manual_BELLS.csv with columns name,ra_deg,dec_deg,theta_E_pub[,q_pub]
from Brownstein 2012 (ApJ 744, 41) Table 4/5, then re-run; it is auto-appended.

Requires: astroquery, astropy, pandas, numpy.
"""
import sys
import os
import argparse
from collections import Counter
import numpy as np
import pandas as pd

SURVEYS = {
    "SLACS": dict(catalog="J/ApJ/682/964",
                  theta_cols=["bSIE", "b_SIE", "thetaE", "REin", "Rein"],
                  q_cols=["qSIE", "q_SIE", "q"]),
    "S4TM":  dict(catalog="J/ApJ/851/48",
                  theta_cols=["bSIE", "b_SIE", "thetaE"],
                  q_cols=["qSIE", "q_SIE", "q"]),
    # BELLS has no VizieR catalog -> manual_BELLS.csv only (handled in main)
    "BELLS": dict(catalog=None,
                  theta_cols=["bSIE"], q_cols=["q"]),
}

# columns we will try to join sub-tables on, in order of preference.
# (recno is deliberately EXCLUDED -- it is a per-table row counter, joining on it mis-matches.)
NAME_CANDS = ["Name", "Target", "SDSS", "SLACS", "BELLS", "System", "ID", "Lens"]

THETA_FUZZY = ("bsie", "sie", "rein", "r_ein", "thetae", "theta_e", "einstein")
Q_FUZZY = ("qsie", "q_sie", "axisratio", "axis_ratio")
COORD_PAIRS = (("_RAJ2000", "_DEJ2000"), ("_RA", "_DE"),
               ("RA_ICRS", "DE_ICRS"), ("_RA.icrs", "_DE.icrs"),
               ("RAJ2000", "DEJ2000"))


def find_col(colnames, preferred, fuzzy):
    cols = list(colnames)
    lower = {c.lower(): c for c in cols}
    for p in preferred:
        if p.lower() in lower:
            return lower[p.lower()]
    for c in cols:
        if any(f in c.lower() for f in fuzzy):
            return c
    return None


def detect_coords_cols(colnames):
    cols = set(colnames)
    for rc, dc in COORD_PAIRS:
        if rc in cols and dc in cols:
            return rc, dc
    return None, None


def coords_to_deg(ra_series, de_series):
    """Robustly turn an RA/Dec column pair into decimal degrees."""
    # try decimal degrees first (the common case: VizieR _RA/_DE are degrees)
    try:
        ra = pd.to_numeric(ra_series, errors="raise").to_numpy(float)
        de = pd.to_numeric(de_series, errors="raise").to_numpy(float)
        if np.nanmax(np.abs(ra)) <= 360.0 and np.nanmax(np.abs(de)) <= 90.0:
            return ra, de
    except (ValueError, TypeError):
        pass
    # otherwise sexagesimal (RA in hours) -- needs astropy
    from astropy.coordinates import SkyCoord
    import astropy.units as u
    c = SkyCoord(ra=np.asarray(ra_series, dtype=str),
                 dec=np.asarray(de_series, dtype=str),
                 unit=(u.hourangle, u.deg))
    return c.ra.deg, c.dec.deg


def merge_catalog_tables(cats, catalog_id):
    """Merge all sub-tables of a VizieR catalog on a shared lens-name column.

    Returns (wide_dataframe, join_key). If no shared name key exists, returns the
    first table and its best name column (single-table fallback).
    """
    tabs = []
    for i, t in enumerate(cats):
        tid = t.meta.get("name", f"{catalog_id}#t{i}")
        tabs.append((tid, t.to_pandas()))

    # pick the name column present in the most sub-tables (>=2 means a real join)
    cnt = Counter()
    for _, pdf in tabs:
        for cand in NAME_CANDS:
            if cand in pdf.columns:
                cnt[cand] += 1
    key = None
    for cand in NAME_CANDS:                       # preference order
        if cnt.get(cand, 0) >= 2:
            key = cand
            break
    if key is None:                               # name col in only one table
        for cand in NAME_CANDS:
            if cnt.get(cand, 0) >= 1:
                key = cand
                break

    if key is None:                               # no name column anywhere
        return tabs[0][1], None

    wide = None
    for _, pdf in tabs:
        if key not in pdf.columns:
            continue
        pdf = pdf.copy()
        pdf[key] = pdf[key].astype(str).str.strip()
        pdf = pdf.drop_duplicates(subset=[key])
        if wide is None:
            wide = pdf
        else:
            newcols = [c for c in pdf.columns if c == key or c not in wide.columns]
            wide = wide.merge(pdf[newcols], on=key, how="outer")
    return wide, key


def fetch_survey(name, cfg, theta_col_override=None, q_col_override=None):
    from astroquery.vizier import Vizier
    print(f"\n=== {name}: querying VizieR {cfg['catalog']} ===")
    v = Vizier(columns=["**"])          # request ALL columns (b_SIE is non-default)
    v.ROW_LIMIT = -1
    try:
        cats = v.get_catalogs(cfg["catalog"])
    except Exception as e:
        print(f"  fetch failed: {type(e).__name__}: {e}")
        return None
    if cats is None or len(cats) == 0:
        print("  no tables returned (this catalog id is not in VizieR)")
        return None

    wide, key = merge_catalog_tables(cats, cfg["catalog"])
    theta_col = theta_col_override or find_col(wide.columns, cfg["theta_cols"], THETA_FUZZY)
    rc, dc = detect_coords_cols(wide.columns)
    q_col = q_col_override or find_col(wide.columns, cfg["q_cols"], Q_FUZZY)

    if theta_col is None or rc is None or key is None:
        print(f"  could not assemble (theta_col={theta_col}, coords={rc}/{dc}, key={key}).")
        for i, t in enumerate(cats):
            fn = f"raw_{name}_t{i}.csv"
            t.to_pandas().to_csv(fn, index=False)
            print(f"    wrote {fn}  columns={list(t.colnames)}")
        return None

    print(f"  merged sub-tables on '{key}';  theta='{theta_col}'  coords='{rc}/{dc}'"
          + (f"  q='{q_col}'" if q_col else ""))
    ra_deg, dec_deg = coords_to_deg(wide[rc], wide[dc])
    df = pd.DataFrame({
        "name": wide[key].astype(str).str.strip(),
        "ra_deg": ra_deg,
        "dec_deg": dec_deg,
        "theta_E_pub": pd.to_numeric(wide[theta_col], errors="coerce"),
        "q_pub": (pd.to_numeric(wide[q_col], errors="coerce") if q_col else np.nan),
        "survey": name,
        "src_table": f"{cfg['catalog']} [{theta_col}|{rc}/{dc}]",
    })
    df = df.dropna(subset=["theta_E_pub", "ra_deg", "dec_deg"])
    df = df[(df["theta_E_pub"] > 0.2) & (df["theta_E_pub"] < 5.0)]
    df = df.drop_duplicates(subset=["name"]).reset_index(drop=True)

    med = df.theta_E_pub.median()
    print(f"  -> {len(df)} lenses  (theta_E median {med:.2f}\", "
          f"range [{df.theta_E_pub.min():.2f}, {df.theta_E_pub.max():.2f}]\")")
    if not (0.3 < med < 2.5):
        print(f"  !! WARNING median {med:.2f}\" is outside 0.5-2.0\" -- wrong column? "
              f"verify with inspect_vizier.py before trusting.")
    return df


def load_manual(name):
    fn = f"manual_{name}.csv"
    if not os.path.exists(fn):
        return None
    m = pd.read_csv(fn)
    need = {"name", "ra_deg", "dec_deg", "theta_E_pub"}
    if not need.issubset(m.columns):
        print(f"  {fn} missing columns {need - set(m.columns)} -- skipping")
        return None
    if "q_pub" not in m.columns:
        m["q_pub"] = np.nan
    m["survey"] = name
    m["src_table"] = fn
    print(f"  loaded {len(m)} {name} lenses from {fn}")
    return m[["name", "ra_deg", "dec_deg", "theta_E_pub", "q_pub", "survey", "src_table"]]


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--surveys", nargs="+", default=["SLACS", "S4TM", "BELLS"],
                    choices=list(SURVEYS))
    ap.add_argument("--theta_col", default=None,
                    help="force this theta_E column (use with a single --surveys)")
    ap.add_argument("--q_col", default=None)
    ap.add_argument("--out", default="real_lens_labels.csv")
    args = ap.parse_args()
    if args.theta_col and len(args.surveys) != 1:
        ap.error("--theta_col only makes sense with exactly one --surveys")

    frames = []
    for name in args.surveys:
        cfg = SURVEYS[name]
        df = None
        if cfg["catalog"] is not None:
            df = fetch_survey(name, cfg, args.theta_col, args.q_col)
        if df is None:                       # VizieR failed or no catalog -> manual
            df = load_manual(name)
            if df is None and cfg["catalog"] is None:
                print(f"\n=== {name}: no VizieR catalog and no manual_{name}.csv ===")
                print(f"  BELLS is not in VizieR. Fill manual_BELLS.csv with columns")
                print(f"  name,ra_deg,dec_deg,theta_E_pub[,q_pub] from Brownstein 2012")
                print(f"  (ApJ 744, 41) Table 4/5, then re-run.")
        if df is not None:
            frames.append(df)

    if not frames:
        print("\nNo labels fetched.")
        sys.exit(1)

    out = pd.concat(frames, ignore_index=True)
    out = out.drop_duplicates(subset=["survey", "name"]).reset_index(drop=True)
    out.to_csv(args.out, index=False)

    print("\n" + "=" * 60)
    print(f"WROTE {len(out)} lenses -> {args.out}")
    for s, g in out.groupby("survey"):
        print(f"  {s:6s}: {len(g):3d}  theta_E median {g.theta_E_pub.median():.2f}\"  "
              f"[{g.theta_E_pub.min():.2f}, {g.theta_E_pub.max():.2f}]\"")
    print("=" * 60)
    print(out.head(8).to_string(index=False))


if __name__ == "__main__":
    main()
