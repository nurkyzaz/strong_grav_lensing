#!/usr/bin/env python
"""G5 Path A data prep (Nurkyz ruling 2026-07-14, option c): convert Roman DC
Rung 0 h5s into our training format (datasets `lensed` + `theta_E`).

Outputs (all in ~/einstein_cnn/):
  train_rung0_f106.h5 / val_rung0_f106.h5      (N,128,128)   single band
  train_rung0_3band.h5 / val_rung0_3band.h5    (N,3,128,128) F106/F129/F158
  eval_rung0_unlabeled_f106.h5 / _3band.h5     + uid order for the
                                                submission CSV (`names`)
Grid: their 91x91 @ 0.11" (10.01") -> bilinear zoom x128/91 to 128 px
(0.0782"/px). Self-contained domain: train and test share the convention, so
no cross-convention hazard (the #24 lesson). Split: seeded 1000-lens val
(sim-val for selection; also our pre-submission score estimate). Labels kept
UNfiltered here — theta_e 0.16-3.6; the train-time filter flags must be
opened to --min_theta_e 0.1 --max_theta_e 3.7 (24% of the set is below the
old 0.45 floor).
"""
import argparse
import os

import h5py
import numpy as np
from scipy.ndimage import zoom

BASE = os.path.expanduser("~/cosmos_acs/roman_dc")
EC = os.path.expanduser("~/einstein_cnn")
BANDS = ["F106", "F129", "F158"]
VAL_N = 1000
SEED = 20260714

ap = argparse.ArgumentParser()
ap.add_argument("--labeled", action="store_true")
ap.add_argument("--unlabeled", action="store_true")
a = ap.parse_args()


def load_groups(fn, with_theta):
    f = h5py.File(fn, "r")
    g = f["images"]
    keys = sorted(g.keys())
    n = len(keys)
    ims = np.empty((n, 3, 128, 128), np.float32)
    th = np.empty(n, np.float32) if with_theta else None
    uids = []
    zf = 128.0 / 91.0
    for i, k in enumerate(keys):
        grp = g[k]
        uid = str(grp.attrs["uid"][0])
        uids.append(uid)
        for b, band in enumerate(BANDS):
            im = grp["exposure_%s_%s" % (uid, band)][:].astype(np.float32)
            ims[i, b] = zoom(im, zf, order=1)
        if with_theta:
            th[i] = float(grp.attrs["theta_e"][0])
        if i % 2000 == 0:
            print("  %d/%d" % (i, n), flush=True)
    return uids, ims, th


def write(fn, ims, th, uids):
    with h5py.File(fn, "w") as f:
        f.create_dataset("lensed", data=ims)
        if th is not None:
            f.create_dataset("theta_E", data=th)
        sd = h5py.special_dtype(vlen=str)
        f.create_dataset("names", data=np.array(uids, object), dtype=sd)
    print("wrote %s  %s" % (fn, ims.shape))


if a.labeled:
    uids, ims, th = load_groups(os.path.join(BASE, "roman_data_challenge_rung_0_v_2_1.h5"), True)
    print("labeled: N=%d  theta q10/50/90 = %.2f/%.2f/%.2f  [%.2f, %.2f]"
          % (len(uids), *np.percentile(th, [10, 50, 90]), th.min(), th.max()))
    rng = np.random.default_rng(SEED)
    order = rng.permutation(len(uids))
    vi, ti = order[:VAL_N], order[VAL_N:]
    for tag, idx in (("train", ti), ("val", vi)):
        sel_u = [uids[j] for j in idx]
        write(os.path.join(EC, "%s_rung0_3band.h5" % tag), ims[idx], th[idx], sel_u)
        write(os.path.join(EC, "%s_rung0_f106.h5" % tag), ims[idx][:, 0], th[idx], sel_u)
    # quick gate stats on F106
    x = ims[ti[:500], 0]
    sky = np.median(x[:, :12, :12], axis=(1, 2))
    rms = np.median(np.abs(x[:, :12, :12] - sky[:, None, None]), axis=(1, 2)) * 1.4826
    peak = np.percentile(x.reshape(len(x), -1), 99.9, axis=1)
    print("F106 gate stats: sky med %.4g  skyRMS med %.4g  peak/sky med %.0f"
          % (np.median(sky), np.median(rms), np.median((peak - sky) / np.maximum(rms, 1e-9))))
    # preview page: 12 systems x 3 stretches (F106)
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    sel = rng.choice(ti, 12, replace=False)
    fig, axes = plt.subplots(3, 12, figsize=(24, 7))
    for j, i in enumerate(sel):
        im = ims[i, 0]
        r = max(np.std(im[:12, :12]), 1e-9)
        for row, dat in enumerate((im, np.clip(im, np.percentile(im, 1), np.percentile(im, 99)),
                                   np.arcsinh((im - np.median(im[:12, :12])) / r))):
            axes[row][j].imshow(dat, origin="lower", cmap="gray")
            axes[row][j].axis("off")
        axes[0][j].set_title("%s\nth=%.2f" % (uids[i], th[i]), fontsize=6)
    plt.suptitle("Rung 0 F106 training previews (linear/pct/asinh), 128px grid")
    plt.tight_layout()
    plt.savefig(os.path.join(BASE, "rung0_train_preview.png"), dpi=110)
    print("preview written")

if a.unlabeled:
    uids, ims, _ = load_groups(
        os.path.join(BASE, "roman_data_challenge_rung_0_unlabeled_v_2_1.h5"), False)
    print("unlabeled: N=%d" % len(uids))
    write(os.path.join(EC, "eval_rung0_unlabeled_3band.h5"), ims, None, uids)
    write(os.path.join(EC, "eval_rung0_unlabeled_f106.h5"), ims[:, 0], None, uids)
