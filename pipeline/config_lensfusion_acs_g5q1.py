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
import config_lensfusion_acs_g2 as _g2
from q1_source_catalog import Q1SourceCatalog

config_dict['source']['class'] = Q1SourceCatalog          # noqa: F405
_sp = config_dict['source']['parameters']                 # noqa: F405
_sp['q1_source_file'] = os.environ.get(
    'LF_Q1_SRC',
    '/home/user/nurkyz/cosmos_acs/q1_slde/q1_sources_smooth.h5')
_sp['q1_source_pixscale'] = float(os.environ.get('LF_Q1_PIXSCALE', '0.05'))
# C53: optional brightness normalization (decouple arc mag from pixscale/thickness).
# LF_Q1_SRCMAG = target source apparent mag; 'off' (default) = native amplitude.
_q1mag = os.environ.get('LF_Q1_SRCMAG', 'off')
_sp['q1_source_apparent_magnitude'] = None if _q1mag.lower() == 'off' else float(_q1mag)

print("GEN5-Q1 CONFIG: real delensed Q1 sources (LF_Q1_PIXSCALE=%s, src_mag=%s)"
      % (_sp['q1_source_pixscale'], _sp['q1_source_apparent_magnitude']))

# ---- CARRY THE FULL GEN5 RECIPE (do NOT drop fixes when swapping the source) ----
# C49: ABSOLUTE source offset (manifest source_cx/cy) -> magnification-theta_E
# coupling + partial/off-axis arcs. Same block as config_lensfusion_acs_g5cosmos.
if (_g2._ROWS and "source_cx" in _g2._ROWS[0]
        and any(float(r.get("source_cx", 0) or 0) or float(r.get("source_cy", 0) or 0)
                for r in _g2._ROWS[:100])):
    def _g2_src_cx():
        return float(_g2._g2_row("scx")["source_cx"])

    def _g2_src_cy():
        return float(_g2._g2_row("scy")["source_cy"])

    _sp['center_x'] = _g2_src_cx
    _sp['center_y'] = _g2_src_cy
    print("GEN5-Q1 source offset: absolute per-row (manifest source_cx/source_cy)")

# C45: magnification cut matched to real Euclid Q1 (median 2.6). GEN5-only.
mag_cut = float(os.environ.get('LF_MAG_CUT', str(mag_cut)))  # noqa: F405,F811
print("GEN5-Q1 mag_cut = %.2f" % mag_cut)
