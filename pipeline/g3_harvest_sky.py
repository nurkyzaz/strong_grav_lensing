#!/usr/bin/env python
"""G3-3: harvest real Euclid Q1 VIS empty-sky cutouts (128 px @ 0.1"/px)
around a MER tile centre, via IRSA server-side cutouts (no tile download).

Emptiness screen (two levels, thresholds logged in the output h5):
  1. catalogue: no source brighter than --maxmag (VIS ZP 24.6) within
     --clear_r arcsec of the cutout centre;
  2. pixels: finite everywhere, robust sky sigma within a sane band, and no
     pixel in the central 6.4" brighter than --max_central_sigma * sigma
     (keeps faint real companions near the edges — that's the point — but
     rejects stars/ghosts that would sit under the injected deflector).

Usage:
  g3_harvest_sky.py --ra 52.93 --dec -28.09 --n 600 --seed 41 --out euclid_sky_edff_1.h5
"""
import argparse
import gzip
import io
import json
import os

import h5py
import numpy as np
import pyvo
import requests
from astropy.io import fits

ZP_Q1 = 24.6      # MER MAGZERO (probe-verified)
PIX = 0.1
STAMP = 128       # px -> 12.8"

ap = argparse.ArgumentParser()
ap.add_argument("--ra", type=float, required=True)
ap.add_argument("--dec", type=float, required=True)
ap.add_argument("--n", type=int, default=600)
ap.add_argument("--seed", type=int, default=41)
ap.add_argument("--out", required=True)
ap.add_argument("--maxmag", type=float, default=23.5)
ap.add_argument("--clear_r", type=float, default=6.0)
ap.add_argument("--sample_r_deg", type=float, default=0.2)
ap.add_argument("--max_central_sigma", type=float, default=8.0)
ap.add_argument("--max_tries", type=int, default=4000)
a = ap.parse_args()
rng = np.random.default_rng(a.seed)

svc = pyvo.dal.SIA2Service("https://irsa.ipac.caltech.edu/SIA")
rows = [r for r in svc.search(pos=(a.ra, a.dec, 0.05)).to_table()
        if str(r["obs_collection"]) == "euclid_DpdMerBksMosaic"
        and "BGSUB-MOSAIC-VIS_" in str(r["access_url"])]
assert rows, "no VIS mosaic at this position"
url = str(rows[0]["access_url"])
print("tile:", url.split("/")[-1][:60])

flim = 10.0 ** (0.4 * (ZP_Q1 - a.maxmag))
tap = pyvo.dal.TAPService("https://irsa.ipac.caltech.edu/TAP")
q = ("SELECT ra, dec FROM euclid_q1_mer_catalogue "
     "WHERE CONTAINS(POINT('ICRS', ra, dec), CIRCLE('ICRS', %f, %f, %f)) = 1 "
     "AND flux_detection_total > %f" % (a.ra, a.dec, a.sample_r_deg + 0.01, flim))
bright = tap.search(q).to_table()
bra = np.array(bright["ra"], dtype="float64")
bdec = np.array(bright["dec"], dtype="float64")
cosd = np.cos(np.radians(a.dec))
print("bright sources (mag<%.1f) in field: %d" % (a.maxmag, len(bra)))

imgs, ras, decs = [], [], []
tried = 0
rej_cat = rej_pix = rej_http = 0
while len(imgs) < a.n and tried < a.max_tries:
    tried += 1
    dra = rng.uniform(-a.sample_r_deg, a.sample_r_deg) / cosd
    ddec = rng.uniform(-a.sample_r_deg, a.sample_r_deg)
    ra, dec = a.ra + dra, a.dec + ddec
    sep2 = ((bra - ra) * cosd * 3600.0) ** 2 + ((bdec - dec) * 3600.0) ** 2
    if sep2.min() < a.clear_r ** 2:
        rej_cat += 1
        continue
    try:
        rsp = requests.get(url + "?center=%f,%f&size=%farcsec"
                           % (ra, dec, STAMP * PIX), timeout=60)
        raw = rsp.content
        if raw[:2] == b"\x1f\x8b":
            raw = gzip.decompress(raw)
        if raw[:6] != b"SIMPLE":
            rej_http += 1
            continue
        with fits.open(io.BytesIO(raw)) as hdul:
            d = None
            for x in hdul:
                if x.data is not None and x.data.ndim == 2:
                    d = x.data.astype("float32")
                    break
    except Exception:
        rej_http += 1
        continue
    if d is None or d.shape[0] < STAMP or d.shape[1] < STAMP:
        rej_pix += 1
        continue
    o = (d.shape[0] - STAMP) // 2
    d = d[o:o + STAMP, o:o + STAMP]
    if not np.isfinite(d).all():
        rej_pix += 1
        continue
    lo, med, hi = np.percentile(d, [16, 50, 84])
    sig = (hi - lo) / 2.0
    if not (5e-4 < sig < 2e-2):          # dead / wildly abnormal region
        rej_pix += 1
        continue
    c = d[STAMP // 4: 3 * STAMP // 4, STAMP // 4: 3 * STAMP // 4]
    if (c - med).max() > a.max_central_sigma * sig:
        rej_pix += 1
        continue
    imgs.append(d - med)                 # background-centred, like the pool
    ras.append(ra)
    decs.append(dec)
    if len(imgs) % 50 == 0:
        print("  %d/%d (tried %d)" % (len(imgs), a.n, tried), flush=True)

print("accepted %d / tried %d (cat %d, pix %d, http %d rejects)"
      % (len(imgs), tried, rej_cat, rej_pix, rej_http))
with h5py.File(a.out, "w") as f:
    f.create_dataset("images", data=np.stack(imgs))
    f.create_dataset("ra", data=np.array(ras))
    f.create_dataset("dec", data=np.array(decs))
    f.attrs["magzero"] = ZP_Q1
    f.attrs["pix_arcsec"] = PIX
    f.attrs["source_url"] = url
    f.attrs["screen"] = json.dumps(dict(maxmag=a.maxmag, clear_r=a.clear_r,
                                        max_central_sigma=a.max_central_sigma))
print("wrote", a.out)
