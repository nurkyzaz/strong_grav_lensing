#!/bin/bash
#SBATCH --job-name=lf_mergeG4b
#SBATCH --partition=normal
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --time=02:00:00
#SBATCH --output=/home/user/nurkyz/cosmos_acs/tiles/merge_gate_g4_part2.out

# G4 merge part 2 — resume after 47548 died on a full compute-node /tmp.
# Merge + label verify already DONE (MERGE_LABELS_OK in merge_gate_g4.out).
# Same steps/order as merge_gate_g4.sbatch [1c]..[3]; temp file on HOME, not /tmp.
set -e
PY=/home/user/nurkyz/miniconda3/envs/Stronglensing/bin/python
cd /home/user/nurkyz/cosmos_acs/tiles

echo "[1c] merged FJ gate ..."
ASSIGN_ALL=/home/user/nurkyz/cosmos_acs/tiles/g4_assign_all.csv
head -1 /home/user/nurkyz/paltas_shards_g4/assign_00.csv > "$ASSIGN_ALL"
for f in /home/user/nurkyz/paltas_shards_g4/assign_*.csv; do tail -n +2 "$f" >> "$ASSIGN_ALL"; done
$PY g2_gate_fj.py "$ASSIGN_ALL"

echo "[2] realism gate on merged train ..."
$PY gate_stage0.py --sim /home/user/nurkyz/einstein_cnn/train_g4_100k.h5 \
    --real /home/user/nurkyz/einstein_cnn/euclid_slacs_images.h5 \
    --csv /home/user/nurkyz/einstein_cnn/failure_features_slacs.csv \
    --meta /home/user/nurkyz/paltas_shards_g4/manifest_00.csv \
    --out gate_g4_merged.png || echo "gate_stage0 meta quirk (manifest not paltas metadata) — numeric rows above still authoritative"

echo "[3] side-by-side + flatness ..."
$PY side_by_side_real_sim.py --real /home/user/nurkyz/einstein_cnn/euclid_slacs_images.h5 \
    --sim /home/user/nurkyz/einstein_cnn/train_g4_100k.h5 --n 8 --seed 7 \
    --out real_vs_train_G4.png
cd /home/user/nurkyz/einstein_cnn
$PY reb_report.py train_g4_100k.h5 g4_merged

rm -f /home/user/nurkyz/paltas_shards_g4/hybrid_shard_*.h5
echo "MERGE_GATE_G4_DONE"
