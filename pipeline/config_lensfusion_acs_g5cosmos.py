# config_lensfusion_acs_g5cosmos.py — GEN5 with COSMOS sources selected by a
# EUCLID-tuned surface-brightness cut (Nurkyz idea): the SB cut
#   mag_auto + 2.5 log10(2 pi (flux_radius*pix)^2) <= LF_SB_CUT
# was set to 21 to match SLACS; retune for Euclid Q1 (real Q1 source mag ~22.7).
# Uses HighSBCOSMOSCatalog directly (clean real COSMOS images, no PyAutoLens mesh
# artifacts, thousands available, no eval-set provenance) and does NOT apply the
# Gen5HighZSource DL/K over-dimming that made earlier COSMOS arcs invisible —
# source brightness is set by source_apparent_magnitude (~real Q1 source mag),
# the manifest's high-z z_source shrinks the source angular size via the base
# GalaxyCatalog z-scaling. Knobs (env): LF_SB_CUT (compactness/arc thickness),
# LF_SRC_MAG_MED (arc brightness).
import os

from scipy.stats import truncnorm as _tn

from config_lensfusion_acs_g5 import *   # noqa: F401,F403  (GEN5 machinery)
from config_lensfusion_acs_pathb_euclid import HighSBCOSMOSCatalog

config_dict['source']['class'] = HighSBCOSMOSCatalog          # noqa: F405
config_dict['source']['parameters']['max_source_surface_brightness'] = float(
    os.environ.get('LF_SB_CUT', '21.5'))
_med = float(os.environ.get('LF_SRC_MAG_MED', '22.7'))        # real Q1 source ~22.7
config_dict['source']['parameters']['source_apparent_magnitude'] = _tn(  # noqa: F405
    (_med - 1.5 - _med) / 0.8, (_med + 1.0 - _med) / 0.8, loc=_med, scale=0.8).rvs
config_dict['source']['parameters']['min_flux_radius'] = 2.0
config_dict['source']['parameters']['minimum_size_in_pixels'] = 12

print("GEN5-COSMOS source: HighSBCOSMOS SB cut %.1f, src_mag median %.1f "
      "(Euclid-tuned; no high-z over-dim)"
      % (config_dict['source']['parameters']['max_source_surface_brightness'],  # noqa: F405
         _med))
