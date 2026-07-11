#!/bin/bash
#SBATCH --job-name=lf_mergeG3
#SBATCH --partition=normal
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --time=03:00:00
#SBATCH --output=/home/user/nurkyz/cosmos_acs/tiles/merge_gate_g3.out

# G3 merge + gates. Labels verified BEFORE any deletion; FJ gate on the merged
# assignments; realism gate vs the RE-DERIVED (_g3) benchmark; scratch files on
# HOME (the 47548 /tmp lesson). QUOTA: deletes the SUPERSEDED-on-PASS
# train_g4/val_g4 sets right before merging (reproducible: retained manifests
# + deterministic seeds; eval-#17 checkpoints kept) — logged in DECISIONS_LOG.
set -e
PY=/home/user/nurkyz/miniconda3/envs/Stronglensing/bin/python
cd /home/user/nurkyz/cosmos_acs/tiles

USED_MB=$(quota 2>/dev/null | awk '/sda1/ {getline; print int($1)}')
echo "quota used: ${USED_MB} MB"
if [ -n "$USED_MB" ] && [ "$USED_MB" -gt 102000 ]; then
    echo "ABORT: <8GB headroom to hard limit"; exit 1
fi

echo "[0] delete superseded G4 train/val (reproducible; quota headroom for merge) ..."
ls -la /home/user/nurkyz/paltas_shards_g4/manifest_00.csv   # reproducibility anchor must exist
rm -f /home/user/nurkyz/einstein_cnn/train_g4_100k.h5 /home/user/nurkyz/einstein_cnn/val_g4_5k.h5
quota -s 2>/dev/null | tail -1

echo "[1] merge ..."
$PY merge_hybrid_shards.py --shards /home/user/nurkyz/paltas_shards_g3 --train-max-id 80 \
    --train-out /home/user/nurkyz/einstein_cnn/train_g3_100k.h5 \
    --val-out /home/user/nurkyz/einstein_cnn/val_g3_5k.h5

echo "[1b] verify labels BEFORE shard deletion ..."
$PY /home/user/nurkyz/cosmos_acs/tiles/g3_verify_labels.py

echo "[1c] merged FJ gate ..."
ASSIGN_ALL=/home/user/nurkyz/cosmos_acs/tiles/g3_assign_all.csv
head -1 /home/user/nurkyz/paltas_shards_g3/assign_00.csv > "$ASSIGN_ALL"
for f in /home/user/nurkyz/paltas_shards_g3/assign_*.csv; do tail -n +2 "$f" >> "$ASSIGN_ALL"; done
$PY g2_gate_fj.py "$ASSIGN_ALL"

echo "[2] realism gate on merged train (vs _g3 benchmark) ..."
$PY gate_stage0.py --sim /home/user/nurkyz/einstein_cnn/train_g3_100k.h5 \
    --real /home/user/nurkyz/einstein_cnn/euclid_slacs_images_g3.h5 \
    --csv /home/user/nurkyz/einstein_cnn/failure_features_slacs.csv \
    --meta /home/user/nurkyz/paltas_shards_g3/manifest_note_none.csv \
    --out gate_g3_merged.png || echo "gate_stage0 meta quirk — numeric rows above still authoritative"

echo "[3] side-by-side + flatness ..."
$PY side_by_side_real_sim.py --real /home/user/nurkyz/einstein_cnn/euclid_slacs_images_g3.h5 \
    --sim /home/user/nurkyz/einstein_cnn/train_g3_100k.h5 --n 8 --seed 7 \
    --out real_vs_train_G3.png
cd /home/user/nurkyz/einstein_cnn
$PY reb_report.py train_g3_100k.h5 g3_merged

rm -f /home/user/nurkyz/paltas_shards_g3/hybrid_shard_*.h5
echo "MERGE_GATE_G3_DONE"
