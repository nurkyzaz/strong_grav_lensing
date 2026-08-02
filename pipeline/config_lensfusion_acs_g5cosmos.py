# config_lensfusion_acs_g5cosmos.py — GEN5 with COSMOS sources, EUCLID-tuned.
# (GEN5 ONLY — GEN4 configs config_lensfusion_acs_g2/_pathb* are untouched.)
# Nurkyz fix-list (2026-08-02):
#   - SB cut retuned for Euclid (21 was SLACS)         -> LF_SB_CUT
#   - smaller sources allowed (thinner arcs)           -> min_flux_radius 1.0,
#                                                          minimum_size_in_pixels 8
#   - PHYSICAL cosmological dimming (z-dependent): use source_ABSOLUTE_magnitude so
#     apparent mag = M + distance_modulus(z_source) + k-corr -> high-z sources are
#     automatically fainter (fixes the fixed-apparent-mag gap). LF_SRC_ABSMAG sets
#     the absolute-mag median; set LF_SRC_ABSMAG=off to fall back to a fixed
#     apparent mag (LF_SRC_MAG_MED).
# Uses HighSBCOSMOSCatalog (clean real COSMOS, no PyAutoLens mesh artifacts). The
# manifest's high z_source (~2) both shrinks the source (base z-scaling) and, via
# absolute mag, dims it cosmologically.
import os

from scipy.stats import truncnorm as _tn

from config_lensfusion_acs_g5 import *   # noqa: F401,F403  (GEN5 machinery)
from config_lensfusion_acs_pathb_euclid import HighSBCOSMOSCatalog

_sp = config_dict['source']['parameters']                     # noqa: F405
config_dict['source']['class'] = HighSBCOSMOSCatalog          # noqa: F405
_sp['max_source_surface_brightness'] = float(os.environ.get('LF_SB_CUT', '21.5'))
_sp['min_flux_radius'] = float(os.environ.get('LF_MIN_FLUX_RADIUS', '1.0'))
_sp['minimum_size_in_pixels'] = int(os.environ.get('LF_MIN_SIZE_PX', '8'))

_absmag = os.environ.get('LF_SRC_ABSMAG', '-20.5')
if _absmag.lower() == 'off':
    _med = float(os.environ.get('LF_SRC_MAG_MED', '24.0'))     # fixed apparent (fallback)
    _sp['source_apparent_magnitude'] = _tn(
        (_med - 1.5 - _med) / 0.8, (_med + 1.0 - _med) / 0.8, loc=_med, scale=0.8).rvs
    _mode = 'fixed apparent med %.1f' % _med
else:
    _M = float(_absmag)
    _sp['source_apparent_magnitude'] = None                    # skip HighSB re-norm
    _sp['source_absolute_magnitude'] = _tn(-2, 2, loc=_M, scale=0.7).rvs  # z-dependent
    _mode = 'ABSOLUTE mag med %.1f (z-dependent cosmological dimming)' % _M

print("GEN5-COSMOS source: SB cut %.1f | min_flux_radius %.1f | minimum_size %d | %s"
      % (_sp['max_source_surface_brightness'], _sp['min_flux_radius'],
         _sp['minimum_size_in_pixels'], _mode))
