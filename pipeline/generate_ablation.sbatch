#!/bin/bash
#SBATCH --job-name=lf_ablgen
#SBATCH --partition=normal
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=2
#SBATCH --mem=8G
#SBATCH --time=08:00:00
#SBATCH --output=/home/user/nurkyz/paltas_abl/slurm_%A_%a.out

# Parameterized ablation generation (MASTER_PLAN D1, 2026-07-06).
# Env (via --export): CONFIG (paltas config), SHARDS (output dir),
#   KERNEL_DIR (bank dir; default psf_bank_v2), KERNEL_FIXED (optional single
#   kernel for ALL shards, e.g. Gaussian ablation), COMBINE_FLAGS (optional,
#   e.g. --no-backdrop), SEEDBASE (default 301), OFFSET (wave offset).
# Same sub-shard layout as v2: S = 4*I + j, S 0-79 train (1250 ea), 80-87 val
# (625 ea). Cluster policies: --gres mandatory; QOS caps 8 jobs -> waves.

set -e
PY=/home/user/nurkyz/miniconda3/envs/Stronglensing/bin/python
TILES=/home/user/nurkyz/cosmos_acs/tiles
: "${CONFIG:?}" "${SHARDS:?}"
KERNEL_DIR=${KERNEL_DIR:-psf_bank_v2}
SEEDBASE=${SEEDBASE:-301}
OFFSET=${OFFSET:-0}
mkdir -p "$SHARDS"
cd "$TILES"

I=$((OFFSET + SLURM_ARRAY_TASK_ID))
for j in 0 1 2 3; do
    S=$((4 * I + j))
    if [ "$I" -lt 20 ]; then N=1250; else N=625; fi
    GENSEED=$((SEEDBASE + S))
    COMBSEED=$((SEEDBASE + 400 + S))
    if [ -n "$KERNEL_FIXED" ]; then
        KERNEL="$KERNEL_FIXED"
    else
        KERNEL=$(printf '%s/kernel_%02d_extended.npy' "$KERNEL_DIR" "$S")
    fi
    OUT="$SHARDS/sub_$(printf '%02d' "$S")"
    H5="$SHARDS/hybrid_shard_$(printf '%02d' "$S").h5"
    echo "sub-shard $S: n=$N genseed=$GENSEED kernel=$KERNEL flags='$COMBINE_FLAGS'"
    export LF_PSF_KERNEL="$KERNEL"
    $PY run_paltas_pilot.py "$CONFIG" "$OUT" --n "$N" --seed "$GENSEED"
    $PY hybrid_combine.py --run "$OUT" --empty empty_cutouts_4k.h5 \
        --real /home/user/nurkyz/einstein_cnn/real_slacs_images.h5 \
        --out "$H5" --seed "$COMBSEED" $COMBINE_FLAGS
    rm -f "$OUT"/image_*.npy
done
echo "SHARD_DONE $I"
