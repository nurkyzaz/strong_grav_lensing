#!/usr/bin/env python3
"""
crossmatch_real_lenses.py
=========================
Compare OUR 51 real-lens test set (SLACS, F814W, Bolton theta_E) against the
published real-lens samples of the closest literature papers, decide which new
lenses to acquire, and write prioritized target lists.

WHY: our current 51 are a somewhat arbitrary subset of the SLACS grade-A sample.
This tool tells us, per candidate paper:
  - how many of our 51 it already contains (overlap),
  - how many NEW lenses it would add,
  - the theta_E coverage of those new lenses (and how many fall in our CNN's
    valid range 0.5-2.5"  and in the under-sampled tails),
so we can grow the real-lens benchmark in a defensible, reproducible way.

DOMAIN NOTE (the reason for the tier ordering below):
  Our CNN is trained HST-like in the F814W (I) band. So F814W samples transfer
  best; F606W (V) introduces a band shift; ground-based (HSC/CFHT) is the largest
  shift. All catalogs below report SIE / b_SIE theta_E -> the SAME definitional
  offset vs our kappa_bar(<theta_E)=1 labels applies UNIFORMLY, so mixing them
  does NOT add a new definition inconsistency (it stays one consistent offset).

RUN THIS ON THE CLUSTER (needs internet to reach VizieR):
    conda activate Stronglensing       # or any env with astropy+astroquery
    pip install astropy astroquery      # if not present
    python crossmatch_real_lenses.py --ours theta_E_for_brian.csv --outdir targets

The VizieR catalog IDs below are my best identification; the script VERIFIES each
fetch (prints the table + detected theta_E column) and FALLS BACK to a keyword
catalog search if an ID misses. Confirm the printed column is really theta_E
before trusting a sample.
"""

import argparse, re, sys, os
import numpy as np
import pandas as pd

# ----------------------------------------------------------------------------- 
# Candidate real-lens samples, ranked by transfer-distance to our HST/F814W CNN.
# tier 1 = get first.  'band' drives the ordering; all use SIE/b_SIE theta_E.
# ----------------------------------------------------------------------------- 
CATALOGS = [
    dict(label="SLACS_Bolton2008", tier=1, band="F814W",
         vizier="J/ApJ/682/964", find=["SLACS", "Bolton", "Einstein"],
         note="63 grade-A with lens models; the set Cao+2025 (ref [23] in our paper) "
              "validates on. Completes the sample our 51 are drawn from. Zero domain shift."),
    dict(label="S4TM_Shu2017", tier=1, band="F814W",
         vizier="J/ApJ/851/48", find=["S4TM", "Shu", "lens"],
         note="SLACS-for-the-masses: same HST ACS F814W + ACSPROC pipeline, designed for "
              "LOWER masses / SMALLER theta_E -> fills our thin <0.8\" tail. ~40 new grade-A."),
    dict(label="BELLS_Brownstein2012", tier=2, band="F814W",
         vizier="J/ApJ/744/41", find=["BELLS", "Brownstein", "emission-line"],
         note="HST ACS-WFC F814W, 25 grade-A at z~0.5, median theta_E ~0.75\" -> also fills "
              "the small-theta_E tail and extends lens redshift. Same band as our training."),
    dict(label="BELLS_GALLERY_Shu2016", tier=3, band="F606W",
         vizier="J/ApJ/833/264", find=["BELLS", "GALLERY", "Shu", "Lyman"],
         note="HST WFC3 F606W (V-band -> BAND SHIFT), 17 grade-A, larger theta_E (median ~1.2\"), "
              "Ly-a sources (bluer/fainter arcs). Useful for the large-theta_E tail; more domain shift."),
    dict(label="SuGOHI_Sonnenfeld", tier=4, band="HSC_gri",
         vizier=None, find=["SuGOHI", "Sonnenfeld", "Hyper Suprime-Cam"],
         note="Gawade+2025's test sample. Closest METHOD match (CNN->theta_E) but GROUND-BASED "
              "HSC g/r/i (~0.168\"/px) -> largest domain shift. Defer to the multiband/ground-based phase."),
]

THETA_COL_HINTS = ["thetae", "theta_e", "rein", "r_ein", "bsie", "b_sie", "einstein", "thein", "the"]

# ----------------------------------------------------------------------------- 
# name <-> short-key helpers (robust to SDSS Jhhmm+/-ddmm truncation)
# ----------------------------------------------------------------------------- 
def short_key_from_coord(ra_deg, dec_deg):
    ra_h = ra_deg / 15.0
    hh = int(ra_h); mm = int((ra_h - hh) * 60)
    sign = '+' if dec_deg >= 0 else '-'
    a = abs(dec_deg); dd = int(a); am = int((a - dd) * 60)
    return f"{hh:02d}{mm:02d}{sign}{dd:02d}{am:02d}"

