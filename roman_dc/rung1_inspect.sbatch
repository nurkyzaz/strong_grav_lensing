#!/bin/bash
#SBATCH --job-name=rung1_inspect
#SBATCH --partition=normal
#SBATCH --cpus-per-task=2
#SBATCH --mem=16G
#SBATCH --time=00:20:00
#SBATCH --output=/home/user/nurkyz/einstein_cnn/slurm_rung1_inspect_%j.out

# Step 0 of docs/RUNG1_PLAN.md: print the challenge HDF5 structure so we can
# fill in the exact image/label/ID key names for train + predict. CPU-only.
# Run this ONCE on the downloaded labeled file before any training, and also
# open view_rung_1_dataset.ipynb to confirm the submission column + metric.
#
# The rung1 scripts (inspect/train/predict_rung1.py) and train_cnn_paltas.py
# must be present in ~/einstein_cnn (same as train_ablation.sbatch's cwd).
#
#   H5=~/cosmos_acs/roman_dc/roman_data_challenge_rung_1_v_3_0.h5 \
#       sbatch pipeline/rung1_inspect.sbatch
set -e
: "${H5:?set H5=/path/to/labeled_or_unlabeled.h5}"
PY=/home/user/nurkyz/miniconda3/envs/Stronglensing/bin/python
cd /home/user/nurkyz/einstein_cnn

$PY inspect_rung1_h5.py "$H5"
echo RUNG1_INSPECT_DONE
