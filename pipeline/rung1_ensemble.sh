#!/bin/bash
# rung1_ensemble.sh -- one-command Rung 1 ensemble driver.
#
# Submits N seed training jobs (rung1_train.sbatch), then a single predict job
# (rung1_predict.sbatch) gated on afterok of ALL of them, so the submission CSV
# is written only if every training run succeeded. Nothing runs on the login
# node -- this just queues the SLURM chain and returns.
#
# Required env:
#   TRAIN_H5   labeled Rung 1 file
#   TEST_H5    unlabeled Rung 1 file
# Optional env:
#   ARCH       resnet50 | convnextv2      (default resnet50)
#   SEEDS      space-separated            (default "0 1 2")
#   EPOCHS                                (default 40)
#   DATA_DIR   ckpt + submission location (default ~/cosmos_acs/roman_dc)
#   PROB_COL   submission column name     (default prob; set from the notebook)
#   IMAGE_KEY / LABEL_KEY / ID_KEY / HARD  (optional; see rung1_*.sbatch)
#
# Usage:
#   TRAIN_H5=~/cosmos_acs/roman_dc/roman_data_challenge_rung_1_v_3_0.h5 \
#   TEST_H5=~/cosmos_acs/roman_dc/rung_1_unlabeled.h5 \
#       bash pipeline/rung1_ensemble.sh
set -euo pipefail

: "${TRAIN_H5:?set TRAIN_H5=/path/to/labeled.h5}"
: "${TEST_H5:?set TEST_H5=/path/to/unlabeled.h5}"
ARCH="${ARCH:-resnet50}"
SEEDS="${SEEDS:-0 1 2}"
EPOCHS="${EPOCHS:-40}"
DATA_DIR="${DATA_DIR:-$HOME/cosmos_acs/roman_dc}"
PROB_COL="${PROB_COL:-prob}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# these are identical across jobs -> export so SLURM's default --export=ALL
# propagates them; per-job vars (ARCH/SEED/CKPT/CKPTS) are set inline below.
export TRAIN_H5 TEST_H5
[ -n "${IMAGE_KEY:-}" ] && export IMAGE_KEY
[ -n "${LABEL_KEY:-}" ] && export LABEL_KEY
[ -n "${ID_KEY:-}" ]    && export ID_KEY
[ -n "${HARD:-}" ]      && export HARD

train_jids=()
ckpts=()
for s in $SEEDS; do
    ckpt="$DATA_DIR/rung1_${ARCH}_s${s}.pt"
    jid=$(ARCH="$ARCH" SEED="$s" EPOCHS="$EPOCHS" CKPT="$ckpt" \
          sbatch --parsable "$SCRIPT_DIR/rung1_train.sbatch")
    jid="${jid%%;*}"   # --parsable may append ';cluster' on multi-cluster setups
    echo "train  seed=$s arch=$ARCH -> job $jid  ($ckpt)"
    train_jids+=("$jid")
    ckpts+=("$ckpt")
done

dep=$(IFS=:; echo "${train_jids[*]}")   # afterok:JID1:JID2:JID3
out="$DATA_DIR/submission_rung1_${ARCH}.csv"
pred_jid=$(CKPTS="${ckpts[*]}" PROB_COL="$PROB_COL" OUT="$out" \
           sbatch --parsable --dependency=afterok:"$dep" \
           "$SCRIPT_DIR/rung1_predict.sbatch")
pred_jid="${pred_jid%%;*}"
echo "predict            -> job $pred_jid  (afterok:$dep)"
echo
echo "queued ${#train_jids[@]} train + 1 predict"
echo "  watch:  squeue -u \$USER"
echo "  result: $out"
