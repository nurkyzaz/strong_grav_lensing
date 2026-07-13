#!/usr/bin/env python
"""Append the theta_E REBALANCE override to config_lensfusion_acs_pathb_euclid.py
(backup .bak_prereb; idempotent; prints the diff block). One image-affecting
change (plan section 2b) — everything else in the recipe is untouched."""
import os
import shutil

CFG = os.path.expanduser("~/cosmos_acs/tiles/config_lensfusion_acs_pathb_euclid.py")
MARK = "_theta_e_rebalanced"

BLOCK = '''

# --- theta_E REBALANCE (2026-07-10, plan section 2b; added after eval #15) ---
# The visibility selection passes 26/53/64/84% by theta_E bin (D2 threshold
# scan), so a flat PRE-selection prior gives a large-theta_E-skewed TRAINING
# set (median 1.609") -> prior-pull returns at small theta_E (L0: SLACS <0.9"
# fail 62% / +33% bias; sim-val probe: +7-8% bias in-distribution; eval #15:
# bias is common-mode across all ensemble members). Fix: piecewise-constant
# pre-selection density oc 1/pass(theta_E) so the POST-selection training
# distribution is ~flat. Expected overall pass ~51% (vs 59% flat-prior).
_REB_BINS = [(0.45, 0.80, 0.26), (0.80, 1.20, 0.53),
             (1.20, 1.70, 0.64), (1.70, 2.30, 0.84)]
_REB_W = np.array([(hi - lo) / p for lo, hi, p in _REB_BINS])
_REB_W = _REB_W / _REB_W.sum()


def _theta_e_rebalanced():
    i = np.random.choice(len(_REB_BINS), p=_REB_W)
    lo, hi, _p = _REB_BINS[i]
    return float(np.random.uniform(lo, hi))


config_dict['main_deflector']['parameters']['theta_E'] = _theta_e_rebalanced
'''

src = open(CFG).read()
if MARK in src:
    print("already patched — nothing to do")
else:
    shutil.copy(CFG, CFG + ".bak_prereb")
    with open(CFG, "a") as f:
        f.write(BLOCK)
    print("patched %s (backup .bak_prereb). Appended block:" % CFG)
    print(BLOCK)
