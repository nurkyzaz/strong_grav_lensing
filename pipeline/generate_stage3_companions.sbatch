#!/bin/bash
#SBATCH --job-name=lf_gen3
#SBATCH --partition=normal
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=2
#SBATCH --mem=8G
#SBATCH --time=08:00:00
#SBATCH --output=/home/user/nurkyz/paltas_shards3/slurm_%A_%a.out

# Stage-3 v3 dataset: v2 recipe (theta_E U[0.45,2.3], 88 real ePSFs, joint lens
# light) + REAL COMPANION INJECTION (source_stamps_clean.h5) to close the
# busy-field gap (Nurkyz 2026-07-07). Sub-shard S = 4*I + j; S 0-79 train
# (1250 ea -> 100k), 80-87 val (625 ea -> 5k, kernel-disjoint).
set -e
PY=/home/user/nurkyz/miniconda3/envs/Stronglensing/bin/python
TILES=/home/user/nurkyz/cosmos_acs/tiles
SHARDS=/home/user/nurkyz/paltas_shards3
mkdir -p "$SHARDS"
cd "$TILES"

OFFSET=${OFFSET:-0}
I=$((OFFSET + SLURM_ARRAY_TASK_ID))

for j in 0 1 2 3; do
    S=$((4 * I + j))
    if [ "$I" -lt 20 ]; then N=1250; else N=625; fi
    GENSEED=$((501 + S))
    COMBSEED=$((901 + S))
    KERNEL=$(printf 'psf_bank_v2/kernel_%02d_extended.npy' "$S")
    OUT="$SHARDS/sub_$(printf '%02d' "$S")"
    H5="$SHARDS/hybrid_shard_$(printf '%02d' "$S").h5"
    echo "sub-shard $S (task $I, j=$j): n=$N genseed=$GENSEED kernel=$KERNEL"
    export LF_PSF_KERNEL="$KERNEL"
    $PY run_paltas_pilot.py config_lensfusion_acs_nonoise.py "$OUT" --n "$N" --seed "$GENSEED"
    $PY hybrid_combine.py --run "$OUT" --empty empty_cutouts_4k.h5 \
        --real /home/user/nurkyz/einstein_cnn/real_slacs_images.h5 \
        --out "$H5" --seed "$COMBSEED" \
        --companion_stamps source_stamps_clean.h5 \
        --companion_rate_lo 8 --companion_rate_hi 26 --companion_flux_pct 35
    rm -f "$OUT"/image_*.npy
done
echo "SHARD_DONE $I"