def short_key_from_name(name):
    m = re.match(r'[Jj]?\s*(\d{2})(\d{2})\d*\.?\d*([+-])(\d{2})(\d{2})', str(name).strip())
    if not m:
        return None
    hh, mm, sgn, dd, am = m.groups()
    return f"{hh}{mm}{sgn}{dd}{am}"

def neighbor_keys(k):
    hh, mm, sgn, dd, am = k[:2], k[2:4], k[4], k[5:7], k[7:9]
    out = set()
    for dmm in (-1, 0, 1):
        for dam in (-1, 0, 1):
            nm = (int(mm) + dmm) % 60
            na = (int(am) + dam) % 60
            out.add(f"{hh}{nm:02d}{sgn}{dd}{na:02d}")
    return out

# ----------------------------------------------------------------------------- 
# VizieR fetch (with keyword fallback + theta_E column auto-detect)
# ----------------------------------------------------------------------------- 
def fetch_catalog(spec):
    from astroquery.vizier import Vizier
    from astropy.coordinates import SkyCoord
    import astropy.units as u

    Vizier.ROW_LIMIT = -1
    tables = None

    def _try(vid):
        try:
            res = Vizier.get_catalogs(vid)
            return res if len(res) else None
        except Exception as e:
            print(f"    [warn] get_catalogs({vid!r}) failed: {type(e).__name__}: {str(e)[:120]}")
            return None

    if spec["vizier"]:
        tables = _try(spec["vizier"])
    if tables is None:
        print(f"    [info] falling back to keyword search: {spec['find']}")
        try:
            cand = Vizier.find_catalogs(" ".join(spec["find"]))
            for vid in list(cand.keys())[:6]:
                print(f"      candidate VizieR id: {vid}  ({cand[vid].description[:70]})")
                tables = _try(vid)
                if tables is not None:
                    spec["vizier"] = vid
                    break
        except Exception as e:
            print(f"    [warn] find_catalogs failed: {type(e).__name__}: {str(e)[:120]}")

    if tables is None:
        return None

    # pick the sub-table that has BOTH sky coords and a theta_E-like column
    best = None
    for t in tables:
        cols = {c.lower().replace(" ", "").replace("-", ""): c for c in t.colnames}
        theta_col = next((cols[h] for h in THETA_COL_HINTS if h in cols), None)
        # try common coordinate column patterns
        ra_col = next((t.colnames[i] for i, c in enumerate(t.colnames)
                       if c in ("RAJ2000", "_RAJ2000", "RA_ICRS", "RAdeg", "RA")), None)
        de_col = next((t.colnames[i] for i, c in enumerate(t.colnames)
                       if c in ("DEJ2000", "_DEJ2000", "DE_ICRS", "DEdeg", "DEC", "Dec")), None)
        name_col = next((t.colnames[i] for i, c in enumerate(t.colnames)
                         if "name" in c.lower() or c.lower() in ("slacs", "bells", "system", "lens")), None)
        if theta_col and (ra_col and de_col or name_col):
            best = (t, theta_col, ra_col, de_col, name_col)
            break

    if best is None:
        print("    [warn] no sub-table with both coords/name and a theta_E column; "
              f"available columns were: {[t.colnames for t in tables][:1]}")
        return None

    t, theta_col, ra_col, de_col, name_col = best
    df = t.to_pandas()
    print(f"    detected theta_E column: '{theta_col}'  "
          f"(coords: {ra_col}/{de_col}, name: {name_col})  rows: {len(df)}")

    # build short keys
    keys, names, ras, des = [], [], [], []
    for _, row in df.iterrows():
        k = None
        if name_col and pd.notna(row.get(name_col)):
            k = short_key_from_name(row[name_col])
        if k is None and ra_col and de_col and pd.notna(row.get(ra_col)) and pd.notna(row.get(de_col)):
            try:
                c = SkyCoord(str(row[ra_col]), str(row[de_col]),
                             unit=(u.hourangle, u.deg)) if not _isnum(row[ra_col]) \
                    else SkyCoord(float(row[ra_col]) * u.deg, float(row[de_col]) * u.deg)
                k = short_key_from_coord(c.ra.deg, c.dec.deg)
                ras.append(c.ra.deg); des.append(c.dec.deg)
            except Exception:
                ras.append(np.nan); des.append(np.nan)
        else:
            ras.append(np.nan); des.append(np.nan)
        keys.append(k)
        names.append(row[name_col] if name_col else k)

    out = pd.DataFrame(dict(key=keys, cat_name=names,
                            ra=ras if len(ras) == len(df) else np.nan,
                            dec=des if len(des) == len(df) else np.nan,
                            theta_E_pub=pd.to_numeric(df[theta_col], errors="coerce")))
    return out.dropna(subset=["key"]).reset_index(drop=True)

