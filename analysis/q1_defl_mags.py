import csv, glob, os
import numpy as np

D = "/home/user/nurkyz/cosmos_acs/q1_slde"
for fn in ["modeling_mge_magnitude.csv", "modeling_sersic_magnitude.csv",
           "modeling_lens_sersic.csv", "modeling_lens_mge.csv"]:
    p = os.path.join(D, fn)
    if not os.path.exists(p):
        continue
    rows = list(csv.DictReader(open(p)))
    if not rows:
        continue
    cols = list(rows[0].keys())
    print("\n=== %s  (nrows %d) ===" % (fn, len(rows)))
    print("cols:", cols[:12])
    for c in cols:
        try:
            v = np.array([float(r[c]) for r in rows if r[c] not in ("", "nan", "NaN")])
        except (ValueError, KeyError):
            continue
        if len(v) > 20 and 12 < np.nanmedian(v) < 28:
            print("   %-28s med=%.2f  [10-90: %.1f-%.1f]"
                  % (c, np.nanmedian(v), np.nanpercentile(v, 10), np.nanpercentile(v, 90)))
