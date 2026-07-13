#!/bin/bash
#SBATCH --job-name=lf_merge3
#SBATCH --partition=normal
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --time=03:00:00
#SBATCH --output=/home/user/nurkyz/cosmos_acs/tiles/merge_gate_v3.out

set -e
PY=/home/user/nurkyz/miniconda3/envs/Stronglensing/bin/python
cd /home/user/nurkyz/cosmos_acs/tiles

echo "[1] merge shards ..."
$PY merge_hybrid_shards.py --shards /home/user/nurkyz/paltas_shards3 --train-max-id 80 \
    --train-out /home/user/nurkyz/einstein_cnn/train_hybrid_100k_v3.h5 \
    --val-out /home/user/nurkyz/einstein_cnn/val_hybrid_5k_v3.h5

echo "[2] merge train metadata ..."
$PY - <<'PYEOF'
import glob, os, pandas as pd
fr = []
for p in sorted(glob.glob(os.path.expanduser("~/paltas_shards3/sub_*/metadata.csv"))):
    if int(os.path.basename(os.path.dirname(p)).split("_")[-1]) < 80:
        fr.append(pd.read_csv(p))
pd.concat(fr, ignore_index=True).to_csv(
    os.path.expanduser("~/paltas_shards3/metadata_train_merged.csv"), index=False)
print("metadata rows:", sum(len(f) for f in fr))
PYEOF

echo "[3] realism gate ..."
$PY gate_stage0.py --sim /home/user/nurkyz/einstein_cnn/train_hybrid_100k_v3.h5 \
    --real /home/user/nurkyz/einstein_cnn/real_slacs_images.h5 \
    --csv failure_features_slacs.csv \
    --meta /home/user/nurkyz/paltas_shards3/metadata_train_merged.csv \
    --out gate_stage0_report_v3.png

echo "[4] companion-count verification ..."
SMOKE_H5=/home/user/nurkyz/einstein_cnn/train_hybrid_100k_v3.h5 $PY characterize_field2.py

# drop per-shard duplicates now inside the merged files (quota)
rm -f /home/user/nurkyz/paltas_shards3/hybrid_shard_*.h5
echo "MERGE_GATE_V3_DONE"
