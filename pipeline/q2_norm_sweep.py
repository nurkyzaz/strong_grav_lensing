#!/usr/bin/env python
"""Q2c2 NORMALIZATION SWEEP (Nurkyz ruling 2026-07-13) — prepared, runs ONLY
on explicit go-ahead (sbatch q2_norm_sweep.sbatch). Option A: rescale real Q1
VIS cutouts into the training-domain flux convention; NO retraining.

Tunes (rescale factor x sky pedestal) on the TUNING SUBSET ONLY (default: the
10-lens pilot set — these lenses are burned for tuning and get dual-reported
at Q2e). Selection metric: lowest RMSE (R2 reported alongside) vs PyAutoLens
SIE einstein_radius_median_pdf. Every model pass on Q1 data is a logged
tuning-subset contact under C18 (this is NOT the official eval; Q2e = eval
#24 runs exactly once, after the winner is frozen and C17 re-verified).

Phases: --build (h5 per combo), --predict (G4 cnv2_3 members, TTA), --report.
"""
import argparse
import csv
import glob
import json
import os
import subprocess

import h5py
import numpy as np
from astropy.io import fits

BASE = os.path.expanduser("~/cosmos_acs/q1_slde")
LENS = os.path.join(BASE, "lens/lens")
TUNE = os.path.join(BASE, "tune")
EC = os.path.expanduser("~/einstein_cnn")
PY = os.path.expanduser("~/miniconda3/envs/Stronglensing/bin/python")

# C17 gate measurements (2026-07-13, q2_c17_gate.py vs euclid_slacs_images_g3):
BENCH_SKY = 0.01706        # benchmark median corner-sky pedestal
SKYRMS_MATCH = 11.4        # factor that matches median skyRMS
FACTORS = [1.91, 8.0, 10.0, SKYRMS_MATCH, 12.0, 14.0]  # 1.91 = ZP-only control
PEDESTALS = ["none", "bench"]                          # >= 12 combos total
MEMBERS = ["g4_cnv2_s1", "g4_cnv2_s2", "g4_cnv2_s3"]   # Euclid primary
G4_B = -0.0015423929634094113                          # frozen g4_recal.json
N_TUNE = 10

ap = argparse.ArgumentParser()
ap.add_argument("--build", action="store_true")
ap.add_argument("--predict", action="store_true")
ap.add_argument("--report", action="store_true")
a = ap.parse_args()


def tag(f, p):
    return "f%04.1f_%s" % (f, p)


def gt_table():
    fn = glob.glob(os.path.join(BASE, "modeling_lens_mass*.csv"))[0]
    gt = {}
    for r in csv.DictReader(open(fn)):
        gt[r["id_str"]] = float(r["einstein_radius_median_pdf"])
    return gt


def tuning_dirs():
    return sorted(glob.glob(LENS + "/*"))[:N_TUNE]


def preprocess(d):
    name = os.path.basename(d)
    vis = fits.open(os.path.join(d, name + ".fits"))["VIS_FLUX"].data.astype(float)
    c = vis.shape[0] // 2
    crop = vis[c - 32:c + 32, c - 32:c + 32]                # 64px @ 0.1" = 6.4"
    return np.repeat(np.repeat(crop, 2, 0), 2, 1) / 4.0     # 128 @ 0.05", flux-conserving


def corner_sky(im):
    k = 12
    corner = np.concatenate([im[:k, :k].ravel(), im[:k, -k:].ravel(),
                             im[-k:, :k].ravel(), im[-k:, -k:].ravel()])
    return float(np.median(corner))


if a.build:
    os.makedirs(TUNE, exist_ok=True)
    gt = gt_table()
    dirs = [d for d in tuning_dirs() if os.path.basename(d) in gt]
    names = [os.path.basename(d) for d in dirs]
    print("tuning subset (%d lenses, frozen, BURNED for tuning):" % len(names))
    for n in names:
        print("  %s  gt=%.3f" % (n, gt[n]))
    ims0 = np.stack([preprocess(d) for d in dirs])
    for f in FACTORS:
        for p in PEDESTALS:
            ims = ims0 * f
            if p == "bench":
                ims = ims + (BENCH_SKY - np.median([corner_sky(i) for i in ims]))
            fn = os.path.join(TUNE, "q2_tune_%s.h5" % tag(f, p))
            with h5py.File(fn, "w") as h:
                h.create_dataset("images", data=ims.astype(np.float32))
                h.create_dataset("theta_E_pub",
                                 data=np.array([gt[n] for n in names], np.float32))
                sd = h5py.special_dtype(vlen=str)
                h.create_dataset("names", data=np.array(names, object), dtype=sd)
                h.create_dataset("survey",
                                 data=np.array(["Q1SLDE"] * len(names), object), dtype=sd)
                h.create_dataset("box_arcsec", data=np.float32(6.4))
                h.create_dataset("pixscale", data=np.float32(0.05))
            print("wrote %s  (skyRMS med of set now vs bench 0.008: check in report)" % fn)
    json.dump(dict(names=names, factors=FACTORS, pedestals=PEDESTALS,
                   bench_sky=BENCH_SKY, members=MEMBERS),
              open(os.path.join(TUNE, "sweep_config.json"), "w"), indent=1)

if a.predict:
    for f in FACTORS:
        for p in PEDESTALS:
            t = tag(f, p)
            for m in MEMBERS:
                out = "preds_q2tune_%s_%s.csv" % (m, t)
                subprocess.check_call(
                    [PY, os.path.join(EC, "predict_real_lenses_paltas.py"),
                     "--ckpt", os.path.join(EC, m + ".pt"),
                     "--real", os.path.join(TUNE, "q2_tune_%s.h5" % t),
                     "--tta", "--outdir", TUNE, "--out", out], cwd=EC)

if a.report:
    cfg = json.load(open(os.path.join(TUNE, "sweep_config.json")))
    print("Q2c2 SWEEP REPORT — ens = mean(%s) + B(g4_recal)" % ",".join(MEMBERS))
    print("%-14s %8s %8s %8s %8s %6s" % ("combo", "bias", "RMSE", "NMAD", "R2", "fail%"))
    best = None
    for f in FACTORS:
        for p in PEDESTALS:
            t = tag(f, p)
            mus, gt_v = [], None
            for m in MEMBERS:
                fn = os.path.join(TUNE, "preds_q2tune_%s_%s.csv" % (m, t))
                rows = list(csv.DictReader(open(fn)))
                mus.append([float(r["theta_E_pred_arcsec"]) for r in rows])
                gt_v = [float(r["theta_E_pub_arcsec"]) for r in rows]
            pred = np.mean(mus, 0) + G4_B
            tt = np.array(gt_v)
            d = pred - tt
            rmse = float(np.sqrt((d ** 2).mean()))
            r2 = float(1 - (d ** 2).sum() / ((tt - tt.mean()) ** 2).sum())
            nmad = float(1.4826 * np.median(np.abs(d - np.median(d))))
            fail = float((np.abs(d / tt) > 0.15).mean())
            print("%-14s %+8.3f %8.3f %8.3f %+8.2f %5.0f%%"
                  % (t, d.mean(), rmse, nmad, r2, 100 * fail))
            if best is None or rmse < best[1]:
                best = (t, rmse, r2)
    print("WINNER (lowest RMSE): %s  RMSE %.3f  R2 %+.2f" % best)
    print("NEXT: freeze this normalization -> re-run q2_c17_gate.py on it -> "
          "only then ⛔ Q2e (eval #24), once, full set.")
