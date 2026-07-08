#!/usr/bin/env python
"""Build the Stage-2 PSF kernel bank: N detector-sampled kernels drawn from
the focus-diverse ePSF library (random exposure cube, chip, position,
rotation). Run on the Mac with .venv_epsf; scp the bank to the cluster and
extend each kernel there with fix_psf_kernel.py.

    .venv_epsf/bin/python build_psf_bank.py --pool benchmark --n 24 --seed 11

Writes psf_bank/kernel_XX.npy + psf_bank/manifest_bank.csv.
"""
import argparse
import glob
import os

import numpy as np
import pandas as pd
from astropy.io import fits
from scipy.ndimage import rotate
from acstools.focus_diverse_epsfs import interp_epsf

HERE = os.path.dirname(os.path.abspath(__file__))


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--pool", choices=["benchmark", "broad"], default="benchmark")
    p.add_argument("--n", type=int, default=24)
    p.add_argument("--seed", type=int, default=11)
    p.add_argument("--outdir", default=os.path.join(HERE, "psf_bank"))
    args = p.parse_args()

    rng = np.random.default_rng(args.seed)
    cubes = sorted(glob.glob(os.path.join(HERE, "epsf_library", args.pool, "*.fits")))
    if not cubes:
        raise SystemExit("no ePSF cubes found — run epsf_retrieve.py first")
    os.makedirs(args.outdir, exist_ok=True)

    rows = []
    i = 0
    attempts = 0
    while i < args.n and attempts < args.n * 10:
        attempts += 1
        cube_path = cubes[int(rng.integers(len(cubes)))]
        data = fits.getdata(cube_path)
        chip = "WFC1" if rng.random() < 0.5 else "WFC2"
        # stay off the extreme edges of the 4096x2048 chip;
        # interp_epsf requires INTEGER detector coordinates (floats -> None)
        x = int(rng.integers(300, 3800))
        y = int(rng.integers(200, 1850))
        try:
            k = interp_epsf(data, x, y, chip=chip, pixel_space=True)
        except Exception:
            k = None
        if k is None:
            print(f"  [redraw] {os.path.basename(cube_path)} {chip} "
                  f"({x:.0f},{y:.0f}) returned no ePSF")
            continue
        k = k.astype("float64")
        angle = float(rng.uniform(0, 360))
        k = rotate(k, angle, reshape=False, order=1, mode="constant", cval=0.0)
        k /= k.sum()
        name = f"kernel_{i:02d}.npy"
        np.save(os.path.join(args.outdir, name), k.astype("float32"))
        rows.append(dict(kernel=name, cube=os.path.basename(cube_path),
                         chip=chip, x=round(x, 1), y=round(y, 1),
                         rot_deg=round(angle, 1), shape=k.shape[0]))
        print(f"{name}: {os.path.basename(cube_path)} {chip} "
              f"({x:.0f},{y:.0f}) rot={angle:.0f}deg shape={k.shape}")
        i += 1
    pd.DataFrame(rows).to_csv(os.path.join(args.outdir, "manifest_bank.csv"),
                              index=False)
    print(f"\nwrote {args.n} kernels + manifest to {args.outdir}")


if __name__ == "__main__":
    main()
