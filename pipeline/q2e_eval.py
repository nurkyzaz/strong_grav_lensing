#!/usr/bin/env python
"""Q2d audit + ⛔ Q2e OFFICIAL EVAL (eval #24) — Nurkyz rulings 2026-07-13:
normalization FROZEN at x11.4, no pedestal (C17-gate-aligned); runs
disconnected as one sbatch chain. This script is the ONE-SHOT official eval
on the full Q1 SLDE set vs PyAutoLens SIE theta_E (their GT, their referee —
caveat carried). Pre-registered rows: primary = G4 cnv2_3 ens; derived
same-passes = g4ar r50_3, ens2 = mean of both sides. Sample rows: full,
excl-tuning-9 (burned in the Q2c2 sweep), in-support (GT in [0.45,2.3]"),
in-support-excl-tuning. Bar: LEMON Fig 12a bias 0.01 RMSE 0.17 NMAD 0.07
R2 0.71 (their 354 vs our 335-with-GT: remainder presumably Rojas systems —
disclosed). Phases: --build (audit + frozen h5 + previews), --predict,
--report."""
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
EC = os.path.expanduser("~/einstein_cnn")
PY = os.path.expanduser("~/miniconda3/envs/Stronglensing/bin/python")
H5 = os.path.join(BASE, "q1_slde_eval_f11p4.h5")   # FROZEN AT CREATION (C18)

FACTOR = 11.4                                       # frozen ruling 2026-07-13
SUPPORT = (0.45, 2.30)                              # training theta_E support
MEMBERS_A = ["g4_cnv2_s1", "g4_cnv2_s2", "g4_cnv2_s3"]     # primary
MEMBERS_B = ["g4ar_r50_s1", "g4ar_r50_s2", "g4ar_r50_s3"]  # faint-arc pick
B_A = -0.0015423929634094113                        # g4_recal.json (frozen)
B_B = -0.0032367853597006224                        # g4ar_recal.json (frozen)
S_A, S_B = 0.9618278137772992, 1.0152982705791773
LEMON = dict(bias=0.01, rmse=0.17, nmad=0.07, r2=0.71)
TUNING = {  # 9 burned lenses (Q2c2 sweep 2026-07-13)
    "102018665_NEG570040238507752998", "102018665_NEG576731213511114485",
    "102018666_NEG579859279508531437", "102018667_NEG587746535508057234",
    "102018668_NEG595646727509469177", "102019123_NEG564667438505382529",
    "102019123_NEG567245233502945885", "102019126_NEG589666030505609975",
    "102019127_NEG596525941504553950"}
RNG = np.random.default_rng(20260714)

ap = argparse.ArgumentParser()
ap.add_argument("--build", action="store_true")
ap.add_argument("--predict", action="store_true")
ap.add_argument("--report", action="store_true")
ap.add_argument("--conv", choices=["repeat", "zoom"], default="repeat",
                help="upsample convention: 'repeat' = eval #24 as run; "
                     "'zoom' = euclidise.py output convention (bilinear, "
                     "per-0.1px values) — the post-#24 forensics found "
                     "#24's repeat/4 texture does NOT match training. "
                     "Factor is translated x11.4/4=2.85 so the absolute "
                     "calibration is IDENTICAL to the frozen ruling.")
a = ap.parse_args()
if a.conv == "zoom":
    H5 = os.path.join(BASE, "q1_slde_eval_f2p85_zoom.h5")
EVAL_TAG = "l24" if a.conv == "repeat" else "l25"


def gt_table():
    fn = glob.glob(os.path.join(BASE, "modeling_lens_mass*.csv"))[0]
    gt, skipped = {}, 0
    for r in csv.DictReader(open(fn)):
        try:
            gt[r["id_str"]] = float(r["einstein_radius_median_pdf"])
        except (ValueError, KeyError):
            skipped += 1
    print("GT table: %d usable, %d skipped (empty theta_E)" % (len(gt), skipped))
    return gt


def preprocess(d):
    name = os.path.basename(d)
    vis = fits.open(os.path.join(d, name + ".fits"))["VIS_FLUX"].data.astype(float)
    c = vis.shape[0] // 2
    crop = vis[c - 32:c + 32, c - 32:c + 32]
    if a.conv == "zoom":  # euclidise.py output convention (bilinear, no /4)
        from scipy.ndimage import zoom as _zoom
        return _zoom(crop, 2.0, order=1) * (FACTOR / 4.0)
    return np.repeat(np.repeat(crop, 2, 0), 2, 1) / 4.0 * FACTOR


