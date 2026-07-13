#!/usr/bin/env python3
"""
inspect_vizier.py — find the right table + theta_E column for a VizieR catalog.

The cross-match auto-picks the first sub-table that has a theta_E-like column.
For multi-table catalogs (S4TM, BELLS) the Einstein radii live in a DIFFERENT
sub-table than the spectroscopy/photometry one, so the auto-pick misses. Run this
to list EVERY sub-table and its columns, spot the one with bSIE / theta_E, then
put the exact "J/ApJ/.../n" table id into CATALOGS in crossmatch_real_lenses.py.

Usage:
    python inspect_vizier.py J/ApJ/851/48           # list all tables of a catalog
    python inspect_vizier.py --find "BELLS Brownstein"   # search ids by keyword
"""
import sys, argparse

def list_tables(catalog_id):
    from astroquery.vizier import Vizier
    Vizier.ROW_LIMIT = -1
    print(f"\n=== tables in {catalog_id} ===")
    try:
        cats = Vizier.get_catalogs(catalog_id)
    except Exception as e:
        print(f"  fetch failed: {type(e).__name__}: {e}")
        return
    if cats is None or len(cats) == 0:
        print("  (no tables returned — id may be wrong; try --find)")
        return
    for i, t in enumerate(cats):
        tid = t.meta.get("name", f"table{i}")
        print(f"\n  [{i}] {tid}   rows={len(t)}")
        print(f"      columns: {list(t.colnames)}")
        # flag likely theta_E columns
        hits = [c for c in t.colnames
                if any(h in c.lower() for h in
                       ("sie", "rein", "thetae", "theta_e", "einstein", "r_ein"))]
        if hits:
            print(f"      >>> likely theta_E column(s): {hits}")
            # show a few example values so you can eyeball units (arcsec)
            for c in hits:
                try:
                    vals = [v for v in t[c][:5]]
                    print(f"          {c} sample: {vals}")
                except Exception:
                    pass

def find(keywords):
    from astroquery.vizier import Vizier
    print(f"\n=== catalog search: {keywords!r} ===")
    try:
        cand = Vizier.find_catalogs(keywords)
    except Exception as e:
        print(f"  search failed: {type(e).__name__}: {e}")
        return
    if not cand:
        print("  (nothing found)")
        return
    for vid in list(cand.keys())[:15]:
        desc = ""
        try:
            desc = getattr(cand[vid], "description", "") or ""
        except Exception:
            pass
        print(f"  {vid:24s}  {desc[:80]}")

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("target", nargs="?", help="VizieR catalog id, e.g. J/ApJ/851/48")
    ap.add_argument("--find", help="keyword search instead of listing a catalog")
    args = ap.parse_args()
    if args.find:
        find(args.find)
    elif args.target:
        list_tables(args.target)
    else:
        ap.print_help()
