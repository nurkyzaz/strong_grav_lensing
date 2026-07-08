# config_lensfusion_acs.py
# paltas config for the LensFusion Einstein-radius CNN training set.
# Matches the real SLACS benchmark grid: 128 px @ 0.05"/px = 6.4" FOV, HST ACS/WFC F814W.
#   - real COSMOS source galaxies (physically lensed)
#   - SLACS-sized PARAMETRIC Sersic deflector light (R_sersic ~1.2", bright ellipticals)
#   - REAL STScI focus-diverse ePSF (acs_psf_epsf23_extended.npy, j9op01l7q @ WFC1 center, detector-sampled)
#   - theta_E ~ U[0.6,2.2] : SIE convention == your SLACS b_SIE labels; flat prior fights prior-pull
# Run:  python -m paltas.generate config_lensfusion_acs.py ~/simct_paltas --n 50000 --h5
import os
import numpy as np
from scipy.stats import norm, truncnorm, uniform
import paltas.Sampling.distributions as dist
from paltas.MainDeflector.simple_deflectors import PEMDShear
from paltas.Sources.cosmos import COSMOSCatalog
from paltas.Sources.sersic import SingleSersicSource

# ---- grid (match the SLACS cutouts) ----
numpix = 128
kwargs_numerics = {'supersampling_factor': 1}

# ACS/WFC F814W AB zeropoint -- CONFIRM for your epoch (~25.94)
output_ab_zeropoint = 25.94

# ---- STScI focus-diverse ePSF, detector-sampled 23px (ISR 2018-08/2023-06; Moffat interim retired same day) ----
_here = os.path.dirname(os.path.abspath(__file__))
_psf_file = os.environ.get('LF_PSF_KERNEL', 'acs_psf_epsf23_extended.npy')
psf_kernel = np.load(_psf_file if os.path.isabs(_psf_file)
                     else os.path.join(_here, _psf_file)).astype('float64')
psf_kernel /= psf_kernel.sum()

# ---- real COSMOS source folder (from galsim_download_cosmos -s 23.5 -d ~/paltas_data) ----
cosmos_folder = os.path.expanduser('~/paltas_data/COSMOS_23.5_training_sample/')

class ApparentSersic(SingleSersicSource):
    """SingleSersicSource with `magnitude` interpreted as APPARENT magnitude
    (the paltas 0.1.1 convention). Needed because paltas 0.2.0 treats
    `magnitude` as ABSOLUTE and converts via absolute_to_apparent(z_source),
    which renders apparent-style values (e.g. 17) at zero flux.
    z_source is kept only for the returned redshift list (discarded for
    lens light by config_handler)."""
    def draw_source(self):
        sersic_params = {
            k: v for k, v in self.source_parameters.items()
            if k in self.required_parameters}
        sersic_params.pop('z_source')
        sersic_params.pop('output_ab_zeropoint')
        sersic_params.pop('magnitude')
        sersic_params['amp'] = SingleSersicSource.mag_to_amplitude(
            self.source_parameters['magnitude'],
            self.source_parameters['output_ab_zeropoint'], sersic_params)
        return (['SERSIC_ELLIPSE'], [sersic_params],
                [self.source_parameters['z_source']])


