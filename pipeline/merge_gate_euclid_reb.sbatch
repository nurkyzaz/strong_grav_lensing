#!/bin/bash
#SBATCH --job-name=lf_mergeREB
#SBATCH --partition=normal
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --time=03:00:00
#SBATCH --output=/home/user/nurkyz/cosmos_acs/tiles/merge_gate_euclid_reb.out

# REB merge + gate (plan 2b). Quota guard first: needs ~8 GB headroom for the
# merged files while shards still exist (shards deleted after a verified merge).
set -e
PY=/home/user/nurkyz/miniconda3/envs/Stronglensing/bin/python
cd /home/user/nurkyz/cosmos_acs/tiles

USED_MB=$(quota 2>/dev/null | awk '/sda1/ {getline; print int($1)}')
if [ -z "$USED_MB" ]; then USED_MB=$(quota -s 2>/dev/null | awk '/sda1/ {getline; gsub("M","",$1); print int($1)}'); fi
echo "quota used: ${USED_MB} MB"
if [ -n "$USED_MB" ] && [ "$USED_MB" -gt 101000 ]; then
    echo "ABORT: less than ~8 GB headroom to the 110 GB hard limit — free space first"
    exit 1
fi

echo "[1] merge shards ..."
$PY merge_hybrid_shards.py --shards /home/user/nurkyz/paltas_shards_euclid_reb --train-max-id 80 \
    --train-out /home/user/nurkyz/einstein_cnn/train_euclid_reb_100k.h5 \
    --val-out /home/user/nurkyz/einstein_cnn/val_euclid_reb_5k.h5

echo "[1b] verify labels BEFORE shard deletion ..."
$PY - <<'PYEOF'
import h5py, numpy as np
for fn in ("/home/user/nurkyz/einstein_cnn/train_euclid_reb_100k.h5",
           "/home/user/nurkyz/einstein_cnn/val_euclid_reb_5k.h5"):
    with h5py.File(fn, "r") as f:
        th = f["theta_E"][:]
        assert (th == 0).sum() == 0, "ZERO labels in " + fn
        for k in ("mass_e1", "mass_e2", "deflector_index", "deflector_mag",
                  "arc_snr", "arc_extent"):
            assert k in f, k + " missing in " + fn
        print(fn.split("/")[-1], "n=%d theta[%.2f,%.2f] med %.3f  keys OK"
              % (len(th), th.min(), th.max(), np.median(th)))
        for lo, hi in ((0.45, .8), (.8, 1.2), (1.2, 1.7), (1.7, 2.3)):
            m = (th >= lo) & (th < hi)
            print("   theta [%.2f,%.2f): frac %.3f" % (lo, hi, m.mean()))
print("MERGE_LABELS_OK")
PYEOF

echo "[1c] deflector_re aux label ..."
$PY add_deflector_re.py /home/user/nurkyz/einstein_cnn/train_euclid_reb_100k.h5
$PY add_deflector_re.py /home/user/nurkyz/einstein_cnn/val_euclid_reb_5k.h5

echo "[2] merge train metadata ..."
$PY merge_shard_metadata.py --shards /home/user/nurkyz/paltas_shards_euclid_reb --train-max-id 80 \
    --out /home/user/nurkyz/paltas_shards_euclid_reb/metadata_train_merged.csv

echo "[3] realism gate on the FULL merged train set ..."
$PY gate_stage0.py --sim /home/user/nurkyz/einstein_cnn/train_euclid_reb_100k.h5 \
    --real /home/user/nurkyz/einstein_cnn/euclid_slacs_images.h5 \
    --csv failure_features_slacs.csv \
    --meta /home/user/nurkyz/paltas_shards_euclid_reb/metadata_train_merged.csv \
    --out gate_stage0_report_euclid_reb.png

echo "[4] side-by-side on merged ..."
$PY side_by_side_real_sim.py --real /home/user/nurkyz/einstein_cnn/euclid_slacs_images.h5 \
    --sim /home/user/nurkyz/einstein_cnn/train_euclid_reb_100k.h5 --n 8 --seed 7 \
    --out real_vs_train_euclid_reb.png

echo "[5] radial profile on merged ..."
$PY radial_profile_compare.py --sim /home/user/nurkyz/einstein_cnn/train_euclid_reb_100k.h5 \
    --lib deflector_stamps_lrg_v6_train.h5 --label "TRAIN euclid-REB" \
    --out /home/user/nurkyz/cosmos_acs/tiles/radial_profile_train_euclid_reb.png

rm -f /home/user/nurkyz/paltas_shards_euclid_reb/hybrid_shard_*.h5
echo "MERGE_GATE_EUCLID_REB_DONE"
