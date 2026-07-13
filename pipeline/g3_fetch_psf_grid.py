#!/usr/bin/env python
"""G3-2: resolve the exact GRID-PSF-VIS URL for the EDF-F test tile via SIA2
and download it to ~/g3_scratch (one-time ~1.5 GB transient; deleted after
stamp extraction). Also saves the resolved URLs for provenance."""
import json
import os

import pyvo
import requests

DST = os.path.expanduser("~/g3_scratch")
os.makedirs(DST, exist_ok=True)

svc = pyvo.dal.SIA2Service("https://irsa.ipac.caltech.edu/SIA")
res = svc.search(pos=(52.93, -28.09, 0.05))
urls = {}
for r in res.to_table():
    u = str(r["access_url"])
    if str(r["obs_collection"]) != "euclid_DpdMerBksMosaic":
        continue
    for tag in ("GRID-PSF-VIS_", "BGSUB-MOSAIC-VIS_", "CATALOG-PSF-VIS_"):
        if tag in u:
            urls[tag.rstrip("_")] = u
json.dump(urls, open(os.path.join(DST, "g3_tile_urls.json"), "w"), indent=2)
print(json.dumps(urls, indent=2))

u = urls["GRID-PSF-VIS"]
out = os.path.join(DST, "grid_psf_vis_102044185.fits")
print("downloading ->", out)
with requests.get(u, stream=True, timeout=300) as rsp:
    rsp.raise_for_status()
    tot = 0
    with open(out, "wb") as f:
        for chunk in rsp.iter_content(1 << 22):
            f.write(chunk)
            tot += len(chunk)
            if tot % (1 << 28) < (1 << 22):
                print("  %.1f GB" % (tot / 1e9), flush=True)
print("done: %.2f GB" % (tot / 1e9))
