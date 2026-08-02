# config_lensfusion_acs_g5q1.py — GEN5 with REAL Q1 delensed sources (C37).
# Inherits the full GEN5 machinery (manifest theta_E / e1,e2 / z_source / gamma;
# PEMDShearFourMultipole AR3 multipoles; per-row migrated z_lens) and ONLY swaps
# the lensed-source population: Gen5HighZSource (dimmed low-z COSMOS -> faint
# diffuse arcs) -> Q1SourceCatalog (real delensed Euclid Q1 source-plane
# reconstructions, native amplitude preserved -> real Euclid arc surface
# brightness). Source library + arc-thickness pixscale via env:
#   LF_Q1_SRC       path to q1_sources_smooth.h5   (default below)
#   LF_Q1_PIXSCALE  source-plane arcsec/px          (default 0.05; calibratable)
import os

from config_lensfusion_acs_g5 import *   # noqa: F401,F403  (GEN5 machinery)
from q1_source_catalog import Q1SourceCatalog

config_dict['source']['class'] = Q1SourceCatalog          # noqa: F405
config_dict['source']['parameters']['q1_source_file'] = os.environ.get(
    'LF_Q1_SRC',
    '/home/user/nurkyz/cosmos_acs/q1_slde/q1_sources_smooth.h5')
config_dict['source']['parameters']['q1_source_pixscale'] = float(
    os.environ.get('LF_Q1_PIXSCALE', '0.05'))

print("GEN5-Q1 CONFIG: real delensed Q1 sources swapped in for COSMOS "
      "(LF_Q1_PIXSCALE=%s)" % config_dict['source']['parameters']  # noqa: F405
      ['q1_source_pixscale'])
