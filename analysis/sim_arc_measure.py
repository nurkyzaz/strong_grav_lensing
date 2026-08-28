"""Measure our GEN5 sim arc photometry vs real Q1. Arc-only native render =
sub/image_*.npy (ZP 25.94, arc = lensed source before deflector light). Deflector
native mag is in euclid.h5 (FJ). The arc-DEFLECTOR contrast cancels the
native<->VIS offset, so it is directly comparable to real (+1.0 mag median)."""
import glob
import sys

import h5py
import numpy as np

P = sys.argv[1]
ZP = 25.94
VIS_OFFSET = 2.48  # native->VIS (FJ: native defl 18.9 <-> real VIS 21.4)

with h5py.File(P + "/euclid.h5", "r") as f:
    dmag = f["deflector_mag"][:]        # native FJ mag
    th = f["theta_E"][:]
files = sorted(glob.glob(P + "/sub/image_*.npy"))
arc_nat = np.array([ZP - 2.5 * np.log10(max(float(np.load(fn).sum()), 1e-9))
                    for fn in files])
n = min(len(arc_nat), len(dmag))
arc_nat, dmag, th = arc_nat[:n], dmag[:n], th[:n]
contrast = arc_nat - dmag


def qq(name, x, *, real=None):
    x = x[np.isfinite(x)]
    s = "  %-30s q25/50/75 = %7.3f /%7.3f /%7.3f" % (
        name, *np.percentile(x, [25, 50, 75]))
    if real:
        s += "   | REAL %s" % real
    print(s)


print("GEN5 sim (%s)  N=%d\n" % (P.split("/")[-1], n))
qq("arc mag NATIVE", arc_nat)
qq("arc mag ->VIS (native+%.2f)" % VIS_OFFSET, arc_nat + VIS_OFFSET,
   real="21.81/22.28/22.75")
qq("deflector mag NATIVE", dmag)
qq("deflector mag ->VIS", dmag + VIS_OFFSET, real="20.35/21.39/22.13")
qq("ARC - DEFLECTOR contrast", contrast, real="0.35/1.00/1.65 (+=arc fainter)")
print("\n(contrast is offset-independent -> the clean apples-to-apples number)")
