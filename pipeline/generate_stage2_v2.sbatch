#!/bin/bash
#SBATCH --job-name=lf_stage2v2
#SBATCH --partition=normal
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=2
#SBATCH --mem=8G
#SBATCH --time=08:00:00
#SBATCH --output=/home/user/nurkyz/paltas_shards2/slurm_%A_%a.out

# Stage-2 v2 regeneration (audit fixes, 2026-07-06):
#   - theta_E prior widened to U[0.45, 2.30] (benchmark coverage fix)
#   - PSF diversity 22 -> 88 kernels: each of the 22 tasks runs FOUR sub-runs,
#     each with its own real focus-diverse ePSF kernel (psf_bank_v2).
#     Sub-shard id S = 4*I + j: S 0-79 train (1250 imgs each -> 100k),
#     S 80-87 val (625 imgs each -> 5k; kernels 80-87 are val-only).
#   - backdrops: empty_cutouts_4k.h5 (4000 cutouts, ~3x less reuse)
# Cluster policies honored: --gres required on all partitions; QOS caps 8
# concurrent jobs -> submit via submit_stage2_v2.sh waves.

set -e
PY=/home/user/nurkyz/miniconda3/envs/Stronglensing/bin/python
TILES=/home/user/nurkyz/cosmos_acs/tiles
SHARDS=/home/user/nurkyz/paltas_shards2
mkdir -p "$SHARDS"
cd "$TILES"

OFFSET=${OFFSET:-0}
I=$((OFFSET + SLURM_ARRAY_TASK_ID))

for j in 0 1 2 3; do
    S=$((4 * I + j))
    if [ "$I" -lt 20 ]; then N=1250; else N=625; fi
    GENSEED=$((201 + S))
    COMBSEED=$((601 + S))
    KERNEL=$(printf 'psf_bank_v2/kernel_%02d_extended.npy' "$S")
    OUT="$SHARDS/sub_$(printf '%02d' "$S")"
    H5="$SHARDS/hybrid_shard_$(printf '%02d' "$S").h5"
    echo "sub-shard $S (task $I, j=$j): n=$N genseed=$GENSEED kernel=$KERNEL"
    export LF_PSF_KERNEL="$KERNEL"
    $PY run_paltas_pilot.py config_lensfusion_acs_nonoise.py "$OUT" --n "$N" --seed "$GENSEED"
    $PY preview_three_stretch.py "$OUT" --n 16
    $PY hybrid_combine.py --run "$OUT" --empty empty_cutouts_4k.h5 \
        --real /home/user/nurkyz/einstein_cnn/real_slacs_images.h5 \
        --out "$H5" --seed "$COMBSEED"
    rm -f "$OUT"/image_*.npy
done
echo "SHARD_DONE $I"
