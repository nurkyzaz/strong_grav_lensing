#!/usr/bin/env python
"""Concatenate the G1 chunk h5s (images/names/survey/theta_E_pub + scalars)."""
import glob
import sys
import numpy as np
import h5py

pat, out = sys.argv[1], sys.argv[2]
files = sorted(glob.glob(pat))
print("chunks:", len(files))
imgs, names, surveys, thetas = [], [], [], []
box = pix = None
for fn in files:
    with h5py.File(fn, "r") as f:
        imgs.append(f["images"][:])
        names.append(f["names"][:])
        surveys.append(f["survey"][:])
        thetas.append(f["theta_E_pub"][:])
        box, pix = float(f["box_arcsec"][()]), float(f["pixscale"][()])
with h5py.File(out, "w") as f:
    f.create_dataset("images", data=np.concatenate(imgs))
    f.create_dataset("names", data=np.concatenate(names))
    f.create_dataset("survey", data=np.concatenate(surveys))
    f.create_dataset("theta_E_pub", data=np.concatenate(thetas))
    f.create_dataset("box_arcsec", data=box)
    f.create_dataset("pixscale", data=pix)
    print("%s: %d cutouts" % (out, f["images"].shape[0]))
