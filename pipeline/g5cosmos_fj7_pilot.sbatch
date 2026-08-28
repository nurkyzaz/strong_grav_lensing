#!/bin/bash
#SBATCH --job-name=g5cos_fj7
#SBATCH --partition=normal
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=03:00:00
#SBATCH --output=/home/user/nurkyz/cosmos_acs/tiles/g5cosmos_fj7_pilot.out
# GEN5-COSMOS fj6: PHYSICS-config fix for arc MORPHOLOGY (Nurkyz 2026-08-03).
# Real Q1 arc morphology (measured from source_light.fits, N=322):
#   completeness 0.26/0.43/0.68 (61% partial<0.5, only 17% full-ring>0.8), n_knots 2.
# Our fj2: completeness 0.52 (30% full-ring), n_knots 1 -> too ring-like.
# Changes (physics, not brightness):
#   C41 offset widened theta_E*U(0.15,0.45)->U(0.30,0.80)  [manifest_match_off3]
#   C45 mag_cut 3.0 -> 2.0 (real total_magnification median 2.6, q25 2.0)
# Deflector FJ mag0 21.39 (matched, C40) + edge smooth 1.5 (C43). No brightness tuning.
set -e
set -o pipefail
PY=/home/user/nurkyz/miniconda3/envs/Stronglensing/bin/python
TILES=/home/user/nurkyz/cosmos_acs/tiles
EC=/home/user/nurkyz/einstein_cnn
P=/home/user/nurkyz/paltas_g5cosmos_fj7
M=/home/user/nurkyz/paltas_g5_c21_pilot/manifest_match_off2.csv
Q1REAL=/home/user/nurkyz/cosmos_acs/q1_slde/q1_slde_eval_f2p85_zoom.h5
mkdir -p "$P"
cd "$TILES"
export LF_PSF_KERNEL=psf_bank_v2/kernel_00_extended.npy
export LF_G2_MANIFEST="$M"
export LF_SB_CUT=21.5
export LF_SRC_ABSMAG=-24.5
export LF_MIN_FLUX_RADIUS=1.0
export LF_MIN_SIZE_PX=8
export LF_MAG_CUT=2.0
$PY run_paltas_pilot.py config_lensfusion_acs_g5cosmos.py "$P/sub" --n 240 --seed 981
$PY g2_join_assign.py "$P/sub" "$M" "$P/assign.csv"
$PY hybrid_combine.py --run "$P/sub" --empty empty_cutouts_expanded_screened.h5 \
    --real "$EC/real_dapool_images.h5" \
    --out "$P/native.h5" --seed 982 \
    --deflector_stamps deflector_stamps_lrg2b_raw.h5 \
    --deflector_manifest "$P/assign.csv" --deflector_jitter 1.0 \
    --deflector_fj --fj_mag0 21.39 --fj_slope 4.5 --fj_theta0 0.88 --fj_scatter 1.15 \
    --deflector_edgesmooth 1.5 \
    --companion_stamps source_stamps_clean.h5 \
    --companion_rate_lo 0 --companion_rate_hi 3 --companion_flux_pct 35 \
    --companion_rmin 30 --companion_area_uniform --arc_poisson
cd "$EC"; export LF_EUC_SKY_SCALE=2.2 LF_EUC_NOISE_CORR=0.45
$PY euclidise.py --inp "$P/native.h5" --out "$P/euclid.h5" --seed 985
$PY euclidise_arcs.py "$P/sub" "$P/sub_arcs"
$PY arc_visibility_select.py --arcs "$P/sub_arcs" --sim "$P/euclid.h5" \
    --out "$P/euclid_sel.h5" --thresh 6 --min_extent 100 2>&1 | tail -2
cd "$TILES"
echo "--- ARC MORPHOLOGY vs REAL ---"
$PY sim_arc_morph.py "$P" || true
echo "--- PHOTOMETRY vs REAL ---"
$PY -c "import sys; sys.argv=['x','$P']; "$P" && $PY measure_phot.py "$P" || true
$PY ar0_arc_gate.py --sim "$P/euclid_sel.h5" --real "$Q1REAL" --n 80 --tag fj7 || echo AR0_NZ
echo "G5COSMOS_FJ7_DONE"
