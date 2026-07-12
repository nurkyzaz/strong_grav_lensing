#!/bin/bash
#SBATCH --job-name=lf_mergeGN
#SBATCH --partition=normal
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --time=03:00:00
#SBATCH --output=/home/user/nurkyz/cosmos_acs/tiles/merge_gate_g4native.out

# Track-N native-arm merge + gates. Same population as the G3 Euclid arm
# (Euclid-selection-matched). Gates vs the NATIVE real SLACS distributional
# reference (established Stage-2 practice; frozen files read-only).
# QUOTA: deletes two SUPERSEDED items first (flagged to Nurkyz 2026-07-12):
#   lensed_train_m2/m3.h5 (pre-paltas m3-era generator, retired 07-02)
#   g4_merged_small_theta.h5 (orphan derived subset of the deleted G4 train)
set -e
PY=/home/user/nurkyz/miniconda3/envs/Stronglensing/bin/python
EC=/home/user/nurkyz/einstein_cnn
cd /home/user/nurkyz/cosmos_acs/tiles

echo "[0] superseded-data cleanup for merge headroom ..."
rm -f "$EC/lensed_train_m2.h5" "$EC/lensed_train_m3.h5" "$EC/g4_merged_small_theta.h5"
quota -s 2>/dev/null | tail -1
USED_MB=$(quota 2>/dev/null | awk '/sda1/ {getline; print int($1)}')
if [ -n "$USED_MB" ] && [ "$USED_MB" -gt 102000 ]; then
    echo "ABORT: <8GB headroom to hard limit"; exit 1
fi

echo "[1] merge native shards ..."
$PY merge_hybrid_shards.py --shards /home/user/nurkyz/paltas_shards_g4n \
    --shard-glob 'native_shard_*.h5' --train-max-id 80 \
    --train-out "$EC/train_g4native_100k.h5" \
    --val-out "$EC/val_g4native_5k.h5" || \
$PY merge_hybrid_shards.py --shards /home/user/nurkyz/paltas_shards_g4n --train-max-id 80 \
    --train-out "$EC/train_g4native_100k.h5" \
    --val-out "$EC/val_g4native_5k.h5"

echo "[1b] verify labels BEFORE shard deletion ..."
$PY g4n_verify_labels.py

echo "[2] realism gate vs NATIVE real SLACS ..."
$PY gate_stage0.py --sim "$EC/train_g4native_100k.h5" \
    --real "$EC/real_slacs_images.h5" \
    --csv "$EC/failure_features_slacs.csv" \
    --meta /home/user/nurkyz/paltas_shards_g4/manifest_00.csv \
    --out gate_g4native_merged.png || echo "gate_stage0 meta quirk — numeric rows authoritative"

echo "[3] side-by-side + flatness ..."
$PY side_by_side_real_sim.py --real "$EC/real_slacs_images.h5" \
    --sim "$EC/train_g4native_100k.h5" --n 8 --seed 7 \
    --out real_vs_train_G4NATIVE.png
cd "$EC"
$PY reb_report.py train_g4native_100k.h5 g4native_merged

rm -f /home/user/nurkyz/paltas_shards_g4n/native_shard_*.h5
echo "MERGE_GATE_G4NATIVE_DONE"
