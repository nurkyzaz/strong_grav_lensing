# Ablation A3 (MASTER_PLAN D1, the causal spine): identical to the v2 config
# in EVERY respect except the theta_E prior, which reverts to an m3-like
# NARROW/SKEWED distribution — truncnorm centred 1.00″, sigma 0.35″, truncated
# to the same [0.45, 2.30] support (so coverage is identical and only the
# SHAPE differs; ~52% of mass in [0.7, 1.3]″, mimicking the halo-determined
# m3-era prior whose collapse attractor was ~0.95–1.0″).
import copy
import os
import sys

from scipy.stats import truncnorm as _tn

sys.path.insert(0, os.path.expanduser('~/cosmos_acs/tiles'))
from config_lensfusion_acs import *   # noqa: F401,F403

config_dict = copy.deepcopy(config_dict)  # noqa: F405
_loc, _scale, _lo, _hi = 1.00, 0.35, 0.45, 2.30
config_dict['main_deflector']['parameters']['theta_E'] = _tn(
    (_lo - _loc) / _scale, (_hi - _loc) / _scale, loc=_loc, scale=_scale).rvs

no_noise = True
