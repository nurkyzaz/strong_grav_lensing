#!/bin/bash
#SBATCH --job-name=rung1_predict
#SBATCH --partition=normal
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --time=02:00:00
#SBATCH --output=/home/user/nurkyz/einstein_cnn/slurm_rung1_predict_%j.out

# Step 3 of docs/RUNG1_PLAN.md: score the UNLABELED set with 8-view TTA,
# ensemble across the seed checkpoints, write the submission CSV.
#
# Required:  TEST_H5   unlabeled Rung 1 file
#            CKPTS     space-separated checkpoint list (quote it)
# Optional:  OUT (default under roman_dc), PROB_COL (default 'prob' -- set to
#            the name the notebook requires), HARD=1 to write 0/1 not prob.
#
#   TEST_H5=~/cosmos_acs/roman_dc/rung_1_unlabeled.h5 \
#   CKPTS="rung1_resnet50_s0.pt rung1_resnet50_s1.pt rung1_resnet50_s2.pt" \
#   sbatch pipeline/rung1_predict.sbatch
set -e
: "${TEST_H5:?set TEST_H5=/path/to/unlabeled.h5}"
: "${CKPTS:?set CKPTS=\"ckpt1.pt ckpt2.pt ...\"}"
OUT="${OUT:-/home/user/nurkyz/cosmos_acs/roman_dc/submission_rung1.csv}"
PROB_COL="${PROB_COL:-prob}"
PY=/home/user/nurkyz/miniconda3/envs/Stronglensing/bin/python
cd /home/user/nurkyz/einstein_cnn

HARD_FLAG=""; [ -n "${HARD:-}" ] && HARD_FLAG="--hard_label"

# CKPTS is intentionally unquoted so the space-separated list expands to args
$PY predict_rung1.py --test_file "$TEST_H5" --ckpt $CKPTS \
    --out "$OUT" --prob_col "$PROB_COL" $HARD_FLAG
echo "RUNG1_PREDICT_DONE $OUT"
