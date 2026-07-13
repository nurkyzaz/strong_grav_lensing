#!/usr/bin/env python
"""AR1: add --arc_poisson to hybrid_combine.py — Poisson shot noise on the
NOISELESS arc render (native arm correctness fix; the Euclid arm already gets
Poisson(signal+sky) in euclidise). DEFAULT OFF until a pilot passes gates
(COMMITMENTS C13). Backup .bak_ar1; prints diff; aborts on missing patterns."""
import difflib
import os
import shutil

FN = os.path.expanduser("~/cosmos_acs/tiles/hybrid_combine.py")
BAK = FN + ".bak_ar1"
src = open(FN).read()

OLD_ARG = '    p.add_argument("--seed", type=int, default=4)'
NEW_ARG = '''    p.add_argument("--seed", type=int, default=4)
    p.add_argument("--arc_poisson", action="store_true",
                   help="AR1: Poisson shot noise on the noiseless arc render "
                        "(exposure --arc_exptime); default OFF until pilot-gated")
    p.add_argument("--arc_exptime", type=float, default=675.0,
                   help="calibrated e-/s exposure for --arc_poisson")'''

OLD_LOAD = '''    for i, fn in enumerate(files):
        sim = np.load(fn).astype("float32")
        target = float(rng.choice(real_rms))'''
NEW_LOAD = '''    for i, fn in enumerate(files):
        sim = np.load(fn).astype("float32")
        if args.arc_poisson:
            # AR1: arc-only shot noise (deflector stamp + backdrop carry their
            # own real noise; render here is the noiseless lensed source)
            counts = np.clip(sim, 0, None) * args.arc_exptime
            sim = (rng.poisson(counts).astype("float32") / args.arc_exptime
                   + np.minimum(sim, 0.0))
        target = float(rng.choice(real_rms))'''

for pat in (OLD_ARG, OLD_LOAD):
    if pat not in src:
        raise SystemExit("ABORT: pattern missing:\n" + pat[:120])
new = src.replace(OLD_ARG, NEW_ARG).replace(OLD_LOAD, NEW_LOAD)
shutil.copy2(FN, BAK)
open(FN, "w").write(new)
print("".join(difflib.unified_diff(src.splitlines(True), new.splitlines(True),
                                   "hybrid_combine.py (old)", "(new)")))
print("patched; backup", BAK)

# smoke: statistics of the transform on a synthetic arc
import numpy as np  # noqa: E402
rng = np.random.default_rng(1)
arc = np.zeros((64, 64), "float32")
arc[30:34, 20:44] = 0.05                      # ~34 e-/px over 675 s
counts = np.clip(arc, 0, None) * 675.0
noisy = rng.poisson(counts).astype("float32") / 675.0
on = arc > 0
print("smoke: mean flux ratio %.4f (expect ~1)  per-px scatter %.4f e-/s "
      "(expect ~%.4f = sqrt(f/t))"
      % (noisy[on].mean() / arc[on].mean(), noisy[on].std(),
         np.sqrt(0.05 / 675.0)))
