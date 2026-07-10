# config_lensfusion_acs_g2.py — GEN4-G2 manifest-driven population config.
# Inherits the FULL Euclid-arm recipe (HighSB sources + Newton mags + SLACS z
# machinery) from config_lensfusion_acs_pathb_euclid, then OVERRIDES the mass
# and source-z draws with values from the population manifest (one physically
# self-consistent system per row: real galaxy's sigma_v -> theta_E, mass shape
# = measured light shape (+scatter), z_source matched).
# Manifest path from env LF_G2_MANIFEST. Rows are consumed one per DRAW
# attempt (theta_E advances the row; e1,e2 / z_source read the current row) —
# mag_cut rejections skip rows, the g2_join_assign.py step recovers the
# accepted-row mapping by exact theta_E match.
import csv as _csv
import os as _os

from config_lensfusion_acs_pathb_euclid import *   # noqa: F401,F403

_MANIFEST = _os.environ["LF_G2_MANIFEST"]
_ROWS = list(_csv.DictReader(open(_MANIFEST)))
_STATE = {"i": -1}


def _g2_theta_e():
    _STATE["i"] += 1
    return float(_ROWS[_STATE["i"] % len(_ROWS)]["theta_E"])


def _g2_e12():
    r = _ROWS[_STATE["i"] % len(_ROWS)]
    return float(r["mass_e1"]), float(r["mass_e2"])


def _g2_zs():
    return float(_ROWS[_STATE["i"] % len(_ROWS)]["z_source"])


config_dict['main_deflector']['parameters']['theta_E'] = _g2_theta_e
config_dict['main_deflector']['parameters']['e1,e2'] = _g2_e12
config_dict['source']['parameters']['z_source'] = _g2_zs
