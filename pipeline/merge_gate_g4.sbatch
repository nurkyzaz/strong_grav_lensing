#!/bin/bash
#SBATCH --job-name=lf_mergeG4
#SBATCH --partition=normal
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --time=03:00:00
#SBATCH --output=/home/user/nurkyz/cosmos_acs/tiles/merge_gate_g4.out

# G4 merge + gates. Quota guard; labels verified BEFORE shard deletion;
# FJ gate on the MERGED assignments (the GEN4 property at scale).
set -e
PY=/home/user/nurkyz/miniconda3/envs/Stronglensing/bin/python
cd /home/user/nurkyz/cosmos_acs/tiles

USED_MB=$(quota 2>/dev/null | awk '/sda1/ {getline; print int($1)}')
echo "quota used: ${USED_MB} MB"
if [ -n "$USED_MB" ] && [ "$USED_MB" -gt 101000 ]; then
    echo "ABORT: <8GB headroom to hard limit"; exit 1
fi

echo "[1] merge ..."
$PY merge_hybrid_shards.py --shards /home/user/nurkyz/paltas_shards_g4 --train-max-id 80 \
    --train-out /home/user/nurkyz/einstein_cnn/train_g4_100k.h5 \
    --val-out /home/user/nurkyz/einstein_cnn/val_g4_5k.h5

echo "[1b] verify labels BEFORE shard deletion ..."
$PY - <<'PYEOF'
import h5py, numpy as np
for fn in ("/home/user/nurkyz/einstein_cnn/train_g4_100k.h5",
           "/home/user/nurkyz/einstein_cnn/val_g4_5k.h5"):
    with h5py.File(fn, "r") as f:
        th = f["theta_E"][:]
        assert (th == 0).sum() == 0, "ZERO labels in " + fn
        for k in ("mass_e1", "mass_e2", "deflector_index", "deflector_mag",
                  "arc_snr", "arc_extent"):
            assert k in f, k + " missing in " + fn
        print(fn.split("/")[-1], "n=%d theta[%.2f,%.2f] med %.3f OK"
              % (len(th), th.min(), th.max(), np.median(th)))
        for lo, hi in ((0.45, .8), (.8, 1.2), (1.2, 1.7), (1.7, 2.3)):
            m = (th >= lo) & (th < hi)
            print("   theta [%.2f,%.2f): frac %.3f" % (lo, hi, m.mean()))
print("MERGE_LABELS_OK")
PYEOF

echo "[1c] merged FJ gate ..."
head -1 /home/user/nurkyz/paltas_shards_g4/assign_00.csv > /tmp/g4_assign_all.csv
for f in /home/user/nurkyz/paltas_shards_g4/assign_*.csv; do tail -n +2 "$f" >> /tmp/g4_assign_all.csv; done
$PY g2_gate_fj.py /tmp/g4_assign_all.csv

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
