#!/usr/bin/env python
"""R1.2b premise check, step 1: Euclidise the kept seed-111 noiseless arc-only
renders (flux + PSF + rebin, NO noise) so arc SNR can be computed in the
Euclidised domain against euclid_sim_pilot.h5 (same seeds, same operator)."""
import glob
import os
import numpy as np
import sys

sys.path.insert(0, os.path.expanduser("~/einstein_cnn"))
from euclidise import euclidise

SRC = os.path.expanduser(sys.argv[1] if len(sys.argv) > 1
                         else "~/paltas_arcs_seed111_keep")
DST = os.path.expanduser(sys.argv[2] if len(sys.argv) > 2
                         else "~/paltas_arcs_seed111_euclid")
os.makedirs(DST, exist_ok=True)
rng = np.random.default_rng(1)
files = sorted(glob.glob(os.path.join(SRC, "image_*.npy")))
for fn in files:
    arc = np.load(fn).astype("float64")
    out = euclidise(arc, rng, add_noise=False)
    np.save(os.path.join(DST, os.path.basename(fn)), out.astype("float32"))
print("euclidised %d arc renders -> %s" % (len(files), DST))
