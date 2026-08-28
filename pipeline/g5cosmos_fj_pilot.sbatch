#!/bin/bash
#SBATCH --job-name=g5cos_fj
#SBATCH --partition=normal
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=03:00:00
#SBATCH --output=/home/user/nurkyz/cosmos_acs/tiles/g5cosmos_fj_pilot.out
# GEN5-COSMOS FJ pilot: the 3 Nurkyz fixes (2026-08-02 review) on top of the
# converged recipe:
#   (1) C40 Faber-Jackson deflector brightness (--deflector_fj): deflector TOTAL
#       flux set from per-row theta_E; calibrated (mag0 18.88, slope 2.5,
#       scatter 0.60) to PRESERVE the approved brightness AND rho(mag,theta)~-0.5
#       (== real Q1 -0.47), now PRINCIPLED not a migration accident.
#   (2) C41 theta_E-scaled source offset (manifest_match_off.csv): partial arcs
#       at every theta_E instead of full rings for large theta.
#   (3) arc-visibility selection threshold 4 -> 6: drop the still-invisible arcs.
set -e
set -o pipefail
PY=/home/user/nurkyz/miniconda3/envs/Stronglensing/bin/python
TILES=/home/user/nurkyz/cosmos_acs/tiles
EC=/home/user/nurkyz/einstein_cnn
P=/home/user/nurkyz/paltas_g5cosmos_fj
M=/home/user/nurkyz/paltas_g5_c21_pilot/manifest_match_off.csv
Q1REAL=/home/user/nurkyz/cosmos_acs/q1_slde/q1_slde_eval_f2p85_zoom.h5
mkdir -p "$P"
cd "$TILES"
export LF_PSF_KERNEL=psf_bank_v2/kernel_00_extended.npy
export LF_G2_MANIFEST="$M"
export LF_SB_CUT=21.5
export LF_SRC_ABSMAG=-24.5
export LF_MIN_FLUX_RADIUS=1.0
export LF_MIN_SIZE_PX=8
$PY run_paltas_pilot.py config_lensfusion_acs_g5cosmos.py "$P/sub" --n 240 --seed 951
$PY g2_join_assign.py "$P/sub" "$M" "$P/assign.csv"
$PY hybrid_combine.py --run "$P/sub" --empty empty_cutouts_expanded_screened.h5 \
    --real "$EC/real_dapool_images.h5" \
    --out "$P/native.h5" --seed 952 \
    --deflector_stamps deflector_stamps_lrg2b_raw.h5 \
    --deflector_manifest "$P/assign.csv" --deflector_jitter 1.0 \
    --deflector_fj --fj_mag0 18.88 --fj_slope 2.5 --fj_theta0 0.88 --fj_scatter 0.60 \
    --companion_stamps source_stamps_clean.h5 \
    --companion_rate_lo 0 --companion_rate_hi 3 --companion_flux_pct 35 \
    --companion_rmin 30 --companion_area_uniform --arc_poisson
cd "$EC"; export LF_EUC_SKY_SCALE=2.2 LF_EUC_NOISE_CORR=0.45
$PY euclidise.py --inp "$P/native.h5" --out "$P/euclid.h5" --seed 955
$PY euclidise_arcs.py "$P/sub" "$P/sub_arcs"
$PY arc_visibility_select.py --arcs "$P/sub_arcs" --sim "$P/euclid.h5" \
    --out "$P/euclid_sel.h5" --thresh 6.0 --min_extent 300 2>&1 | tail -2
cd "$TILES"
$PY ar0_arc_gate.py --sim "$P/euclid_sel.h5" --real "$Q1REAL" --n 80 --tag fj || echo AR0_NZ
$PY side_by_side_real_sim.py --real "$Q1REAL" --sim "$P/euclid_sel.h5" --n 8 --seed 3 \
    --out "$P/sbs_fj.png"
echo "G5COSMOS_FJ_DONE"