if a.build:
    gt = gt_table()
    dirs, names, gts, missing = [], [], [], 0
    for d in sorted(glob.glob(LENS + "/*")):
        n = os.path.basename(d)
        if n not in gt:
            missing += 1
            continue
        if not os.path.exists(os.path.join(d, n + ".fits")):
            print("NO FITS: %s" % n)
            continue
        dirs.append(d)
        names.append(n)
        gts.append(gt[n])
    gts = np.array(gts)
    ins = (gts >= SUPPORT[0]) & (gts <= SUPPORT[1])
    tun = np.array([n in TUNING for n in names])
    print("Q2d AUDIT: N=%d with GT (%d dirs lack GT — LEMON had 354; disclose)"
          % (len(names), missing))
    print("  GT theta_E: q10/50/90 = %.2f / %.2f / %.2f arcsec"
          % tuple(np.percentile(gts, [10, 50, 90])))
    print("  in-support [%.2f,%.2f]: %d (%.0f%%)  below: %d  above: %d"
          % (SUPPORT[0], SUPPORT[1], ins.sum(), 100 * ins.mean(),
             (gts < SUPPORT[0]).sum(), (gts > SUPPORT[1]).sum()))
    print("  tuning-burned present: %d of 9" % tun.sum())
    ims = np.stack([preprocess(d) for d in dirs]).astype(np.float32)

    # C17 stats on the FULL frozen set
    k = 12
    rms_l, ps_l = [], []
    for im in ims:
        corner = np.concatenate([im[:k, :k].ravel(), im[:k, -k:].ravel(),
                                 im[-k:, :k].ravel(), im[-k:, -k:].ravel()])
        sky = np.median(corner)
        rms = 1.4826 * np.median(np.abs(corner - sky))
        rms_l.append(rms)
        ps_l.append((np.percentile(im, 99.99) - sky) / max(rms, 1e-12))
    print("  C17 full-set: skyRMS med %.4g (bench 0.008)  peak/sky med %.0f (bench 480)"
          % (np.median(rms_l), np.median(ps_l)))

    with h5py.File(H5, "w") as h:
        h.create_dataset("images", data=ims)
        h.create_dataset("theta_E_pub", data=gts.astype(np.float32))
        sd = h5py.special_dtype(vlen=str)
        h.create_dataset("names", data=np.array(names, object), dtype=sd)
        h.create_dataset("survey", data=np.array(["Q1SLDE"] * len(names), object), dtype=sd)
        h.create_dataset("box_arcsec", data=np.float32(6.4))
        h.create_dataset("pixscale", data=np.float32(0.05))
    print("FROZEN eval file written (C18): %s  N=%d" % (H5, len(names)))
    with open(os.path.join(BASE, "q2d_audit.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["name", "theta_E_gt", "in_support", "tuning_burned"])
        for n, g, i, t in zip(names, gts, ins, tun):
            w.writerow([n, "%.4f" % g, int(i), int(t)])

    # previews: ALL out-of-support + 20-lens in-support sample (standing rule)
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    sel_out = [i for i in range(len(names)) if not ins[i]]
    sel_in = list(RNG.choice(np.where(ins)[0], min(20, int(ins.sum())), replace=False))
    for tag, sel in (("outsupport", sel_out), ("insample", sel_in)):
        sel = sel[:40]
        if not sel:
            continue
        fig, axes = plt.subplots(3, len(sel), figsize=(2.2 * len(sel), 7), squeeze=False)
        for j, i in enumerate(sel):
            im = ims[i]
            rms = max(np.std(im[:12, :12]), 1e-9)
            for r, dat in enumerate((im, np.clip(im, np.percentile(im, 1),
                                                 np.percentile(im, 99)),
                                     np.arcsinh(im / rms))):
                axes[r][j].imshow(dat, origin="lower", cmap="gray")
                axes[r][j].axis("off")
            axes[0][j].set_title("%s\n%.2f" % (names[i][:9], gts[i]), fontsize=5)
        plt.tight_layout()
        fn = os.path.join(BASE, "q2e_preview_%s.png" % tag)
        plt.savefig(fn, dpi=100)
        plt.close()
        print("preview written: %s (%d systems)" % (fn, len(sel)))

SUFF = "q1_slde_f11p4" if a.conv == "repeat" else "q1_slde_f2p85_zoom"

if a.predict:
    for m in MEMBERS_A + MEMBERS_B:
        subprocess.check_call(
            [PY, os.path.join(EC, "predict_real_lenses_paltas.py"),
             "--ckpt", os.path.join(EC, m + ".pt"), "--real", H5,
             "--tta", "--outdir", os.path.join(EC, "brian_run"),
             "--out", "preds_%s_%s_%s.csv" % (EVAL_TAG, m, SUFF)], cwd=EC)

if a.report:
    aud = {r["name"]: r for r in csv.DictReader(open(os.path.join(BASE, "q2d_audit.csv")))}

    def load(members, B, S):
        mus, sigs, names, gt_v = [], [], None, None
        for m in members:
            fn = os.path.join(EC, "brian_run", "preds_%s_%s_%s.csv" % (EVAL_TAG, m, SUFF))
            rows = list(csv.DictReader(open(fn)))
            if names is None:
                names = [r["name"] for r in rows]
                gt_v = np.array([float(r["theta_E_pub_arcsec"]) for r in rows])
            mus.append([float(r["theta_E_pred_arcsec"]) for r in rows])
            sigs.append([float(r["theta_E_sigma_arcsec"]) for r in rows])
        M, Sg = np.array(mus), np.array(sigs)
        mm = M.mean(0)
        s_ens = np.sqrt(np.maximum((Sg ** 2 + M ** 2).mean(0) - mm ** 2, 1e-12))
        return names, gt_v, mm + B, S * s_ens

    names, t, pA, sA = load(MEMBERS_A, B_A, S_A)
    _, _, pB, sB = load(MEMBERS_B, B_B, S_B)
    M2 = np.stack([pA, pB])
    p2 = M2.mean(0)
    s2 = np.sqrt(np.maximum((np.stack([sA, sB]) ** 2 + M2 ** 2).mean(0) - p2 ** 2, 1e-12))
    ins = np.array([aud[n]["in_support"] == "1" for n in names])
    tun = np.array([aud[n]["tuning_burned"] == "1" for n in names])

    def met(pp, tt):
        dd = pp - tt
        return dict(bias=dd.mean(), rmse=float(np.sqrt((dd ** 2).mean())),
                    nmad=float(1.4826 * np.median(np.abs(dd - np.median(dd)))),
                    r2=float(1 - (dd ** 2).sum() / ((tt - tt.mean()) ** 2).sum()),
                    fail=float((np.abs(dd / tt) > 0.15).mean()))

    print("\n⛔ EVAL %s — Q2e (%s convention), frozen calib x%.1f, N=%d"
          % (EVAL_TAG, a.conv, FACTOR, len(names)))
    print("LEMON Fig12a ref: bias +0.01  RMSE 0.17  NMAD 0.07  R2 +0.71")
    ROWS = [("cnv2_3 (primary)", pA, sA), ("r50_3 (derived)", pB, sB),
            ("ens2 (derived)", p2, s2)]
    MASKS = [("full", np.ones(len(names), bool)),
             ("excl-tuning", ~tun),
             ("in-support", ins),
             ("in-supp excl-tun", ins & ~tun)]
    for rname, pp, ss in ROWS:
        print("== %s ==" % rname)
        for mname, mk in MASKS:
            m = met(pp[mk], t[mk])
            print("  %-17s N=%3d  bias %+.3f  RMSE %.3f  NMAD %.3f  R2 %+.2f  fail %.0f%%"
                  % (mname, mk.sum(), m["bias"], m["rmse"], m["nmad"],
                     m["r2"], 100 * m["fail"]))
        # bootstrap on the full row
        n = len(names)
        boot = {k: np.empty(4000) for k in ("rmse", "nmad", "r2", "bias")}
        for bi in range(4000):
            idx = RNG.integers(0, n, n)
            mb = met(pp[idx], t[idx])
            for k in boot:
                boot[k][bi] = mb[k]
        print("  boot(full): P(RMSE<0.17)=%.2f  P(NMAD<0.07)=%.2f  P(R2>0.71)=%.2f  P(|bias|<0.03)=%.2f"
              % ((boot["rmse"] < LEMON["rmse"]).mean(), (boot["nmad"] < LEMON["nmad"]).mean(),
                 (boot["r2"] > LEMON["r2"]).mean(), (np.abs(boot["bias"]) < 0.03).mean()))
        d_, frac = pp - t, (pp - t) / t
        z = np.abs(d_) / ss
        rel = ss / pp
        conf = rel <= np.median(rel)
        print("  med frac %+.1f%% | conf-half fail %.0f%% | cov RECAL %.0f/%.0f%%"
              % (100 * np.median(frac), 100 * (np.abs(frac[conf]) > 0.15).mean(),
                 100 * (z <= 1).mean(), 100 * (z <= 1.96).mean()))
        for lo, hi in [(0.0, 0.45), (0.45, 0.9), (0.9, 1.2), (1.2, 1.5), (1.5, 3.0)]:
            mk = (t >= lo) & (t < hi)
            if mk.sum():
                print("    [%.2f,%.2f): N=%3d  %3.0f%%  %+5.1f%%"
                      % (lo, hi, mk.sum(), 100 * (np.abs(frac[mk]) > 0.15).mean(),
                         100 * np.median(frac[mk])))
    out_fn = os.path.join(EC, "brian_run", "preds_%s_ens_%s.csv" % (EVAL_TAG, SUFF))
    with open(out_fn, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["name", "theta_E_gt", "pred_cnv2_3", "sig_cnv2_3",
                    "pred_r50_3", "sig_r50_3", "pred_ens2", "sig_ens2",
                    "in_support", "tuning_burned"])
        for i, n in enumerate(names):
            w.writerow([n, "%.4f" % t[i], "%.4f" % pA[i], "%.4f" % sA[i],
                        "%.4f" % pB[i], "%.4f" % sB[i], "%.4f" % p2[i],
                        "%.4f" % s2[i], int(ins[i]), int(tun[i])])
    print("wrote %s" % out_fn)
