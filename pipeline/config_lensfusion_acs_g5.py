# config_lensfusion_acs_g5.py — GEN5 (high-z: Euclid-Q1 + Roman) manifest-
# driven config (Nurkyz naming ruling 2026-07-22: GEN4 = low-z native
# SLACS/S4TM, GEN5 = the z-migrated high-z population).
# Inherits the FULL g2 manifest machinery (theta_E / e1,e2 / z_source /
# optional gamma1,gamma2 read per-row from LF_G2_MANIFEST) and adds:
#  * PEMDShearFourMultipole with the manifest's isophote-anchored m=3,4
#    multipoles (AR3) and per-row MIGRATED z_lens (C21);
#  * Gen5HighZSource: dims each Newton-renormalized source draw by the
#    distance-modulus + flat-nu K-correction from the Newton reference
#    population (z ~ 0.65, where the mean-24.3 mags were MEASURED) to the
#    row's drawn z_source — fixes the arcs-not-dimmed bug (Nurkyz review
#    2026-07-22): HighSBCOSMOSCatalog.normalize_to_mag overwrote paltas's
#    cosmological dimming with a low-z-calibrated apparent-mag prior.
# mult2 is zeroed: the m=2 moment is already the PEMD ellipticity.
import numpy as _np

from config_lensfusion_acs_g2 import *   # noqa: F401,F403
import config_lensfusion_acs_g2 as _g2
from config_lensfusion_acs_pathb_euclid import HighSBCOSMOSCatalog
from paltas.MainDeflector.simple_deflectors import PEMDShearFourMultipole

GEN5_ZS_REF = 0.65   # Newton unlensed-mag prior reference redshift


class Gen5HighZSource(HighSBCOSMOSCatalog):
    """HighSB + Newton-mag source with GEN5 high-z dimming: after the
    Newton apparent-magnitude renormalization (calibrated at z~0.65), dim
    by dm = 5 log10(D_L(z_s)/D_L(0.65)) - 2.5 log10((1+z_s)/(1+0.65))
    (luminosity distance + flat-f_nu K-correction). DISCLOSED proxy: no
    source luminosity-function evolution — the AR0 arc gate vs real Q1
    arbitrates the residual."""

    def draw_source(self, catalog_i=None, phi=None):
        models, kwargs_list, zs = super().draw_source(catalog_i, phi)
        z_s = float(self.source_parameters['z_source'])
        dl_ratio = (self.cosmo.luminosityDistance(z_s)
                    / self.cosmo.luminosityDistance(GEN5_ZS_REF))
        dm = 5.0 * _np.log10(dl_ratio) - 2.5 * _np.log10(
            (1.0 + z_s) / (1.0 + GEN5_ZS_REF))
        kwargs_list[0]['image'] *= 10.0 ** (-0.4 * dm)
        return models, kwargs_list, zs


print("GEN5 SOURCE DIMMING ACTIVE (Newton mags dimmed by DL+K from z_ref "
      "%.2f to the row z_source)" % GEN5_ZS_REF)
config_dict['source']['class'] = Gen5HighZSource


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
