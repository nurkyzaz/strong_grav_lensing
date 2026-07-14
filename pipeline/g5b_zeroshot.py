#!/usr/bin/env python
"""G5b ZERO-SHOT baseline (Nurkyz request 2026-07-14): existing models
(G4 cnv2_3 Euclid primary + g4ar r50_3) on the Rung 0 LABELED data —
public labels, so this is a logged baseline, not a ⛔ frozen-benchmark eval.

Evaluated on the SAME seeded 1000-lens challenge-val split Path A holds out,
so zero-shot vs their-trained are apples-to-apples on identical lenses.

Preprocessing (pre-registered, mirrors the frozen Q2 recipe): F106 crop
central 58 px @0.11" = 6.38" -> bilinear zoom to 128 px (0.0499"/px);
per-image corner-sky subtraction; global factor matching median skyRMS to
the euclid bench (0.008); + bench pedestal 0.01706. PSF/band caveat carried:
Roman F106 PSF (~0.09") is SHARPER than the VIS-matched training PSF
(0.16") and the band differs — expectations LOW by design; this row exists
to quantify pure cross-instrument transfer (G5b) before G5c.

Report: our conventions + THEIR grading (Ding+21 chi2/Precision/Accuracy),
sigma raw AND conformally scaled on this same split (labeled as such).
Phases: --build, --predict, --report."""
import argparse
import csv
import os
import subprocess

import h5py
import numpy as np
from scipy.ndimage import zoom

BASE = os.path.expanduser("~/cosmos_acs/roman_dc")
EC = os.path.expanduser("~/einstein_cnn")
H5 = os.path.join(BASE, "g5b_zeroshot_val1000.h5")
BENCH_RMS, BENCH_SKY = 0.008, 0.01706
MEMBERS_A = ["g4_cnv2_s1", "g4_cnv2_s2", "g4_cnv2_s3"]
MEMBERS_B = ["g4ar_r50_s1", "g4ar_r50_s2", "g4ar_r50_s3"]
B_A, S_A = -0.0015423929634094113, 0.9618278137772992
B_B, S_B = -0.0032367853597006224, 1.0152982705791773

ap = argparse.ArgumentParser()
ap.add_argument("--build", action="store_true")
ap.add_argument("--predict", action="store_true")
ap.add_argument("--report", action="store_true")
a = ap.parse_args()

if a.build:
    with h5py.File(os.path.join(EC, "val_rung0_f106.h5"), "r") as f:
        val_uids = [x.decode() if isinstance(x, bytes) else str(x) for x in f["names"][:]]
    src = h5py.File(os.path.join(BASE, "roman_data_challenge_rung_0_v_2_1.h5"), "r")["images"]
    ims, ths = [], []
    zf = 128.0 / 58.0
    for uid in val_uids:
        grp = src["strong_lens_%s" % uid]
        im = grp["exposure_%s_F106" % uid][:].astype(np.float64)
        c = im.shape[0] // 2
        crop = im[c - 29:c + 29, c - 29:c + 29]                # 58 px = 6.38"
        k = 6
        corner = np.concatenate([crop[:k, :k].ravel(), crop[:k, -k:].ravel(),
                                 crop[-k:, :k].ravel(), crop[-k:, -k:].ravel()])
        crop = crop - np.median(corner)
        ims.append(zoom(crop, zf, order=1))
        ths.append(float(grp.attrs["theta_e"][0]))
    ims = np.stack(ims)
    rms = []
    for im in ims[:300]:
        k = 12
        corner = np.concatenate([im[:k, :k].ravel(), im[:k, -k:].ravel(),
                                 im[-k:, :k].ravel(), im[-k:, -k:].ravel()])
        rms.append(1.4826 * np.median(np.abs(corner - np.median(corner))))
    factor = BENCH_RMS / np.median(rms)
    ims = ims * factor + BENCH_SKY
    print("skyRMS med %.4g -> factor %.3f (measured, logged)" % (np.median(rms), factor))
    with h5py.File(H5, "w") as h:
        h.create_dataset("images", data=ims.astype(np.float32))
        h.create_dataset("theta_E_pub", data=np.array(ths, np.float32))
        sd = h5py.special_dtype(vlen=str)
        h.create_dataset("names", data=np.array(val_uids, object), dtype=sd)
        h.create_dataset("survey", data=np.array(["Rung0"] * len(val_uids), object), dtype=sd)
        h.create_dataset("box_arcsec", data=np.float32(6.38))
        h.create_dataset("pixscale", data=np.float32(6.38 / 128))
    print("wrote %s N=%d" % (H5, len(val_uids)))

if a.predict:
    for m in MEMBERS_A + MEMBERS_B:
        subprocess.check_call(
            [os.path.expanduser("~/miniconda3/envs/Stronglensing/bin/python"),
             os.path.join(EC, "predict_real_lenses_paltas.py"),
             "--ckpt", os.path.join(EC, m + ".pt"), "--real", H5,
             "--tta", "--outdir", BASE, "--out", "preds_g5b_%s.csv" % m], cwd=EC)

if a.report:
    def load(members, B, S):
        mus, sigs, names, gt = [], [], None, None
        for m in members:
            rows = list(csv.DictReader(open(os.path.join(BASE, "preds_g5b_%s.csv" % m))))
            if names is None:
                names = [r["name"] for r in rows]
                gt = np.array([float(r["theta_E_pub_arcsec"]) for r in rows])
            mus.append([float(r["theta_E_pred_arcsec"]) for r in rows])
            sigs.append([float(r["theta_E_sigma_arcsec"]) for r in rows])
        M, Sg = np.array(mus), np.array(sigs)
        mm = M.mean(0)
        s = np.sqrt(np.maximum((Sg ** 2 + M ** 2).mean(0) - mm ** 2, 1e-12))
        return names, gt, mm + B, S * s

    names, t, pA, sA = load(MEMBERS_A, B_A, S_A)
    _, _, pB, sB = load(MEMBERS_B, B_B, S_B)
    print("G5b ZERO-SHOT on challenge-val N=%d (Rung 0 labeled)" % len(t))
    for tag, p, s in (("g4_cnv2_3", pA, sA), ("g4ar_r50_3", pB, sB),
                      ("ens2", 0.5 * (pA + pB), np.sqrt(0.5 * (sA**2 + sB**2) + 0.25 * (pA - pB)**2))):
        d = p - t
        frac = d / t
        rmse = float(np.sqrt((d ** 2).mean()))
        r2 = float(1 - (d ** 2).sum() / ((t - t.mean()) ** 2).sum())
        nmad = float(1.4826 * np.median(np.abs(d - np.median(d))))
        # THEIR grading (Ding+21): raw sigma and conformal (|z| q68 -> x1) on this split
        chi2_raw = float((((d) / s) ** 2).mean())
        sc = np.quantile(np.abs(d) / s, 0.68)
        s_conf = s * sc
        chi2_c = float(((d / s_conf) ** 2).mean())
        print("%-10s bias %+.3f RMSE %.3f NMAD %.3f R2 %+.2f fail %.0f%% | "
              "THEIRS: chi2 %.1f (conf %.2f, scale x%.2f) P %.3f->%.3f A %+.3f"
              % (tag, d.mean(), rmse, nmad, r2, 100 * (np.abs(frac) > 0.15).mean(),
                 chi2_raw, chi2_c, sc, (s / t).mean(), (s_conf / t).mean(), frac.mean()))
