#!/usr/bin/env python
"""G3-4: patch euclidise.py — replace the Gaussian PSF-matching step with the
real ACS->VIS matching kernel (Q1 GRID-PSF-VIS target, photutils method).

- Backup to euclidise.py.bak_g3; prints a unified diff; aborts if the expected
  pattern is missing (the ApparentSersic patch-script pattern).
- The Gaussian path stays available via env LF_EUCLIDISE_PSF=gaussian
  (ablation); default is the real kernel, and a MISSING kernel file is a hard
  error, never a silent fallback.
"""
import difflib
import os
import shutil

FN = os.path.expanduser("~/einstein_cnn/euclidise.py")
BAK = FN + ".bak_g3"

src = open(FN).read()

OLD_IMPORT = "from scipy.ndimage import gaussian_filter, zoom"
NEW_IMPORT = ("from scipy.ndimage import gaussian_filter, zoom\n"
              "from scipy.signal import fftconvolve")

OLD_BLOCK = """def euclidise(img, rng, add_noise=True):
    f = img * 10.0 ** (0.4 * (ZP_EUC - ZP_HST))          # e-/s at Euclid ZP
    sig_match = np.sqrt(FWHM_EUC ** 2 - FWHM_HST ** 2) / 2.355 / PIX_HST
    f = gaussian_filter(f, sig_match)                     # PSF match"""

NEW_BLOCK = """MATCH_KERNEL_FILE = os.path.expanduser(
    "~/cosmos_acs/tiles/acs2vis_matching_kernel.npy")
_MATCH_KERNEL = None


def _match_kernel():
    \"\"\"G3: real ACS->VIS matching kernel (Q1 GRID-PSF-VIS target, photutils
    Tukey(0.3); see acs2vis_kernel_provenance.json). Missing file = hard
    error - never silently fall back to the Gaussian.\"\"\"
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
        f = fftconvolve(f, _match_kernel(), mode="same")  # PSF match (real)"""

OLD_MAIN_IMPORT = "import argparse\nimport numpy as np"
NEW_MAIN_IMPORT = "import argparse\nimport os\nimport numpy as np"

for pat in (OLD_IMPORT, OLD_BLOCK, OLD_MAIN_IMPORT):
    if pat not in src:
        raise SystemExit("ABORT: expected pattern not found:\n" + pat[:120])

new = (src.replace(OLD_MAIN_IMPORT, NEW_MAIN_IMPORT)
          .replace(OLD_IMPORT, NEW_IMPORT)
          .replace(OLD_BLOCK, NEW_BLOCK))

shutil.copy2(FN, BAK)
open(FN, "w").write(new)
print("".join(difflib.unified_diff(src.splitlines(True), new.splitlines(True),
                                   "euclidise.py (old)", "euclidise.py (new)")))
print("patched; backup at", BAK)

# smoke: import and run one image through both paths
import numpy as np  # noqa: E402
import sys  # noqa: E402
sys.path.insert(0, os.path.expanduser("~/einstein_cnn"))
import importlib  # noqa: E402
import euclidise as E  # noqa: E402
importlib.reload(E)
rng = np.random.default_rng(1)
img = np.zeros((128, 128)); img[64, 64] = 100.0
os.environ["LF_EUCLIDISE_PSF"] = "real"
a = E.euclidise(img.copy(), rng, add_noise=False)
os.environ["LF_EUCLIDISE_PSF"] = "gaussian"
b = E.euclidise(img.copy(), rng, add_noise=False)
del os.environ["LF_EUCLIDISE_PSF"]
print("point-source flux: real %.4f gaussian %.4f (ratio %.4f)"
      % (a.sum(), b.sum(), a.sum() / b.sum()))
pk = lambda m: m.max() / m.sum()
print("peak fraction: real %.4f gaussian %.4f (real should be LOWER-peaked "
      "core+wings)" % (pk(a), pk(b)))
