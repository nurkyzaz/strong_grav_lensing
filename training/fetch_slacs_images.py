#!/usr/bin/env python
"""
fetch_slacs_images.py
---------------------
For each lens in slacs_labels.csv, query MAST for HST ACS/WFC F814W, download the
drizzled science product, cut out a fixed ANGULAR box centred on the lens galaxy,
resample to 128x128, and save everything the test script needs.

Outputs:
  real_slacs_images.h5     key 'images'  [N,1,128,128] float32 (raw flux, e-/s)
                           key 'names'   [N] str
                           key 'pixscale' scalar arcsec/px of the 128x128 cutout
  previews/<name>.png      asinh-stretched preview to eyeball centring + arc visibility

Centre each cutout on the lens-galaxy coordinates (the bright central blob) -- this
is correct for real SLACS (unlike the off-centre IllustrisTNG kappa maps, which we
centre on the kappa centroid).

Start with --limit 15 for a smoke test (drizzled frames are large). Drop --limit
for the full sample once a few cutouts look right.
"""
import argparse
import os
import numpy as np
import pandas as pd
import h5py
from astropy.coordinates import SkyCoord
from astropy import units as u
from astropy.io import fits
from astropy.wcs import WCS
from astropy.nddata import Cutout2D
from scipy.ndimage import zoom
from astroquery.mast import Observations
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

BOX_ARCSEC = 6.4    # cutout side -> 6.4"/128px = 0.05"/px, inside training FOV 4-10"
NPIX = 128


def asinh_display(img, soft=0.02, lo=1.0, hi=99.7):
    """asinh stretch + percentile clip, only for the PNG preview (raw linear
    display hides the arcs under the bright lens)."""
    finite = img[np.isfinite(img)]
    if finite.size == 0:
        return np.zeros_like(img)
    vlo, vhi = np.percentile(finite, [lo, hi])
    x = np.clip((img - vlo) / max(hi - lo, 1e-9), 0, None)
    x = np.arcsinh(x / soft)
    x = np.clip(x, 0, np.percentile(x[np.isfinite(x)], 99.7))
    x = x / (x.max() + 1e-9)
    return np.nan_to_num(x)


def fetch_one(name, ra, dec, outdir_prev, radius_deg=0.02):
    coord = SkyCoord(ra * u.deg, dec * u.deg)

    obs = Observations.query_criteria(
        coordinates=coord,
        radius=radius_deg * u.deg,
        obs_collection="HST",
        instrument_name="ACS/WFC",
        filters="F814W",
        dataproduct_type="image",
    )
    if len(obs) == 0:
        return None, "no ACS/WFC F814W obs at these coords"

    # prefer calibrated/drizzled science products
    prods = Observations.get_product_list(obs)
    prods = Observations.filter_products(
        prods,
        productType=["SCIENCE"],
        extension="fits",
    )
    # keep drizzled mosaics (DRZ/DRC) -- WCS-calibrated, science-ready
    mask = np.array([
        ("drz" in str(fn).lower() or "drc" in str(fn).lower())
        for fn in prods["productFilename"]
    ])
    drz = prods[mask] if mask.any() else prods
    if len(drz) == 0:
        return None, "no science FITS products"

    last_err = "no product yielded a valid cutout"
    for row in drz[:6]:  # try a few until one cuts out cleanly
        try:
            dl = Observations.download_products(
                row, download_dir="mast_cache", mrp_only=False
            )
            path = dl["Local Path"][0]
        except Exception as e:
            last_err = f"download failed: {e}"
            continue

        try:
            with fits.open(path, memmap=True) as hdul:
                sci = next((h for h in hdul
                            if h.data is not None and h.data.ndim == 2
                            and ("SCI" in (h.name or "") or h.header.get("EXTNAME", "") == "SCI")),
                           None)
                if sci is None:
                    sci = next((h for h in hdul if h.data is not None and h.data.ndim == 2), None)
                if sci is None:
                    last_err = "no 2D image extension"
                    continue
                data = np.asarray(sci.data, dtype=np.float32)
                wcs = WCS(sci.header)

            cut = Cutout2D(data, coord, size=BOX_ARCSEC * u.arcsec, wcs=wcs, mode="partial",
                           fill_value=0.0)
            arr = np.nan_to_num(cut.data, nan=0.0)
            if arr.shape[0] < 8 or arr.shape[1] < 8:
                last_err = "cutout too small (lens near frame edge?)"
                continue

            factor = (NPIX / arr.shape[0], NPIX / arr.shape[1])
            img = zoom(arr, factor, order=1).astype(np.float32)

            fig, ax = plt.subplots(figsize=(3, 3))
            ax.imshow(asinh_display(img), origin="lower", cmap="gray")
            ax.set_title(name, fontsize=8)
            ax.axhline(NPIX / 2, color="r", lw=0.4, alpha=0.4)
            ax.axvline(NPIX / 2, color="r", lw=0.4, alpha=0.4)
            ax.set_xticks([]); ax.set_yticks([])
            fig.savefig(os.path.join(outdir_prev, f"{name}.png"),
                        dpi=110, bbox_inches="tight")
            plt.close(fig)
            return img, None
        except Exception as e:
            last_err = f"cutout failed: {e}"
            continue
    return None, last_err


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--labels", default="slacs_labels.csv")
    ap.add_argument("--out", default="real_slacs_images.h5")
    ap.add_argument("--limit", type=int, default=None, help="only first N lenses (smoke test)")
    args = ap.parse_args()

    df = pd.read_csv(args.labels)
    if args.limit:
        df = df.head(args.limit)
    os.makedirs("previews", exist_ok=True)

    images, names, kept_theta, kept_q = [], [], [], []
    for i, r in df.iterrows():
        img, err = fetch_one(r["name"], r["ra_deg"], r["dec_deg"], "previews")
        if img is None:
            print(f"  [skip] {r['name']:>16}: {err}")
            continue
        images.append(img[None, :, :])  # [1,128,128]
        names.append(str(r["name"]))
        kept_theta.append(r["theta_E_pub"])
        kept_q.append(r.get("q_pub", np.nan))
        print(f"  [ok]   {r['name']:>16}: cutout saved "
              f"(theta_E_pub={r['theta_E_pub']:.2f}\")")

    if not images:
        print("No cutouts produced. Check network access to MAST from the cluster, "
              "or inspect the skip reasons above.")
        return

    images = np.stack(images).astype(np.float32)
    with h5py.File(args.out, "w") as f:
        f.create_dataset("images", data=images)
        f.create_dataset("names", data=np.array(names, dtype="S32"))
        f.create_dataset("theta_E_pub", data=np.array(kept_theta, dtype=np.float32))
        f.create_dataset("q_pub", data=np.array(kept_q, dtype=np.float32))
        f.attrs["pixscale_arcsec"] = BOX_ARCSEC / NPIX  # 0.05 "/px
        f.attrs["box_arcsec"] = BOX_ARCSEC
    print(f"\nWROTE {len(images)} cutouts -> {args.out} "
          f"(pixscale {BOX_ARCSEC/NPIX:.4f}\"/px). Previews in ./previews/")
    print("EYEBALL the previews first: lens centred on the red cross, arc visible.")


if __name__ == "__main__":
    main()
