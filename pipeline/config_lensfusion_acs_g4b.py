# config_lensfusion_acs_g4b.py — C21/AR3 manifest-driven config.
# Inherits the FULL g2 manifest machinery (theta_E / e1,e2 / z_source /
# optional gamma1,gamma2 read per-row from LF_G2_MANIFEST) and upgrades the
# main deflector to PEMDShearFourMultipole with the manifest's
# isophote-anchored m=3,4 multipoles (AR3) and per-row MIGRATED z_lens (C21).
# mult2 is zeroed: the m=2 moment is already the PEMD ellipticity.
from config_lensfusion_acs_g2 import *   # noqa: F401,F403
import config_lensfusion_acs_g2 as _g2
from paltas.MainDeflector.simple_deflectors import PEMDShearFourMultipole


def _g4b_z_lens():
    return float(_g2._g2_row("zl")["z_l_new"])


def _g4b_m3a():
    return float(_g2._g2_row("m3a")["mult3_a"])


def _g4b_m3phi():
    return float(_g2._g2_row("m3phi")["mult3_phi"])


def _g4b_m4a():
    return float(_g2._g2_row("m4a")["mult4_a"])


def _g4b_m4phi():
    return float(_g2._g2_row("m4phi")["mult4_phi"])


config_dict['main_deflector']['class'] = PEMDShearFourMultipole
_P = config_dict['main_deflector']['parameters']
_P['z_lens'] = _g4b_z_lens
_P['mult2_a'] = 0.0
_P['mult2_phi'] = 0.0
_P['mult2_center_x'] = 0.0
_P['mult2_center_y'] = 0.0
_P['mult3_a'] = _g4b_m3a
_P['mult3_phi'] = _g4b_m3phi
_P['mult3_center_x'] = 0.0
_P['mult3_center_y'] = 0.0
_P['mult4_a'] = _g4b_m4a
_P['mult4_phi'] = _g4b_m4phi
_P['mult4_center_x'] = 0.0
_P['mult4_center_y'] = 0.0
