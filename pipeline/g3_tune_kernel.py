#!/usr/bin/env python
"""G3-2: tune the matching-kernel window; diagnose where the residual lives.
Picks the window minimizing a weighted score (core exactness + wing match),
saves the winner over acs2vis_matching_kernel.npy."""
import glob
import json

import numpy as np
from photutils.psf.matching import (CosineBellWindow, HanningWindow,
                                    SplitCosineBellWindow, TukeyWindow,
                                    create_matching_kernel)
from scipy.ndimage import zoom
from scipy.signal import fftconvolve

SIZE = 67


def centred(img, size):
    out = np.zeros((size, size))
    c = size // 2
    h = img.shape[0] // 2
    y0 = c - h
    out[y0:y0 + img.shape[0], y0:y0 + img.shape[1]] = img
    return out


vis = np.load("/home/user/nurkyz/cosmos_acs/tiles/vis_psf_q1.npy")
vis_up = np.clip(zoom(vis, 2.0, order=3), 0, None)[:-1, :-1]
vis_t = centred(vis_up / vis_up.sum(), SIZE)

ks = sorted(glob.glob(
    "/home/user/nurkyz/cosmos_acs/tiles/psf_bank_v2/kernel_*_extended.npy"))
acc = None
for fn in ks[:80]:
    k = np.load(fn).astype("float64")
    k /= k.sum()
    if k.shape[0] <= SIZE:
        kc = centred(k, SIZE)
    else:
        h = k.shape[0] // 2
        c0 = h - SIZE // 2
        kc = k[c0:c0 + SIZE, c0:c0 + SIZE]
        kc /= kc.sum()
    acc = kc if acc is None else acc + kc
acs = acc / acc.sum()

yy, xx = np.mgrid[-(SIZE // 2):SIZE // 2 + 1, -(SIZE // 2):SIZE // 2 + 1]
r = np.hypot(xx, yy) * 0.05
core = r < 0.15
wing = (r >= 0.15) & (r < 0.5)

wins = [("cosbell0.15", CosineBellWindow(alpha=0.15)),
        ("cosbell0.35", CosineBellWindow(alpha=0.35)),
        ("cosbell0.6", CosineBellWindow(alpha=0.6)),
        ("tukey0.3", TukeyWindow(alpha=0.3)),
        ("tukey0.6", TukeyWindow(alpha=0.6)),
        ("hanning", HanningWindow()),
        ("splitcos0.2_0.3", SplitCosineBellWindow(alpha=0.3, beta=0.2))]
best = None
for name, w in wins:
    K = create_matching_kernel(acs, vis_t, window=w)
    conv = fftconvolve(acs, K, mode="same")
    resid = np.linalg.norm(conv - vis_t) / np.linalg.norm(vis_t)
    core_r = np.abs(conv[core] - vis_t[core]).sum() / vis_t[core].sum()
    wing_r = np.abs(conv[wing] - vis_t[wing]).sum() / vis_t[wing].sum()
    neg = -K.min() / K.max()
    score = core_r + wing_r
    print("%-16s L2 %.3f  core %.3f  wing %.3f  neg %.3f  sum %.4f"
          % (name, resid, core_r, wing_r, neg, K.sum()))
    if best is None or score < best[1]:
        best = (name, score, K, conv, core_r, wing_r)

name, score, K, conv, core_r, wing_r = best
print("\nWINNER:", name, "core", core_r, "wing", wing_r)
prof = lambda p, lo, hi: p[(r >= lo) & (r < hi)].mean()
for lo, hi in ((0, 0.05), (0.05, 0.1), (0.1, 0.2), (0.2, 0.3), (0.3, 0.5)):
    print("  r %/.2f-%.2f\": conv %.3e target %.3e".replace("%/", "%")
          % (lo, hi, prof(conv, lo, hi), prof(vis_t, lo, hi)))
np.save("/home/user/nurkyz/cosmos_acs/tiles/acs2vis_matching_kernel.npy", K)
meta = json.load(open(
    "/home/user/nurkyz/cosmos_acs/tiles/acs2vis_kernel_provenance.json"))
meta.update(window=name, core_resid=float(core_r), wing_resid=float(wing_r))
json.dump(meta, open(
    "/home/user/nurkyz/cosmos_acs/tiles/acs2vis_kernel_provenance.json", "w"),
    indent=2)
print("saved winner kernel + provenance")
