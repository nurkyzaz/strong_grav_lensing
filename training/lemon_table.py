#!/usr/bin/env python
"""R1.2: LEMON-convention metrics table (their Table 3: bias, RMSE, NMAD, R^2)
for our Euclidised-benchmark predictions, alongside our standard metrics.
LEMON reference (Busillo et al. 2026, Table 3, 60 Euclidised HST lenses,
no filtering): bias -0.03", RMSE 0.14", NMAD 0.11", R2 = 0.53."""
import os
import sys
import pandas as pd
import numpy as np

EXCLUDE = {"J0955+0101"}

print("LEMON ref (their 60 mixed-GT lenses): bias -0.03  RMSE 0.14  NMAD 0.11  R2 0.53")
for fn in sys.argv[1:]:
    d = pd.read_csv(os.path.expanduser(fn))
    if "name" in d.columns:
        d = d[~d["name"].isin(EXCLUDE)]
    pcol = [c for c in d.columns if "pred" in c][0]
    tcol = [c for c in d.columns if "pub" in c or "true" in c][0]
    delta = d[pcol] - d[tcol]
    frac = delta / d[tcol]
    ss_res = (delta ** 2).sum()
    ss_tot = ((d[tcol] - d[tcol].mean()) ** 2).sum()
    r2 = 1.0 - ss_res / ss_tot
    nmad = 1.4826 * (delta - delta.median()).abs().median()
    print("%-42s N=%3d bias %+.3f  RMSE %.3f  NMAD %.3f  R2 %+.2f | "
          "median frac %+.1f%%  fail>15%%: %.0f%%"
          % (os.path.basename(fn), len(d), delta.mean(),
             np.sqrt((delta ** 2).mean()), nmad, r2,
             100 * frac.median(), 100 * (frac.abs() > 0.15).mean()))
