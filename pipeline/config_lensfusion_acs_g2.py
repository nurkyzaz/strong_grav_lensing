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
# Order-agnostic row dispatcher: paltas draws parameters in config-dict order,
# which need not put theta_E first. Each sample calls each overridden param
# exactly once, so: when a param is requested that was already served for the
# current row, a NEW sample has begun -> advance the row. All three params
# therefore always read the SAME row, whatever the draw order. (v1 advanced on
# theta_E only -> e1,e2 lagged one row; caught by g2_join_assign's 1:1 assert.)
_STATE = {"row": 0, "served": set()}


def _g2_row(param):
    if param in _STATE["served"]:
        _STATE["row"] += 1
        _STATE["served"] = set()
    _STATE["served"].add(param)
    return _ROWS[_STATE["row"] % len(_ROWS)]


def _g2_theta_e():
    return float(_g2_row("theta")["theta_E"])


def _g2_e12():
    r = _g2_row("e12")
    return float(r["mass_e1"]), float(r["mass_e2"])


def _g2_zs():
    return float(_g2_row("zs")["z_source"])


config_dict['main_deflector']['parameters']['theta_E'] = _g2_theta_e
config_dict['main_deflector']['parameters']['e1,e2'] = _g2_e12
config_dict['source']['parameters']['z_source'] = _g2_zs