def _isnum(x):
    try:
        float(x); return True
    except Exception:
        return False

# ----------------------------------------------------------------------------- 
def crossmatch(ours_keys, cat_df):
    """Return (overlap_keys, new_rows) where new_rows are catalog lenses not in ours."""
    ours_expanded = set()
    for k in ours_keys:
        ours_expanded |= neighbor_keys(k)
    overlap, new_idx = [], []
    for i, k in enumerate(cat_df["key"]):
        if k in ours_expanded:
            overlap.append(k)
        else:
            new_idx.append(i)
    return overlap, cat_df.iloc[new_idx].reset_index(drop=True)

def tail_stats(theta):
    theta = theta.dropna()
    return dict(
        n=len(theta),
        in_cnn_range=int(((theta >= 0.5) & (theta <= 2.5)).sum()),
        small_tail=int((theta < 0.8).sum()),       # our under-sampled low end
        large_tail=int((theta > 1.7).sum()),        # our under-sampled high end
        median=float(np.median(theta)) if len(theta) else float("nan"),
    )

# ----------------------------------------------------------------------------- 
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ours", default="theta_E_for_brian.csv")
    ap.add_argument("--outdir", default="targets")
    ap.add_argument("--name-col", default="name")
    args = ap.parse_args()
    os.makedirs(args.outdir, exist_ok=True)

    ours = pd.read_csv(args.ours)
    ours_keys = [short_key_from_name(n) for n in ours[args.name_col]]
    bad = [n for n, k in zip(ours[args.name_col], ours_keys) if k is None]
    ours_keys = [k for k in ours_keys if k]
    print(f"Loaded {len(ours)} of our lenses; parsed {len(ours_keys)} keys"
          + (f"; FAILED: {bad}" if bad else "") + "\n")

    summary = []
    merged_targets = []
    for spec in CATALOGS:
        print(f"=== {spec['label']}  (tier {spec['tier']}, {spec['band']}) ===")
        try:
            cat = fetch_catalog(spec)
        except ImportError:
            print("  astroquery/astropy not installed -> skipping live fetch.")
            cat = None
        if cat is None or len(cat) == 0:
            print("  -> no usable table fetched; verify the VizieR id / column manually.\n")
            summary.append(dict(catalog=spec["label"], tier=spec["tier"], band=spec["band"],
                                overlap=None, new=None, new_in_range=None,
                                new_small_tail=None, new_large_tail=None))
            continue

        overlap, new = crossmatch(ours_keys, cat)
        st = tail_stats(new["theta_E_pub"])
        print(f"  overlap with our 51: {len(set(overlap))}   |   NEW lenses: {len(new)}")
        print(f"  NEW theta_E: median {st['median']:.2f}\"  in[0.5,2.5]:{st['in_cnn_range']}"
              f"  <0.8\":{st['small_tail']}  >1.7\":{st['large_tail']}")

        new_sorted = new.sort_values("theta_E_pub").reset_index(drop=True)
        path = os.path.join(args.outdir, f"targets_{spec['label']}.csv")
        new_sorted.to_csv(path, index=False)
        print(f"  wrote {path}\n")

        nn = new_sorted.copy()
        nn.insert(0, "source_catalog", spec["label"])
        nn.insert(1, "tier", spec["tier"])
        nn.insert(2, "band", spec["band"])
        merged_targets.append(nn)

        summary.append(dict(catalog=spec["label"], tier=spec["tier"], band=spec["band"],
                            overlap=len(set(overlap)), new=len(new),
                            new_in_range=st["in_cnn_range"],
                            new_small_tail=st["small_tail"], new_large_tail=st["large_tail"]))

    sdf = pd.DataFrame(summary).sort_values(["tier", "catalog"])
    print("================  RANKED SUMMARY  ================")
    print(sdf.to_string(index=False))
    sdf.to_csv(os.path.join(args.outdir, "summary.csv"), index=False)

    if merged_targets:
        allt = pd.concat(merged_targets, ignore_index=True)
        # de-dup lenses that appear in multiple catalogs: keep the lowest tier (best band)
        allt = allt.sort_values(["tier"]).drop_duplicates("key", keep="first")
        allt = allt.sort_values(["tier", "theta_E_pub"]).reset_index(drop=True)
        allt.to_csv(os.path.join(args.outdir, "targets_priority.csv"), index=False)
        print(f"\nMerged, de-duplicated priority list -> {args.outdir}/targets_priority.csv "
              f"({len(allt)} unique new lenses)")

if __name__ == "__main__":
    main()
