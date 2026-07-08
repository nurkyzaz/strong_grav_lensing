#!/usr/bin/env python
"""
fetch_real_lens_images.py
=========================
Download HST cutouts for the real-lens benchmark (SLACS / S4TM / BELLS, all HST
ACS/WFC F814W) from MAST, centred on each lens, at a FIXED 6.4" angular box
-> 128x128 px (0.05"/px). This matches your existing 51-SLACS cutouts and the
HSTempty / SIMCT pipeline, so the scale-conditioned CNN's scale input stays well
defined across all real lenses (fixed FOV -> single, known scale scalar).

Reads:  real_lens_labels.csv  (from build_real_lens_labels.py)
Writes: real_<survey>_images.h5
          key 'images'      [N,1,128,128] float32  raw drizzled flux (e-/s), NO normalization
          key 'names'       [N] utf-8
          key 'theta_E_pub' [N] float32            published SIE b_SIE [arcsec]
          key 'survey'      [N] utf-8
          key 'pixscale'    scalar float32          arcsec/px of the 128x128 cutout (=0.05)
          key 'box_arcsec'  scalar float32          angular box (=6.4)
        previews/<survey>/<name>.png  asinh-stretched, red cross at cutout centre

  ** NO subtraction / normalization here ** -- raw cutouts, exactly like the
  fetch_slacs_images.py you already use. Lens-light subtraction (residual_v2) and
  flux_rescale -> normalize_images(asinh) happen downstream in your test script,
  to stay aligned with Brian's raw-electron/s pipeline.

BELLS GALLERY note: it is WFC3/UVIS F606W, a different band -> pass --gallery to
switch the MAST query. Treat results as a separate, domain-shifted tier.

Usage
-----
  # smoke test: 5 lenses, prints what it finds, downloads, eyeball the previews
  python fetch_real_lens_images.py --survey S4TM --limit 5

  # full survey
  python fetch_real_lens_images.py --survey S4TM
  python fetch_real_lens_images.py --survey BELLS
  python fetch_real_lens_images.py --survey SLACS         # all 63 (re-fetch is cheap; MAST caches)

  # optional large-theta tier (band shift)
  python fetch_real_lens_images.py --survey BELLS_GALLERY --gallery --labels gallery_labels.csv

Requires: astroquery, astropy, h5py, scipy, numpy, pandas, matplotlib (Stronglensing env).
Drizzled frames are ~200 MB each; the first fetch of a survey is the slow part.
MAST caches downloads, so re-runs are fast.
"""
import os
import sys
import argparse
import warnings
import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")  # WCS / FITS verification chatter

DEFAULT_BOX = 6.4    # arcsec, fixed FOV (matches your SLACS cutouts)
DEFAULT_NPIX = 128


def mast_query(coord, gallery=False, radius_arcsec=20.0):
    """Return a MAST product table of drizzled science images covering `coord`."""
    from astroquery.mast import Observations
    import astropy.units as u

    if gallery:
        instrument, filt = "WFC3/UVIS", "F606W"
    else:
        instrument, filt = "ACS/WFC", "F814W"

    obs = Observations.query_criteria(
        coordinates=coord,
        radius=radius_arcsec * u.arcsec,
        obs_collection="HST",
        instrument_name=instrument,
        filters=filt,
        dataproduct_type="image",
    )
    if obs is None or len(obs) == 0:
        return None

    prods = Observations.get_product_list(obs)
    # keep drizzled science products; prefer CTE-corrected DRC over DRZ
    sci = Observations.filter_products(
        prods, productType="SCIENCE", extension="fits")
    if sci is None or len(sci) == 0:
        return None
    fn = np.array([str(x).lower() for x in sci["productFilename"]])
    drc = sci[[("drc" in f) for f in fn]]
    drz = sci[[("drz" in f) for f in fn]]
    chosen = drc if len(drc) else drz
    return chosen if len(chosen) else None


def download_and_cut(prod_table, coord, box_arcsec, npix, cache_dir):
    """Download products in order until one yields a valid cutout. Returns 2D array."""
    from astroquery.mast import Observations
    from astropy.io import fits
    from astropy.wcs import WCS
    from astropy.nddata import Cutout2D
    import astropy.units as u
    from scipy.ndimage import zoom

    for row in prod_table:
        try:
            man = Observations.download_products(
                row, download_dir=cache_dir, cache=True)
        except Exception as e:
            print(f"      download error: {type(e).__name__}: {e}")
            continue
        path = man["Local Path"][0]
        try:
            with fits.open(path, memmap=True) as hdul:
                # drizzled products: science image is in the 'SCI' extension (ext 1)
                sci_ext = None
                for i, h in enumerate(hdul):
                    if h.data is not None and h.header.get("EXTNAME", "").upper() == "SCI":
                        sci_ext = i
                        break
                if sci_ext is None:
                    sci_ext = 1 if len(hdul) > 1 and hdul[1].data is not None else 0
                data = np.asarray(hdul[sci_ext].data, dtype=np.float32)
                wcs = WCS(hdul[sci_ext].header)

            # is the target actually inside this frame?
            x, y = wcs.world_to_pixel(coord)
            if not (0 <= x < data.shape[1] and 0 <= y < data.shape[0]):
                continue

            cut = Cutout2D(data, position=coord, size=box_arcsec * u.arcsec,
                           wcs=wcs, mode="partial", fill_value=0.0)
            cdata = np.nan_to_num(cut.data, nan=0.0).astype(np.float32)
            if cdata.size == 0 or not np.isfinite(cdata).any():
                continue

            # resample to exactly npix x npix
            if cdata.shape != (npix, npix):
                zy, zx = npix / cdata.shape[0], npix / cdata.shape[1]
                cdata = zoom(cdata, (zy, zx), order=1).astype(np.float32)
                if cdata.shape != (npix, npix):  # rounding guard
                    cdata = cdata[:npix, :npix]
                    pad = [(0, npix - cdata.shape[0]), (0, npix - cdata.shape[1])]
                    cdata = np.pad(cdata, pad)
            return cdata
        except Exception as e:
            print(f"      cutout error on {os.path.basename(path)}: "
                  f"{type(e).__name__}: {e}")
            continue
    return None


