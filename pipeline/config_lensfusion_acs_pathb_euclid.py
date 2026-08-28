# config_lensfusion_acs_pathb_euclid.py -- EUCLID-ARM variant (2026-07-09, R1.2b-B).
# = pathb arc-only config + HIGH-SURFACE-BRIGHTNESS source selection.
#
# Why: the SLACS source population is COMPACT and high-SB (Newton et al. 2011,
# SLACS XI: unlensed F814W 22-26, mean 24.3, but sub-kpc half-light radii ->
# SB_eff ~ 18-21 mag/arcsec^2), while an unselected COSMOS 23.5 draw averages
# ~22.4 -- 3-4 mag/arcsec^2 LOWER SB. Surface brightness is conserved by
# lensing and sets arc visibility against the deflector glare; at Euclid
# resolution our small-theta_E arcs were therefore invisible (pilot v2:
# 2%/6% pass at theta_E<1.2) while REAL small-theta_E lenses show arcs.
# This is population-matched SELECTION on real COSMOS galaxies (mag_auto +
# flux_radius from the catalog), NOT the banned v0 arbitrary flux boost.
import copy
import os
import sys

import numpy as np

sys.path.insert(0, os.path.expanduser('~/cosmos_acs/tiles'))
from config_lensfusion_acs_pathb_nonoise import *   # noqa: F401,F403
from paltas.Sources.cosmos import COSMOSCatalog, HUBBLE_ACS_PIXEL_WIDTH


class HighSBCOSMOSCatalog(COSMOSCatalog):
    """COSMOSCatalog with (a) a MAX effective-surface-brightness cut:
    SB_eff = mag_auto + 2.5 log10(2 pi (flux_radius * pix)^2) <= threshold
    [mag/arcsec^2] -- selects the compact morphologies of the SLACS source
    population (Newton et al. 2011); and (b) per-draw renormalization of the
    source's TOTAL apparent magnitude to 'source_apparent_magnitude' (drawn
    from the MEASURED Newton unlensed-mag distribution, mean 24.3) -- the
    COSMOS_23.5 catalog floor (m<23.5) is otherwise brighter than the real
    source population, which truncated the faint-arc tail (measured
    2026-07-09: sim prominence 16th pct 47.7 vs real 24.8)."""
    required_parameters = COSMOSCatalog.required_parameters + (
        'max_source_surface_brightness', 'source_apparent_magnitude')

    def _passes_cuts(self):
        is_ok = super()._passes_cuts()
        sb_max = self.source_parameters['max_source_surface_brightness']
        if sb_max is not None:
            r_as = self.catalog['flux_radius'] * HUBBLE_ACS_PIXEL_WIDTH
            with np.errstate(divide='ignore'):
                sb = self.catalog['mag_auto'] + 2.5 * np.log10(
                    2.0 * np.pi * np.clip(r_as, 1e-4, None) ** 2)
            is_ok &= sb <= sb_max
        # C51 (GEN5-only, env-gated so GEN4 pathb is untouched): MAX source
        # half-light radius. Our COSMOS arcs measured ~2.5x too THICK vs real Q1
        # (radial FWHM 1.2" vs 0.47"; Nurkyz "small deflector, thick arc") because
        # COSMOS galaxies are angularly larger than the compact high-z sources real
        # Euclid lenses show. Capping the catalog flux_radius selects compact
        # sources -> thinner, realistic arcs. Off unless LF_SRC_MAX_RE_ARCSEC set.
        import os as _os
        _rmax = _os.environ.get('LF_SRC_MAX_RE_ARCSEC')
        if _rmax:
            r_as = self.catalog['flux_radius'] * HUBBLE_ACS_PIXEL_WIDTH
            is_ok &= r_as <= float(_rmax)
        return is_ok

    def draw_source(self, catalog_i=None, phi=None):
        models, kwargs_list, zs = super().draw_source(catalog_i, phi)
        target = self.source_parameters['source_apparent_magnitude']
        if target is not None:
            kw = kwargs_list[0]
            self.normalize_to_mag(
                kw['image'], float(target),
                self.source_parameters['output_ab_zeropoint'], kw['scale'])
        return models, kwargs_list, zs


config_dict = copy.deepcopy(config_dict)  # noqa: F405
config_dict['source']['class'] = HighSBCOSMOSCatalog
config_dict['source']['parameters']['max_source_surface_brightness'] = 21.0
# keep min_flux_radius modest so compact high-SB galaxies are not excluded
config_dict['source']['parameters']['min_flux_radius'] = 3.0
config_dict['source']['parameters']['minimum_size_in_pixels'] = 12

# E2 (2026-07-09): source REDSHIFT matched to the SLACS source population
# (z_BG ~ 0.5-0.8, median ~0.65; Bolton 2008) instead of the fixed z=1.5.
# (1+z)^4 SB dimming made our arcs ~1.8 mag/arcsec^2 fainter than the real
# population; the theta_E label is set directly by the deflector prior, so
# this changes source APPEARANCE only.
# truncnorm bounds [0.55, 1.1]: LOWER BOUND MUST EXCEED z_lens=0.5 (the
# first C-pilot's [0.3,1.1] allowed ~16% source-in-front-of-lens draws --
# unphysical; caught 2026-07-09, fixed before the full run).
from scipy.stats import truncnorm as _tn
config_dict['source']['parameters']['z_source'] = _tn(
    (0.55 - 0.65) / 0.15, 3.0, loc=0.65, scale=0.15).rvs

# Newton et al. 2011 UNLENSED source apparent-mag distribution (F814W 22-26,
# mean 24.3): per-draw renormalization target. Restores the faint-arc tail
# that the m<23.5 catalog floor removed (Nurkyz 2026-07-09: 'sim arcs a bit
# brighter than real'; measured +13% median, missing faint 16th pct).
config_dict['source']['parameters']['source_apparent_magnitude'] = _tn(
    (22.5 - 24.3) / 1.0, (25.5 - 24.3) / 1.0, loc=24.3, scale=1.0).rvs

no_noise = True


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
