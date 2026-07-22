#!/bin/bash
#SBATCH --job-name=g5_select
#SBATCH --partition=normal
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=01:00:00
#SBATCH --output=/home/user/nurkyz/cosmos_acs/tiles/g5_c21_select.out

# GEN5 v3b: the arc-VISIBILITY SELECTION step (g4 production recipe, thresh
# 0.8) that the pilot chain skipped — real Q1 lenses are discovery-selected,
# so gates must read the SELECTED sim set (explains the 78.9-vs-103 peak/sky
# CHECK on the unselected v3). Selection runs on the same v2 renders +
# v3 euclidised images; gates re-read on the selected h5.
set -e
set -o pipefail
PY=/home/user/nurkyz/miniconda3/envs/Stronglensing/bin/python
TILES=/home/user/nurkyz/cosmos_acs/tiles
EC=/home/user/nurkyz/einstein_cnn
P=/home/user/nurkyz/paltas_g5_c21_pilot
cd "$EC"

export LF_EUC_SKY_SCALE=2.2
$PY euclidise_arcs.py "$P/sub_pilot" "$P/sub_pilot_euclid_arcs"
$PY arc_visibility_select.py --arcs "$P/sub_pilot_euclid_arcs" \
    --sim "$P/euclid_pilot_v3.h5" --out "$P/euclid_pilot_v3_selected.h5" \
    --thresh 0.8 --min_extent 150

cd "$TILES"
$PY gate_stage0.py --sim "$P/euclid_pilot_v3_selected.h5" \
    --real /home/user/nurkyz/cosmos_acs/q1_slde/q1_slde_eval_f2p85_zoom.h5 \
    --csv failure_features_slacs.csv \
    --meta "$P/sub_pilot/metadata.csv" \
    --out "$P/gate_q1_stats_v3sel.png" || echo "GATE_Q1_NONZERO (read the numbers)"
$PY ar0_arc_gate.py --sim "$P/euclid_pilot_v3_selected.h5" \
    --real /home/user/nurkyz/cosmos_acs/q1_slde/q1_slde_eval_f2p85_zoom.h5 \
    --n 200 --tag g5_c21_q1_v3sel || echo "AR0_Q1_NONZERO (read the numbers)"
$PY side_by_side_real_sim.py \
    --real /home/user/nurkyz/cosmos_acs/q1_slde/q1_slde_eval_f2p85_zoom.h5 \
    --sim "$P/euclid_pilot_v3_selected.h5" --n 8 --seed 5 \
    --out "$P/real_vs_sim_q1_v3sel.png"

echo "GEN5_C21_SELECT_DONE"