def save_preview(img, path, name):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    v = img - np.median(img)
    s = np.arcsinh(v / (np.std(v) + 1e-8))
    plt.figure(figsize=(3, 3))
    plt.imshow(s, origin="lower", cmap="gray")
    n = img.shape[0]
    plt.plot(n / 2, n / 2, "+", color="red", ms=10, mew=1.5)
    plt.title(name, fontsize=8)
    plt.axis("off")
    plt.tight_layout()
    plt.savefig(path, dpi=90, bbox_inches="tight")
    plt.close()


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--labels", default="real_lens_labels.csv")
    ap.add_argument("--survey", required=True,
                    help="survey tag to fetch (matches the 'survey' column), "
                         "e.g. SLACS / S4TM / BELLS / BELLS_GALLERY")
    ap.add_argument("--gallery", action="store_true",
                    help="use WFC3/UVIS F606W query (for BELLS GALLERY)")
    ap.add_argument("--box", type=float, default=DEFAULT_BOX,
                    help="angular cutout box in arcsec (default 6.4, matches SLACS)")
    ap.add_argument("--npix", type=int, default=DEFAULT_NPIX)
    ap.add_argument("--limit", type=int, default=None, help="stop after N lenses")
    ap.add_argument("--cache", default="mast_cache")
    ap.add_argument("--out", default=None, help="output .h5 (default real_<survey>_images.h5)")
    ap.add_argument("--dry-run", action="store_true",
                    help="only report what MAST finds; download nothing")
    args = ap.parse_args()

    import h5py
    from astropy.coordinates import SkyCoord
    import astropy.units as u

    df = pd.read_csv(args.labels)
    df = df[df["survey"].str.upper() == args.survey.upper()].reset_index(drop=True)
    if len(df) == 0:
        sys.exit(f"no lenses with survey=={args.survey} in {args.labels}")
    if args.limit:
        df = df.iloc[:args.limit].reset_index(drop=True)

    out_h5 = args.out or f"real_{args.survey.lower()}_images.h5"
    prev_dir = os.path.join("previews", args.survey.lower())
    os.makedirs(prev_dir, exist_ok=True)
    os.makedirs(args.cache, exist_ok=True)

    print(f"Fetching {len(df)} {args.survey} lenses "
          f"({'WFC3/UVIS F606W' if args.gallery else 'ACS/WFC F814W'}), "
          f"box={args.box}\" -> {args.npix}px ({args.box/args.npix:.4f}\"/px)\n")

    images, names, thetas, kept = [], [], [], []
    for i, r in df.iterrows():
        coord = SkyCoord(r.ra_deg * u.deg, r.dec_deg * u.deg)
        tag = f"  [{i+1:3d}/{len(df)}] {r['name']:14s} theta_E_pub={r.theta_E_pub:.2f}\""
        prods = mast_query(coord, gallery=args.gallery)
        if prods is None:
            print(tag + "   MISS (no drizzled F814W product covering it)")
            continue
        if args.dry_run:
            print(tag + f"   {len(prods)} drizzled product(s) available")
            continue
        img = download_and_cut(prods, coord, args.box, args.npix, args.cache)
        if img is None:
            print(tag + "   MISS (download/cutout failed)")
            continue
        images.append(img[None])          # [1,128,128]
        names.append(str(r["name"]))
        thetas.append(float(r.theta_E_pub))
        kept.append(str(r["survey"]))
        save_preview(img, os.path.join(prev_dir, f"{r['name']}.png"), r["name"])
        print(tag + "   [ok]")

    if args.dry_run:
        return
    if not images:
        sys.exit("no images fetched -- check coordinates / MAST availability")

    images = np.asarray(images, dtype=np.float32)
    dt = h5py.string_dtype(encoding="utf-8")
    with h5py.File(out_h5, "w") as f:
        f.create_dataset("images", data=images)
        f.create_dataset("names", data=np.array(names, dtype=object), dtype=dt)
        f.create_dataset("theta_E_pub", data=np.asarray(thetas, np.float32))
        f.create_dataset("survey", data=np.array(kept, dtype=object), dtype=dt)
        f.create_dataset("pixscale", data=np.float32(args.box / args.npix))
        f.create_dataset("box_arcsec", data=np.float32(args.box))

    print(f"\nWROTE {len(images)} cutouts -> {out_h5}")
    print(f"  previews in {prev_dir}/   (eyeball centring + arc visibility before trusting)")
    miss = len(df) - len(images)
    if miss:
        print(f"  {miss} misses -- usually a coordinate just off the ACS footprint "
              f"or no public F814W frame; check those names by hand.")


if __name__ == "__main__":
    main()
