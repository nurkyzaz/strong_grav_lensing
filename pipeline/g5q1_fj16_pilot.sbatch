#!/bin/bash
#SBATCH --job-name=g5q1_fj16
#SBATCH --partition=normal
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=03:00:00
#SBATCH --output=/home/user/nurkyz/cosmos_acs/tiles/fj16_pilot.out
# GEN5 fj15: switch SOURCE library COSMOS -> real Q1 delensed sources (plan
# #12/#14 arc thickness + clumpiness), carrying the FULL fj13 recipe unchanged:
#   FJ deflector (mag0 21.39/slope 4.5/scatter 1.15) + truncated tail [19.2,23.4]
#   + edge-smooth 1.5 + ABSOLUTE source offset (manifest_match_abs, r_max 0.4)
#   + mag_cut 2.0 + companions + noise (SKY 2.2, CORR 0.45) + sel floor 7.6.
# COSMOS-only source knobs (SB cut, min/max Re, ABSMAG) are DROPPED — Q1 sources
# are real compact sources; arc thickness/brightness now via LF_Q1_PIXSCALE.
set -e
set -o pipefail
PY=/home/user/nurkyz/miniconda3/envs/Stronglensing/bin/python
TILES=/home/user/nurkyz/cosmos_acs/tiles
EC=/home/user/nurkyz/einstein_cnn
P=/home/user/nurkyz/paltas_g5q1_fj16
M=/home/user/nurkyz/paltas_g5_c21_pilot/manifest_match_abs.csv
Q1REAL=/home/user/nurkyz/cosmos_acs/q1_slde/q1_slde_eval_f2p85_zoom.h5
mkdir -p "$P"
cd "$TILES"
export LF_PSF_KERNEL=psf_bank_v2/kernel_00_extended.npy
export LF_G2_MANIFEST="$M"
export LF_MAG_CUT=2.0
export LF_Q1_PIXSCALE=0.016
export LF_Q1_SRCMAG=23.0
$PY run_paltas_pilot.py config_lensfusion_acs_g5q1.py "$P/sub" --n 240 --seed 1061
$PY g2_join_assign.py "$P/sub" "$M" "$P/assign.csv"
$PY hybrid_combine.py --run "$P/sub" --empty empty_cutouts_expanded_screened.h5 \
    --real "$EC/real_dapool_images.h5" --out "$P/native.h5" --seed 1062 \
    --deflector_stamps deflector_stamps_lrg2b_raw.h5 \
    --deflector_manifest "$P/assign.csv" --deflector_jitter 1.0 \
    --deflector_fj --fj_mag0 21.39 --fj_slope 4.5 --fj_theta0 0.88 --fj_scatter 1.15 \
    --fj_mag_min 19.2 --fj_mag_max 23.4 --deflector_edgesmooth 1.5 \
    --companion_stamps source_stamps_clean.h5 \
    --companion_rate_lo 0 --companion_rate_hi 3 --companion_flux_pct 35 \
    --companion_rmin 30 --companion_area_uniform --arc_poisson
cd "$EC"
export LF_EUC_SKY_SCALE=2.2 LF_EUC_NOISE_CORR=0.45
$PY euclidise.py --inp "$P/native.h5" --out "$P/euclid.h5" --seed 1065
$PY euclidise_arcs.py "$P/sub" "$P/sub_arcs"
$PY arc_visibility_select.py --arcs "$P/sub_arcs" --sim "$P/euclid.h5" \
    --out "$P/euclid_sel.h5" --thresh 6 --min_extent 100 --min_sky_snr 7.6
cd "$TILES"
echo "=== ARC WIDTH (target real 0.47) ==="; $PY arc_width_theta.py "$P" || true
echo "=== MORPHOLOGY ==="; $PY sim_arc_morph.py "$P" || true
echo "=== PHOTOMETRY ==="; $PY measure_phot.py "$P" || true
echo "=== COUPLING ==="; $PY coupling.py "$P" euclid.h5 || true
$PY ar0_arc_gate.py --sim "$P/euclid_sel.h5" --real "$Q1REAL" --n 80 --tag fj16 || echo AR0NZ
echo G5Q1_FJ16_DONE
