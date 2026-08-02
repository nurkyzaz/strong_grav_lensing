#!/bin/bash
#SBATCH --job-name=g5q1_pilot
#SBATCH --partition=normal
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=02:30:00
#SBATCH --output=/home/user/nurkyz/cosmos_acs/tiles/g5q1_pilot.out
# GEN5-Q1 FULL 200 PILOT with the calibrated recipe (C37): real Q1 delensed
# sources, LF_Q1_PIXSCALE=0.03, arc_flux_scale=0.5, companion 2-9, sky 2.2,
# arc-visibility selection 0.8/150. Final eyeball before full generation.
set -e
set -o pipefail
PY=/home/user/nurkyz/miniconda3/envs/Stronglensing/bin/python
TILES=/home/user/nurkyz/cosmos_acs/tiles
EC=/home/user/nurkyz/einstein_cnn
P=/home/user/nurkyz/paltas_g5q1_pilot
M=/home/user/nurkyz/paltas_g5_c21_pilot/manifest_pilot.csv
Q1REAL=/home/user/nurkyz/cosmos_acs/q1_slde/q1_slde_eval_f2p85_zoom.h5
mkdir -p "$P"
cd "$TILES"
export LF_PSF_KERNEL=psf_bank_v2/kernel_00_extended.npy
export LF_G2_MANIFEST="$M"
export LF_Q1_SRC=/home/user/nurkyz/cosmos_acs/q1_slde/q1_sources_smooth.h5
export LF_Q1_PIXSCALE=0.03
$PY run_paltas_pilot.py config_lensfusion_acs_g5q1.py "$P/sub" --n 200 --seed 951 \
    2>&1 | tee "$P/render.log"
grep -q "Q1 SOURCE LIBRARY ACTIVE" "$P/render.log" || { echo "FAIL: Q1 source banner"; exit 1; }
$PY g2_join_assign.py "$P/sub" "$M" "$P/assign.csv"
$PY hybrid_combine.py --run "$P/sub" --empty empty_cutouts_expanded_screened.h5 \
    --real "$EC/real_dapool_images.h5" \
    --out "$P/native.h5" --seed 952 \
    --deflector_stamps deflector_stamps_lrg2b_raw.h5 \
    --deflector_manifest "$P/assign.csv" --deflector_jitter 1.0 \
    --companion_stamps source_stamps_clean.h5 \
    --companion_rate_lo 2 --companion_rate_hi 9 --companion_flux_pct 35 \
    --arc_poisson --arc_flux_scale 0.5
cd "$EC"
export LF_EUC_SKY_SCALE=2.2
$PY euclidise.py --inp "$P/native.h5" --out "$P/euclid.h5" --seed 955
$PY euclidise_arcs.py "$P/sub" "$P/sub_euclid_arcs"
$PY arc_visibility_select.py --arcs "$P/sub_euclid_arcs" --sim "$P/euclid.h5" \
    --out "$P/euclid_sel.h5" --thresh 0.8 --min_extent 150 || echo SELECT_NOTE
cd "$TILES"
echo "--- stage0 gate vs real Q1 ---"
$PY gate_stage0.py --sim "$P/euclid.h5" --real "$Q1REAL" --csv failure_features_slacs.csv \
    --meta "$P/sub/metadata.csv" --out "$P/gate_q1.png" || echo GATE_NZ
echo "--- AR0 arc gate vs real Q1 ---"
$PY ar0_arc_gate.py --sim "$P/euclid.h5" --real "$Q1REAL" --n 200 --tag g5q1_pilot || echo AR0_NZ
$PY side_by_side_real_sim.py --real "$Q1REAL" --sim "$P/euclid.h5" --n 8 --seed 5 \
    --out "$P/real_vs_sim_g5q1_pilot.png"
echo "G5Q1_PILOT_DONE"
