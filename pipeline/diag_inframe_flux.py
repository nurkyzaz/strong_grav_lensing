"""Diagnose pilot-v4 over-bright deflectors: compare IN-FRAME flux, sim vs real.

Hypothesis: total-flux scaling stuffs 100% of the galaxy's TOTAL-mag flux into
the 6.4" frame, while real cutouts only contain the in-frame fraction of it
(rest of the de Vaucouleurs wings lie beyond the frame). Prediction: sim
in-frame flux ~1.4-1.7x real at matched magnitude.
Run: python diag_inframe_flux.py
"""
import numpy as np, h5py
from scipy.special import gammainc

def robust_sky(img, frac=0.25):
    n = img.shape[0]; m = int(n * frac)
    corners = np.concatenate([img[:m, :m].ravel(), img[:m, -m:].ravel(),
                              img[-m:, :m].ravel(), img[-m:, -m:].ravel()])
    med = np.median(corners)
    mad = np.median(np.abs(corners - med)) * 1.4826
    return med, mad

def inframe_flux(imgs):
    out = []
    for im in imgs:
        med, _ = robust_sky(im)
        out.append(float(np.clip(im - med, 0, None).sum()))
    return np.array(out)

with h5py.File("/home/user/nurkyz/einstein_cnn/pathb_pilot_v4.h5", "r") as f:
    sim = f["lensed"][:]
    dmag = f["deflector_mag"][:] if "deflector_mag" in f else None
with h5py.File("/home/user/nurkyz/einstein_cnn/real_slacs_images.h5", "r") as f:
    key = "images" if "images" in f else list(f.keys())[0]
    real = f[key][:]
    names = [n.decode() if isinstance(n, bytes) else str(n)
             for n in f["names"][:]] if "names" in f else None

fs = inframe_flux(sim)
fr = inframe_flux(real)
print("IN-FRAME flux (e-/s, sky-subtracted, positive part):")
print("  sim  median %.3f  16-84%% [%.3f, %.3f]" % (np.median(fs), *np.percentile(fs, [16, 84])))
print("  real median %.3f  16-84%% [%.3f, %.3f]" % (np.median(fr), *np.percentile(fr, [16, 84])))
print("  ratio of medians sim/real: %.2f" % (np.median(fs) / np.median(fr)))

# implied in-frame magnitude vs the drawn magnitude
ZP = 25.94
if dmag is not None:
    ok = dmag > 0
    mag_inframe_sim = ZP - 2.5 * np.log10(np.clip(fs[ok], 1e-9, None))
    print("sim: drawn TOTAL mag median %.2f; implied IN-FRAME mag median %.2f"
          % (np.median(dmag[ok]), np.median(mag_inframe_sim)))
mag_inframe_real = ZP - 2.5 * np.log10(np.clip(fr, 1e-9, None))
print("real: implied IN-FRAME mag median %.2f  16-84%% [%.2f, %.2f]"
      % (np.median(mag_inframe_real), *np.percentile(mag_inframe_real, [16, 84])))

# analytic check: de Vaucouleurs fraction inside r (circular) for Re
b = 7.669
def devauc_frac(r, re):
    return gammainc(8.0, b * (r / re) ** 0.25)
for re in (1.4, 2.0, 2.9):
    print("de Vauc Re=%.1f\": frac within r=2.0\"=%.2f, within r=3.2\" (frame half-width)=%.2f"
          % (re, devauc_frac(2.0, re), devauc_frac(3.2, re)))
