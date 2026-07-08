#!/usr/bin/env python
"""
check_drc_wht.py
Report what uncertainty information the cached HST drizzled frames actually carry,
so we know how to build a per-pixel variance / uncertainty map.

Prints, for the first few *_drc.fits in the MAST cache:
  - the extension list (SCI / WHT / CTX ...)
  - the drizzle weight type (WHT_TYPE / D001WTYP): IVM vs EXP vs ERR
  - EXPTIME and the SCI BUNIT (flux units)
  - whether variance = 1/WHT is valid (IVM) or a noise model is needed (EXP)

Usage:
    python check_drc_wht.py                 # scans ./mast_cache
    python check_drc_wht.py some_dir        # scan another dir
"""
import sys
import glob
import os
from astropy.io import fits


def hdr_get(hdrs, *keys):
    for h in hdrs:
        for k in keys:
            if k in h:
                return h[k]
    return None


def main():
    root = sys.argv[1] if len(sys.argv) > 1 else "mast_cache"
    files = sorted(glob.glob(os.path.join(root, "**", "*_drc.fits"), recursive=True))
    if not files:
        files = sorted(glob.glob(os.path.join(root, "**", "*_drz.fits"), recursive=True))
    if not files:
        sys.exit(f"no *_drc.fits / *_drz.fits found under {root}/")

    print(f"found {len(files)} drizzled frame(s); inspecting up to 3\n")
    for path in files[:3]:
        print("=" * 70)
        print(os.path.basename(path))
        with fits.open(path) as hdul:
            exts = [(i, h.header.get("EXTNAME", "PRIMARY"),
                     None if h.data is None else h.data.shape) for i, h in enumerate(hdul)]
            for i, name, shp in exts:
                print(f"  ext[{i}] {name:8s} shape={shp}")
            hdrs = [h.header for h in hdul]
            wtyp = hdr_get(hdrs, "WHT_TYPE", "D001WTYP", "WHTTYPE")
            exptime = hdr_get(hdrs, "EXPTIME")
            bunit = hdr_get(hdrs, "BUNIT")
            print(f"  WHT_TYPE = {wtyp}")
            print(f"  EXPTIME  = {exptime}")
            print(f"  SCI BUNIT = {bunit}")
            if wtyp and "IVM" in str(wtyp).upper():
                print("  -> WHT is INVERSE-VARIANCE: variance = 1/WHT, sigma = 1/sqrt(WHT). Clean.")
            elif wtyp and "EXP" in str(wtyp).upper():
                print("  -> WHT is EXPOSURE TIME: NOT variance. Build noise model "
                      "(sky RMS + Poisson via EXPTIME).")
            else:
                print(f"  -> WHT type '{wtyp}' unrecognized; will use sky-RMS + Poisson model.")
    print("=" * 70)
    print("Report the WHT_TYPE line back -- it decides how we build the uncertainty map.")


if __name__ == "__main__":
    main()
