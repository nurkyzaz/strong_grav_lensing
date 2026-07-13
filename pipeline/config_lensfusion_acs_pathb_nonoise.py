# config_lensfusion_acs_pathb_nonoise.py -- PATH B variant (2026-07-08).
# Renders the lensed source ONLY (no parametric lens light): the deflector is
# a mass-only lens, so paltas produces the arc/ring + a valid theta_E label,
# and hybrid_combine.py pastes a REAL elliptical-galaxy cutout as the deflector
# light (real HST morphology/PSF). Detector noise OFF (added by hybrid_combine).
import copy
import os
import sys

sys.path.insert(0, os.path.expanduser('~/cosmos_acs/tiles'))
from config_lensfusion_acs import *   # noqa: F401,F403

config_dict = copy.deepcopy(config_dict)  # noqa: F405
config_dict.pop('lens_light', None)       # no parametric lens light
config_dict.pop('cross_object', None)     # its joint (mag,Re) prior targeted lens_light

no_noise = True