config_dict = {
    'main_deflector': {
        'class': PEMDShear,
        'parameters': {
            'M200': 1e13,
            'z_lens': 0.5,
            'gamma': truncnorm(-3, 3, loc=2.0, scale=0.15).rvs,  # density slope ~ isothermal (Stage 2a width)
            'theta_E': uniform(loc=0.45, scale=1.85).rvs,       # U[0.45,2.3]: flat, pads BOTH benchmark edges (S4TM min 0.54; audit 2026-07-06)
            'e1': norm(loc=0.0, scale=0.1).rvs,
            'e2': norm(loc=0.0, scale=0.1).rvs,
            'center_x': norm(loc=0.0, scale=0.05).rvs,           # mass centre jittered vs light (Stage 2a)
            'center_y': norm(loc=0.0, scale=0.05).rvs,
            'gamma1': norm(loc=0.0, scale=0.04).rvs,             # mild external shear
            'gamma2': norm(loc=0.0, scale=0.04).rvs,
            'ra_0': 0.0, 'dec_0': 0.0
        }
    },
    'source': {
        'class': COSMOSCatalog,
        'parameters': {
            'z_source': 1.5,
            'cosmos_folder': cosmos_folder,
            'max_z': 1.0, 'minimum_size_in_pixels': 20, 'faintest_apparent_mag': 23.5,
            'smoothing_sigma': 0.0, 'random_rotation': True,
            'output_ab_zeropoint': output_ab_zeropoint,
            'min_flux_radius': 5.0,
            'center_x': uniform(loc=-0.25, scale=0.5).rvs,       # source offset U(+-0.25") (Stage 2a)
            'center_y': uniform(loc=-0.25, scale=0.5).rvs
        }
    },
    'lens_light': {
        'class': ApparentSersic,
        'parameters': {
            'z_source': 0.5,                                     # deflector light at z_lens
            'magnitude': uniform(loc=15.6, scale=4.1).rvs,       # DATA-DRIVEN: real SLACS deflectors [15.93,19.32] padded (2026-07-05)
            'output_ab_zeropoint': output_ab_zeropoint,
            'R_sersic': truncnorm(-2.12, 4.57, loc=1.98, scale=0.75).rvs,  # DATA-DRIVEN: Bolton08 Re of the 62 benchmark lenses (2026-07-05)
            'n_sersic': truncnorm(-4, 4, loc=4.0, scale=0.5).rvs,     # de Vaucouleurs
            'e1,e2': dist.EllipticitiesTranslation(
                q_dist=truncnorm(-3, 1, loc=0.8, scale=0.15).rvs,
                phi_dist=uniform(loc=-np.pi/2, scale=np.pi).rvs),
            'center_x': norm(loc=0.0, scale=0.02).rvs,           # light ~ cutout centre; mass decoupled
            'center_y': norm(loc=0.0, scale=0.02).rvs
        }
    },
    'cosmology': {'parameters': {'cosmology_name': 'planck18'}},
    'psf': {
        'parameters': {
            'psf_type': 'PIXEL',
            'kernel_point_source': psf_kernel,
            'point_source_supersampling_factor': 1
        }
    },
    'detector': {
        'parameters': {
            # ACS/WFC F814W: tune exposure_time/sky_brightness so the sim sky RMS matches
            # your real SLACS cutouts (compare to the sky_rms column in failure_features_slacs.csv)
            'pixel_scale': 0.05, 'ccd_gain': 2.0, 'read_noise': 4.0,
            'magnitude_zero_point': output_ab_zeropoint,
            'exposure_time': 675.0, 'sky_brightness': 22.1,
            'num_exposures': 1, 'background_noise': None
        }
    }
}

# Stage 0.3: require genuinely lensed geometry (anti-blob gate)
mag_cut = 3.0


# ---- Stage-1.2c (2026-07-05): JOINT empirical (magnitude, R_sersic) prior ----
# Independent draws made unreal faint+huge deflectors (peak/sky 307 vs real
# >=492): real ellipticals correlate brightness and size. Sample per-lens
# (aperture mag, Bolton08 Re) pairs from the 63 benchmark deflectors with
# jitter (+-0.3 mag, x[0.85,1.15] Re); cross_object overrides the independent
# magnitude/R_sersic entries above (paltas warns once about the overwrite --
# expected, ignore).
import pandas as _pd

_emp = _pd.read_csv(os.path.join(_here, 'lens_light_empirical.csv'))
_EMP_MAG = _emp['mag'].values
_EMP_RE = _emp['re'].values


def _joint_mag_re():
    i = np.random.randint(len(_EMP_MAG))
    mag = float(_EMP_MAG[i] + np.random.uniform(-0.3, 0.3))
    re = float(np.clip(_EMP_RE[i] * np.random.uniform(0.85, 1.15), 0.4, 7.0))
    return mag, re


config_dict['cross_object'] = {'parameters': {
    'lens_light:magnitude,lens_light:R_sersic': _joint_mag_re}}
