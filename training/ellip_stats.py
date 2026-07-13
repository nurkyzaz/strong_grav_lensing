#!/usr/bin/env python
"""Reprint the ellipticity-label summary from a saved label .h5 (no re-fitting)."""
import argparse, h5py, numpy as np
ap = argparse.ArgumentParser()
ap.add_argument("--ellip_file", required=True)
args = ap.parse_args()
d = {}
with h5py.File(args.ellip_file, "r") as f:
    for k in f.keys(): d[k] = f[k][:]
ok = d["ok_fit"] == 1.0
e_fit = np.hypot(d["e1_fit"], d["e2_fit"])
de = np.hypot(d["e1_fit"]-d["e1_mom"], d["e2_fit"]-d["e2_mom"])
off = np.hypot(d["cx"]-63.5, d["cy"]-63.5)
both = ok & (d["ok_mom"]==1.0)
def pct(a, ps=(16,50,84)): return ", ".join(f"P{p}={np.nanpercentile(a,p):.3f}" for p in ps)
print(f"\n=== ellipticity label stats ({args.ellip_file}) ===")
print(f" N={len(ok)} | fit ok {ok.mean()*100:.1f}% | moment ok {(d['ok_mom']==1).mean()*100:.1f}%")
print(f" |e_fit|:    {pct(e_fit[ok])}")
print(f" q_fit:      {pct(d['q_fit'][ok])}")
print(f" rms_fit:    {pct(d['rms_fit'][ok])}")
print(f" gamma_fit:  {pct(d['gamma_fit'][ok])}")
print(f" centre off (px from image centre): {pct(off[ok])}")
if both.sum() > 10:
    c1 = np.corrcoef(d['e1_fit'][both], d['e1_mom'][both])[0,1]
    c2 = np.corrcoef(d['e2_fit'][both], d['e2_mom'][both])[0,1]
    print(f" fit-vs-moment: corr(e1)={c1:.3f} corr(e2)={c2:.3f} | "
          f"median|de|={np.median(de[both]):.3f} | frac|de|>0.1 = {(de[both]>0.1).mean()*100:.1f}%")
print(f" theta_E_pix: {pct(d['theta_E_pix'][ok])}")
