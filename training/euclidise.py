#!/usr/bin/env python
"""R1.2: Euclidise HST ACS F814W cutouts following the published HST2EUCLID
recipe (Euclid Collab: Bergamini et al. 2025, A&A aa53984-25), reimplemented
because the original code is not public.

Recipe (their numbers):
  - flux conversion to Euclid VIS I_E at ZP_Euclid = 23.9 (AB);
  - PSF matched to Euclid VIS (FWHM ~0.16" -- Gaussian approximation here,
    DISCLOSED deviation: they build a photutils matching kernel from TinyTim;
    our ACS input PSF FWHM ~0.10");
  - resampled to 100 mas/px (here exact 2x2 sum from our 50 mas grid);
  - noise: Poisson(signal + sky), sky level set so an m_AB=24.5 extended
    source (1.3" diameter aperture) has S/N=10 at the EWS I_E exposure 2280 s.
Deviations (state in the paper): single-band F814W I_E proxy (they blend
F606W 0.542 + F814W 0.458); Gaussian PSF-matching kernel; input HST noise
(subdominant but nonzero) rides along -- symmetric between train and test.

Output images are bilinearly upsampled back to 128 px so the existing CNN
architecture and normalization apply unchanged (information content is Euclid).
"""
import argparse
import os
import numpy as np
import h5py
from scipy.ndimage import gaussian_filter, zoom
from scipy.signal import fftconvolve

ZP_HST = 25.94
ZP_EUC = 23.9
PIX_HST = 0.05
PIX_EUC = 0.10
FWHM_HST = 0.10
FWHM_EUC = 0.16
T_EXP = 2280.0
M_LIM, SN_LIM, APER_DIAM = 24.5, 10.0, 1.3


def euclid_sky_variance_per_px():
    """Per-Euclid-pixel sky variance [e-^2 over the full exposure] such that an
    m=24.5 extended source in a 1.3" diameter aperture reaches S/N=10.
    LF_EUC_SKY_SCALE (default 1.0): multiplicative variance scale — the GEN5
    Q1 arm sets ~2.2 because REAL Q1 release imaging measures noisier than
    the nominal EWS depth spec (stage0 sky-RMS ratio 0.673, 2026-07-22);
    gate-tuned, disclosed."""
    n_pix = np.pi * (APER_DIAM / 2.0) ** 2 / (PIX_EUC ** 2)
    counts = 10.0 ** (-0.4 * (M_LIM - ZP_EUC)) * T_EXP
    total_var = (counts / SN_LIM) ** 2
    scale = float(os.environ.get("LF_EUC_SKY_SCALE", "1.0"))
    return max((total_var - counts) / n_pix, 1.0) * scale


MATCH_KERNEL_FILE = os.path.expanduser(
    "~/cosmos_acs/tiles/acs2vis_matching_kernel.npy")
_MATCH_KERNEL = None


def _match_kernel():
    """G3: real ACS->VIS matching kernel (Q1 GRID-PSF-VIS target, photutils
    Tukey(0.3); see acs2vis_kernel_provenance.json). Missing file = hard
    error - never silently fall back to the Gaussian."""
    global _MATCH_KERNEL
    if _MATCH_KERNEL is None:
        _MATCH_KERNEL = np.load(MATCH_KERNEL_FILE)
    return _MATCH_KERNEL


def euclidise(img, rng, add_noise=True):
    f = img * 10.0 ** (0.4 * (ZP_EUC - ZP_HST))          # e-/s at Euclid ZP
    if os.environ.get("LF_EUCLIDISE_PSF", "real") == "gaussian":  # ablation
        sig_match = np.sqrt(FWHM_EUC ** 2 - FWHM_HST ** 2) / 2.355 / PIX_HST
        f = gaussian_filter(f, sig_match)                 # PSF match (legacy)
    else:
        f = fftconvolve(f, _match_kernel(), mode="same")  # PSF match (real)
    n2 = f.shape[0] // 2
    f = f.reshape(n2, 2, n2, 2).sum(axis=(1, 3))          # 2x2 sum -> 100 mas
    if add_noise:
        counts = np.clip(f, 0, None) * T_EXP
        sky_var = euclid_sky_variance_per_px()
        noiseless = f.copy()
        noisy = rng.poisson(counts + sky_var).astype("float64") - sky_var
        f = np.where(f >= 0, noisy / T_EXP, f + rng.normal(0, np.sqrt(sky_var)
                                                           / T_EXP, f.shape))
        # C38 (Nurkyz eyeball 2026-08-02): real Q1 noise is drizzle-CORRELATED
        # (neighbor-corr 0.758 vs our white 0.697 -> real looks smoother at the
        # same RMS). LF_EUC_NOISE_CORR = Gaussian sigma [Euclid px] to smooth
        # the NOISE REALIZATION only, renormalized to the same RMS. Default OFF
        # (unset/0) -> GEN4 output byte-identical.
        corr = float(os.environ.get("LF_EUC_NOISE_CORR", "0"))
        if corr > 0:
            delta = f - noiseless
            sm = gaussian_filter(delta, corr)
            s0, s1 = delta.std(), sm.std()
            if s1 > 0:
                f = noiseless + sm * (s0 / s1)
    return zoom(f, 2.0, order=1)                          # back to 128 px grid


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--inp", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--image_key", default=None,
                    help="default: 'images' if present else 'lensed'")
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--no_noise", action="store_true")
    a = ap.parse_args()

    rng = np.random.default_rng(a.seed)
    CH = 2000  # chunked: the 100k sets do not fit in RAM twice
    with h5py.File(a.inp, "r") as fi, h5py.File(a.out, "w") as fo:
        key = a.image_key or ("images" if "images" in fi else "lensed")
        n = fi[key].shape[0]
        side = fi[key].shape[-1]
        dset = fo.create_dataset(key, shape=(n, side, side), dtype="float32")
        for k in fi.keys():
            if k != key:
                v = fi[k][()] if fi[k].shape == () else fi[k][:]
                fo.create_dataset(k, data=v)
        for i in range(0, n, CH):
            block = fi[key][i:i + CH]
            if block.ndim == 4:
                block = block[:, 0]
            dset[i:i + CH] = np.stack([
                euclidise(im.astype("float64"), rng, add_noise=not a.no_noise)
                for im in block]).astype("float32")
            if (i // CH) % 10 == 0:
                print("  %d/%d" % (i, n), flush=True)
    print("wrote %s: %d images (key %s); sky sigma %.4f e-/s per Euclid px"
          % (a.out, n, key, np.sqrt(euclid_sky_variance_per_px()) / T_EXP))


if __name__ == "__main__":
    main()
