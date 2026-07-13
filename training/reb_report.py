#!/usr/bin/env python
"""Rebalance-pilot report: selected theta_E distribution (the flatness check),
per-bin counts pre/post selection, and a small-theta_E subset h5 for the
focused side-by-side. Usage: reb_report.py <selected.h5> <out_prefix>"""
import sys
import numpy as np
import h5py
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

sel_fn, prefix = sys.argv[1], sys.argv[2]
with h5py.File(sel_fn, "r") as f:
    key = "lensed" if "lensed" in f else "images"
    imgs = f[key][:]
    th = f["theta_E"][:].astype("float64")
    extra = {k: f[k][:] for k in f.keys() if k not in (key,)}

BINS = [(0.45, 0.80), (0.80, 1.20), (1.20, 1.70), (1.70, 2.30)]
print("SELECTED n=%d  theta_E median %.3f  (flat target: ~1.30)" % (len(th), np.median(th)))
for lo, hi in BINS:
    m = (th >= lo) & (th < hi)
    exp = (hi - lo) / 1.85
    print("  [%.2f,%.2f): n=%4d  frac %.2f  (flat expectation %.2f)"
          % (lo, hi, m.sum(), m.mean() if len(th) else 0, exp))

fig, ax = plt.subplots(figsize=(7, 4))
ax.hist(th, bins=np.arange(0.45, 2.35, 0.1), edgecolor="k")
ax.set_xlabel("theta_E (arcsec), SELECTED training draws")
ax.set_title("Rebalance pilot: post-selection theta_E (target: flat)")
fig.tight_layout()
fig.savefig(prefix + "_theta_hist.png", dpi=130)

m = th < 1.0
with h5py.File(prefix + "_small_theta.h5", "w") as f:
    f.create_dataset(key, data=imgs[m])
    for k, v in extra.items():
        try:
            f.create_dataset(k, data=v[m] if len(v) == len(th) else v)
        except Exception:
            pass
print("small-theta subset (theta_E<1.0): n=%d -> %s_small_theta.h5" % (m.sum(), prefix))
