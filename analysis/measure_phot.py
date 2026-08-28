"""Photometry vs real Q1 (VIS = native, euclidise preserves AB mag). Arg: pilot dir."""
import glob
import sys

import h5py
import numpy as np

P = sys.argv[1]
d = h5py.File(P + "/euclid.h5", "r")["deflector_mag"][:]
a = np.array([25.94 - 2.5 * np.log10(max(float(np.load(f).sum()), 1e-9))
              for f in sorted(glob.glob(P + "/sub/image_*.npy"))])
n = min(len(d), len(a))
d, a = d[:n], a[:n]
c = a - d


def q(x):
    return np.round(np.percentile(x, [25, 50, 75]), 2)


print("  deflector mag ", q(d), " | REAL 20.35/21.39/22.13")
print("  arc mag       ", q(a), " | REAL 21.81/22.28/22.75")
print("  contrast a-d  ", q(c), " | REAL 0.35/1.00/1.65")
