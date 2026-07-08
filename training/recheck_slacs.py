#!/usr/bin/env python
"""
recheck_slacs.py  -  finish the HSTempty -> SLACS diagnostic.

Run from ~/einstein_cnn/ AFTER test_hstempty_slacs.py has written the CSVs
(see the patch in the meeting notes). Expects, in the current directory and
in the SAME row order the test script iterates the h5 (row order is fixed):

  real_slacs_residual_v2_preds.csv   columns: theta_true,theta_pred   (required)
  real_slacs_images_preds.csv        columns: theta_true,theta_pred   (optional, raw)
  real_slacs_residual_v2.h5          key 'images' [51,1,128,128]       (required)

Writes recheck_summary.txt and prints the same to stdout.
"""
import io
import numpy as np
import h5py


def load(path):
    a = np.genfromtxt(path, delimiter=",", names=True)
    return np.asarray(a["theta_true"], float), np.asarray(a["theta_pred"], float)


def block(tag, t, p, out):
    err = 100.0 * (p - t) / t
    r = np.corrcoef(t, p)[0, 1]
    slope = np.polyfit(t, p, 1)[0]                       # OLS pred ~ true
    cod = 1 - np.sum((p - t) ** 2) / np.sum((t - t.mean()) ** 2)
    db = p - np.median(p - t)                            # remove constant median offset
    cod_db = 1 - np.sum((db - t) ** 2) / np.sum((t - t.mean()) ** 2)
    ratio = p.std() / t.std()
    verdict = ("COLLAPSE toward a constant (true regression-to-mean)"
               if ratio < 0.4 else
               "DECORRELATED - predictions vary but read the WRONG features")
    print(f"\n[{tag}] N={len(t)}", file=out)
    print(f"  true: mean={t.mean():.3f}  std={t.std():.3f}", file=out)
    print(f"  pred: mean={p.mean():.3f}  std={p.std():.3f}  "
          f"sigma_pred/sigma_true={ratio:.2f}", file=out)
    print(f"  median frac={np.median(err):+.1f}%   r={r:.2f}   "
          f"slope(pred~true)={slope:.2f}", file=out)
    print(f"  R2(CoD)={cod:.2f}   R2_debiased={cod_db:.2f}", file=out)
    print(f"  -> {verdict}", file=out)
    return err


def main():
    out = io.StringIO()

    t_r, p_r = load("real_slacs_residual_v2_preds.csv")
    err_r = block("v2-subtracted", t_r, p_r, out)

    try:
        t_w, p_w = load("real_slacs_images_preds.csv")
        block("raw (unsubtracted)", t_w, p_w, out)
        dmae = np.abs(p_w - t_w).mean() - np.abs(p_r - t_r).mean()
        print(f"\n[raw vs subtracted] dMAE = {dmae:+.3f}\"  "
              f"(large magnitude => central region / subtraction state dominates "
              f"the prediction)", file=out)
    except OSError:
        print("\n(real_slacs_images_preds.csv not found - skipping raw comparison)",
              file=out)

    # crater metric on the subtracted residual; h5 row order == CSV row order
    with h5py.File("real_slacs_residual_v2.h5", "r") as h:
        imgs = np.asarray(h["images"]).reshape(-1, 128, 128)
    yy, xx = np.mgrid[0:128, 0:128]
    rpix = np.hypot(xx - 63.5, yy - 63.5)
    core = rpix < 10.0                                   # ~0.5" at 0.05"/px
    central_frac = np.array(
        [np.abs(im[core]).sum() / (np.abs(im).sum() + 1e-9) for im in imgs]
    )

    c_signed = np.corrcoef(central_frac, err_r)[0, 1]
    c_abs = np.corrcoef(central_frac, np.abs(err_r))[0, 1]
    print("\n[crater test, v2-subtracted]", file=out)
    print(f"  corr(central_frac, signed err) = {c_signed:+.2f}", file=out)
    print(f"  corr(central_frac, |err|)      = {c_abs:+.2f}", file=out)
    print("  strong +ve => over-subtraction craters really inflate theta_E "
          "(the +18% is real crater bias -> clean subtraction should fix it)", file=out)
    print("  near 0      => crater story is NOT the driver; the over-prediction "
          "is unexplained -> do not commit to Path A on the crater premise", file=out)

    order = np.argsort(-np.abs(err_r))[:10]
    print("\n  worst-10 (subtracted):   idx   true   pred    err%    central_frac",
          file=out)
    for i in order:
        print(f"   {i:>3}   {t_r[i]:.2f}   {p_r[i]:.2f}   "
              f"{err_r[i]:+6.1f}    {central_frac[i]:.3f}", file=out)

    txt = out.getvalue()
    print(txt)
    with open("recheck_summary.txt", "w") as f:
        f.write(txt)


if __name__ == "__main__":
    main()
