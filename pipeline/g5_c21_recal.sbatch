#!/bin/bash
#SBATCH --job-name=g5_recal
#SBATCH --partition=normal
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=01:00:00
#SBATCH --output=/home/user/nurkyz/cosmos_acs/tiles/g5_c21_recal.out

# GEN5 v3 = knob recalibration ONLY on the v2 native renders (no re-render;
# the physics passed in v2, per Nurkyz's #4 the noise/flux operators are
# re-tuned AFTER the dimming fixes):
#   Euclid arm: LF_EUC_SKY_SCALE 2.2 (= 1/0.673^2; real Q1 noisier than the
#   nominal EWS spec) -> re-gate stage0 + AR0 vs real Q1.
#   Roman arm: LF_ROM_FLUX 0.17 (= 0.09 x 1.88 gate suggestion) -> re-gate.
set -e
set -o pipefail
PY=/home/user/nurkyz/miniconda3/envs/Stronglensing/bin/python
TILES=/home/user/nurkyz/cosmos_acs/tiles
EC=/home/user/nurkyz/einstein_cnn
P=/home/user/nurkyz/paltas_g5_c21_pilot
cd "$EC"

export LF_EUC_SKY_SCALE=2.2
$PY euclidise.py --inp "$P/native_pilot.h5" --out "$P/euclid_pilot_v3.h5" --seed 955

cd "$TILES"
$PY gate_stage0.py --sim "$P/euclid_pilot_v3.h5" \
    --real /home/user/nurkyz/cosmos_acs/q1_slde/q1_slde_eval_f2p85_zoom.h5 \
    --csv failure_features_slacs.csv \
    --meta "$P/sub_pilot/metadata.csv" \
    --out "$P/gate_q1_stats_v3.png" || echo "GATE_Q1_NONZERO (read the numbers)"
$PY ar0_arc_gate.py --sim "$P/euclid_pilot_v3.h5" \
    --real /home/user/nurkyz/cosmos_acs/q1_slde/q1_slde_eval_f2p85_zoom.h5 \
    --n 200 --tag g5_c21_q1_v3 || echo "AR0_Q1_NONZERO (read the numbers)"
$PY side_by_side_real_sim.py \
    --real /home/user/nurkyz/cosmos_acs/q1_slde/q1_slde_eval_f2p85_zoom.h5 \
    --sim "$P/euclid_pilot_v3.h5" --n 8 --seed 5 \
    --out "$P/real_vs_sim_q1_v3.png"

export LF_ROM_FLUX=0.17
$PY romanise.py --inp "$P/native_pilot.h5" --out "$P/roman_pilot.h5" --seed 956
export LF_G5ROM_DIR="$P"
$PY g5rom_pilot_gate.py || echo "ROM_GATE_NONZERO (read the numbers)"

echo "GEN5_C21_RECAL_DONE"
