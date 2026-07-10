#!/usr/bin/env python
"""Diagnose Nurkyz's three observations on real_vs_sim_euc_selected.png:
1. 5/8 sim arcs invisible by eye despite passing SNR>0.7 -> check the displayed
   panels' arc SNRs (eye-calibration was done on NATIVE panels; Euclid glare
   may need a higher threshold or a contrast term).
2. SIM #11 abrupt deflector-light edge -> check its backdrop cutout for a
   large-scale gradient (suspected empty-cutout outlier).
3. 'sim arcs look smaller' -> theta_E of displayed panels vs real; arc
   footprint extent distribution.
side_by_side seed 5 selects 8 indices from the selected h5 the same way.
"""
import numpy as np
import h5py

SEL = "/home/user/nurkyz/einstein_cnn/euc_sel_pilot_selected.h5"
EMPTY = "/home/user/nurkyz/cosmos_acs/tiles/empty_cutouts_4k.h5"

with h5py.File(SEL, "r") as f:
    snr = f["arc_snr"][:]
    th = f["theta_E"][:]
    ci = f["cutout_index"][:] if "cutout_index" in f else None
    n = len(snr)

# replicate side_by_side's selection (seed 5)
rng = np.random.default_rng(5)
idx = rng.choice(n, size=8, replace=False)
print("displayed sim panels (selected-h5 indices):")
for i in idx:
    line = "  #%d  theta_E=%.2f  arc_snr=%.2f" % (i, th[i], snr[i])
    if ci is not None:
        line += "  cutout_index=%d" % ci[i]
    print(line)
print("displayed theta_E median %.2f | full-selected median %.2f" %
      (np.median(th[idx]), np.median(th)))
print("real benchmark theta_E (Bolton): median ~1.17, range 0.69-1.78")

# backdrop gradient check for the displayed panels' cutouts
if ci is not None:
    with h5py.File(EMPTY, "r") as f:
        key = "empty" if "empty" in f else list(f.keys())[0]
        emp = f[key]
        print("\nbackdrop gradient check (plane-fit amplitude / noise):")
        yy, xx = np.mgrid[0:128, 0:128]
        A = np.c_[xx.ravel(), yy.ravel(), np.ones(128 * 128)]
        for i in idx:
            c = emp[int(ci[i])]
            coef, *_ = np.linalg.lstsq(A, c.ravel(), rcond=None)
            plane = (A @ coef).reshape(128, 128)
            grad_amp = plane.max() - plane.min()
            resid = c - plane
            mad = np.median(np.abs(resid - np.median(resid))) * 1.4826
            print("  panel #%d cutout %d: gradient amp / noise = %.1f"
                  % (i, ci[i], grad_amp / mad if mad > 0 else np.inf))

# arc footprint extent of the whole selected set (euclidised arcs folder gone
# for the pilot? it was deleted at job end -- use stored SNR only). Extent from
# native pilot arcs folder if still present:
import glob, os
arcdir = os.path.expanduser("/home/user/nurkyz/paltas_euc_sel_pilot")
files = sorted(glob.glob(os.path.join(arcdir, "image_*.npy")))
print("\nnative arc npys still present: %d (deleted at job end if 0)" % len(files))
