#!/bin/bash
#SBATCH --job-name=lf_stage2
#SBATCH --partition=normal
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=2
#SBATCH --mem=8G
#SBATCH --time=08:00:00
#SBATCH --output=/home/user/nurkyz/paltas_shards/slurm_%A_%a.out

# Stage-2 training-set generation (CLAUDE.md plan 2026-07-06).
# Shards 0-19: train, 5k images each -> 100k total.
# Shards 20-21: sim-val, 2.5k each -> 5k, DISJOINT seeds AND kernels.
# Per shard: one real focus-diverse ePSF kernel (psf_bank), noiseless paltas
# render -> hybrid combine (real empty cutout + calibrated topup noise) ->
# preview first 16 -> delete intermediate npy (quota).
#
# NOTE (2026-07-06): this cluster's MaxArraySize=10, so the 22 shards are
# submitted as three array chunks (see submit_stage2.sh), each passing an
# OFFSET so SLURM_ARRAY_TASK_ID (0-9 or 0-1) maps to the real shard id 0-21.
# Every partition here (normal/a/b/c) requires --gres=gpu:N even for CPU-only
# work (paltas generation does not use the GPU) -- SLURM policy, not a choice;
# flagged to Nurkyz, minimal gres:1 requested.

set -e
PY=/home/user/nurkyz/miniconda3/envs/Stronglensing/bin/python
TILES=/home/user/nurkyz/cosmos_acs/tiles
SHARDS=/home/user/nurkyz/paltas_shards
mkdir -p "$SHARDS"
cd "$TILES"

OFFSET=${OFFSET:-0}
I=$((OFFSET + SLURM_ARRAY_TASK_ID))
if [ "$I" -lt 20 ]; then
    N=5000; GENSEED=$((101 + I)); COMBSEED=$((501 + I)); KID=$I
else
    N=2500; GENSEED=$((901 + I - 20)); COMBSEED=$((951 + I - 20)); KID=$I  # kernels 20,21 val-only
fi
KERNEL=$(printf 'psf_bank/kernel_%02d_extended.npy' "$KID")
OUT="$SHARDS/shard_$(printf '%02d' "$I")"
H5="$SHARDS/hybrid_shard_$(printf '%02d' "$I").h5"

echo "shard $I (offset=$OFFSET array_id=$SLURM_ARRAY_TASK_ID): n=$N genseed=$GENSEED combseed=$COMBSEED kernel=$KERNEL"
export LF_PSF_KERNEL="$KERNEL"

$PY run_paltas_pilot.py config_lensfusion_acs_nonoise.py "$OUT" --n "$N" --seed "$GENSEED"
$PY preview_three_stretch.py "$OUT" --n 16
$PY hybrid_combine.py --run "$OUT" --empty empty_cutouts.h5 \
    --real /home/user/nurkyz/einstein_cnn/real_slacs_images.h5 \
    --out "$H5" --seed "$COMBSEED"
# keep metadata.csv + previews + config copy; drop the raw npy (quota)
rm -f "$OUT"/image_*.npy
echo "SHARD_DONE $I"
