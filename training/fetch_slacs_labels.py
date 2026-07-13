#!/usr/bin/env python
"""
fetch_slacs_labels.py
---------------------
Pull published SLACS lens parameters (SIE Einstein radius + axis ratio) from
VizieR so we have reference labels for the real-lens test.

Output:
  slacs_labels.csv  -> columns: name, ra_deg, dec_deg, theta_E_pub, q_pub, src_table

CAVEAT (carry this through to the plot):
  Published theta_E here are SIE-analytic values. Our CNN labels use
  kappa_bar(<theta_E)=1 on IllustrisTNG. These are DIFFERENT definitions and
  differ by a systematic offset for the same lens -- a definition difference,
  not pure model error.

If auto-detection of the Einstein-radius / axis-ratio columns fails, the script
dumps the raw catalog to slacs_raw_<n>.csv and prints all columns so you can set
--theta_col / --q_col by hand and re-run.
"""
import argparse
import sys
import numpy as np
import pandas as pd
from astropy.coordinates import SkyCoord
from astropy import units as u
from astroquery.vizier import Vizier

# SLACS catalogs that carry an SIE lensing fit (theta_E + axis ratio).
# Bolton+2008  (SLACS V,  ApJ 682, 964)  -> clean SIE lensing fit, has b_SIE + q
# Auger+2009   (SLACS IX, ApJ 705, 1099) -> photometry + lensing
# Auger+2010   (         ApJ 724, 511)   -> joint lensing+dynamics
CANDIDATE_CATALOGS = ["J/ApJ/682/964", "J/ApJ/705/1099", "J/ApJ/724/511"]

THETA_KEYS = ["einstein", "b_sie", "bsie", "thetaein", "theta_e",
              "reinst", "r_ein", "rein", "tein"]
Q_KEYS_DESC = ["axis ratio", "axis-ratio", "ellipticit"]
Q_KEYS_NAME = ["q_sie", "qsie", "q"]
RA_KEYS = ["raj2000", "_ra", "ra_", "ra"]
DE_KEYS = ["dej2000", "_de", "de_", "dec", "de"]


def col_text(table, name):
    desc = table[name].description or ""
    return f"{name} || {desc}".lower()


def find_theta(table):
    # prefer a description that mentions Einstein explicitly
    for name in table.colnames:
        if "einstein" in col_text(table, name):
            return name
    for name in table.colnames:
        t = col_text(table, name)
        if any(k in t for k in THETA_KEYS):
            return name
    return None


def find_q(table):
    for name in table.colnames:
        d = (table[name].description or "").lower()
        if any(k in d for k in Q_KEYS_DESC):
            return name
    for name in table.colnames:
        if name.lower() in Q_KEYS_NAME:
            return name
    return None


def find_radec(table):
    ra = de = None
    for name in table.colnames:
        low = name.lower()
        if ra is None and any(low == k or low.startswith("raj") or low.startswith("_ra") for k in RA_KEYS):
            ra = name
        if de is None and any(low == k or low.startswith("dej") or low.startswith("_de") for k in DE_KEYS):
            de = name
    return ra, de


def find_name(table):
    for cand in ["SDSS", "Name", "_2MASS", "SLACS", "ID", "Lens"]:
        for name in table.colnames:
            if cand.lower() in name.lower():
                return name
    return table.colnames[0]


def parse_radec(table, ra_col, de_col):
    ra_vals = table[ra_col]
    de_vals = table[de_col]
    # try numeric degrees first, then sexagesimal
    try:
        ra_deg = np.asarray(ra_vals, dtype=float)
        de_deg = np.asarray(de_vals, dtype=float)
        if np.nanmax(ra_deg) <= 360 and np.nanmin(ra_deg) >= 0 and np.nanmax(np.abs(de_deg)) <= 90:
            return ra_deg, de_deg
    except (ValueError, TypeError):
        pass
    coords = SkyCoord([str(r) for r in ra_vals],
                      [str(d) for d in de_vals],
                      unit=(u.hourangle, u.deg))
    return coords.ra.deg, coords.dec.deg


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--catalog", default=None,
                    help="VizieR catalog id (default: try the SLACS list)")
    ap.add_argument("--theta_col", default=None, help="override Einstein-radius column")
    ap.add_argument("--q_col", default=None, help="override axis-ratio column")
    ap.add_argument("--out", default="slacs_labels.csv")
    args = ap.parse_args()

    cats = [args.catalog] if args.catalog else CANDIDATE_CATALOGS

    v = Vizier(columns=["**"])
    v.ROW_LIMIT = -1

    for cat in cats:
        print(f"\n=== querying VizieR catalog {cat} ===")
        try:
            tl = v.get_catalogs(cat)
        except Exception as e:
            print(f"  could not fetch {cat}: {e}")
            continue
        if not tl:
            print("  (no tables returned)")
            continue

        for ti, table in enumerate(tl):
            theta_col = args.theta_col or find_theta(table)
            q_col = args.q_col or find_q(table)
            ra_col, de_col = find_radec(table)
            name_col = find_name(table)

            print(f"\n  table {ti}: {len(table)} rows, {len(table.colnames)} cols")
            print(f"    columns: {', '.join(table.colnames)}")
            print(f"    -> name={name_col} ra={ra_col} dec={de_col} "
                  f"theta_E={theta_col} q={q_col}")

            if theta_col is None or ra_col is None or de_col is None:
                dump = f"slacs_raw_{cat.replace('/','_')}_t{ti}.csv"
                table.to_pandas().to_csv(dump, index=False)
                print(f"    !! missing a required column; dumped raw table -> {dump}")
                print(f"       inspect it, then re-run with --catalog {cat} "
                      f"--theta_col <col> [--q_col <col>]")
                continue

            try:
                ra_deg, de_deg = parse_radec(table, ra_col, de_col)
            except Exception as e:
                print(f"    !! could not parse RA/Dec ({e}); dumping raw.")
                table.to_pandas().to_csv(f"slacs_raw_{cat.replace('/','_')}_t{ti}.csv", index=False)
                continue

            df = pd.DataFrame({
                "name": [str(x).strip() for x in table[name_col]],
                "ra_deg": ra_deg,
                "dec_deg": de_deg,
                "theta_E_pub": np.asarray(table[theta_col], dtype=float),
                "q_pub": (np.asarray(table[q_col], dtype=float)
                          if q_col is not None else np.nan),
                "src_table": f"{cat}#t{ti}",
            })
            df = df.dropna(subset=["theta_E_pub", "ra_deg", "dec_deg"])
            df = df[(df["theta_E_pub"] > 0.2) & (df["theta_E_pub"] < 5.0)]
            df = df.drop_duplicates(subset=["name"]).reset_index(drop=True)

            if len(df) >= 5:
                df.to_csv(args.out, index=False)
                print(f"\n  WROTE {len(df)} lenses -> {args.out}")
                print(df.head(10).to_string(index=False))
                print(f"\n  theta_E_pub: median={df.theta_E_pub.median():.2f}\" "
                      f"range=[{df.theta_E_pub.min():.2f}, {df.theta_E_pub.max():.2f}]\"")
                return
            else:
                print(f"    only {len(df)} usable rows in this table; trying next.")

    print("\nNo usable table found automatically. Inspect any slacs_raw_*.csv dumped "
          "above and re-run with explicit --catalog/--theta_col/--q_col.")
    sys.exit(1)


if __name__ == "__main__":
    main()
