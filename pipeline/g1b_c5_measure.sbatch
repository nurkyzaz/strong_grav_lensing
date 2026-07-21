#!/bin/bash
#SBATCH --job-name=g1b_c5
#SBATCH --partition=normal
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=02:00:00
#SBATCH --output=/home/user/nurkyz/cosmos_acs/tiles/g1b_c5.out

# C5 (2026-07-21): G1b library build + measurement pass with isophote a3/a4.
# Stage 1: builder v5 on the 779 fetched cutouts, keep_final-filtered
#          (C29: consumes tables/g1b_prune_final.csv, NOT the raw review CSV)
#          + the standing auto-screens (faint / q<0.5 / blank / trail).
# Stage 2 PILOT: measure first 20 stamps incl. isophote fits + previews.
#          Chain STOPS here for visual inspection (standing pilot-gate rule).
#          Full measure runs via MEASURE_FULL=1 sbatch --export=ALL,... resub
#          or g1b_c5_full.sbatch.
set -e
PY=/home/user/nurkyz/miniconda3/envs/Stronglensing/bin/python
cd /home/user/nurkyz/cosmos_acs/tiles

$PY build_deflector_from_lrg.py \
    --inp /home/user/nurkyz/einstein_cnn/real_lrgdefl2b_images_256.h5 \
    --out deflector_stamps_lrg2b_raw.h5 \
    --keep_csv g1b_prune/g1b_prune_final.csv

if [ "${MEASURE_FULL:-0}" = "1" ]; then
    $PY g1b_measure_stamps.py --stamps deflector_stamps_lrg2b_raw.h5 \
        --src /home/user/nurkyz/einstein_cnn/real_lrgdefl2b_images_256.h5 \
        --labels /home/user/nurkyz/einstein_cnn/lrgdefl2b_labels.csv \
        --out g1b_kinematics_v1.csv \
        --preview g1b_measure_preview.png --iso_preview g1b_iso_preview.png
    echo "G1B_C5_FULL_DONE"
else
    $PY g1b_measure_stamps.py --stamps deflector_stamps_lrg2b_raw.h5 \
        --src /home/user/nurkyz/einstein_cnn/real_lrgdefl2b_images_256.h5 \
        --labels /home/user/nurkyz/einstein_cnn/lrgdefl2b_labels.csv \
        --out g1b_kinematics_pilot.csv --limit 20 \
        --preview g1b_pilot_preview.png --iso_preview g1b_pilot_iso.png
    echo "G1B_C5_PILOT_DONE (inspect previews, then resubmit with MEASURE_FULL=1)"
fi
