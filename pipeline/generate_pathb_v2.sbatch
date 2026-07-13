#!/bin/bash
#SBATCH --job-name=lf_genpathb2
#SBATCH --partition=normal
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=2
#SBATCH --mem=8G
#SBATCH --time=08:00:00
#SBATCH --output=/home/user/nurkyz/paltas_shards_pathb_v2/slurm_%A_%a.out

# PATH B v2 full dataset (2026-07-09, after P1b/P2/P3/P4 pilots v4b-v7):
# arc-only paltas + REAL LRG deflector light (256px library v6, APERTURE-mag
# scaled, dihedral-augmented) + companions + real backdrop + noise calibrated
# to the benchmark-DISJOINT DA pool. Sub-shard S=4*I+j; S 0-79 train (1250 ea
# -> 100k, stamps = 41-stamp TRAIN split), S 80-87 val (625 ea -> 5k,
# kernel-disjoint AND stamp-disjoint: 8-stamp VAL split).
# Seeds 2701+/3101+ (disjoint from v1/v2/v3 hybrid AND the deleted flawed
# pathb shards' 701/1101 era).
set -e
PY=/home/user/nurkyz/miniconda3/envs/Stronglensing/bin/python
TILES=/home/user/nurkyz/cosmos_acs/tiles
SHARDS=/home/user/nurkyz/paltas_shards_pathb_v2
mkdir -p "$SHARDS"
cd "$TILES"

OFFSET=${OFFSET:-0}
I=$((OFFSET + SLURM_ARRAY_TASK_ID))
for j in 0 1 2 3; do
    S=$((4 * I + j))
    if [ "$I" -lt 20 ]; then N=1250; else N=625; fi
    if [ "$S" -lt 80 ]; then STAMPS=deflector_stamps_lrg_v6_train.h5; else STAMPS=deflector_stamps_lrg_v6_val.h5; fi
    GENSEED=$((2701 + S))
    COMBSEED=$((3101 + S))
    KERNEL=$(printf 'psf_bank_v2/kernel_%02d_extended.npy' "$S")
    OUT="$SHARDS/sub_$(printf '%02d' "$S")"
    H5="$SHARDS/hybrid_shard_$(printf '%02d' "$S").h5"
    echo "sub-shard $S: n=$N genseed=$GENSEED kernel=$KERNEL stamps=$STAMPS"
    export LF_PSF_KERNEL="$KERNEL"
    $PY run_paltas_pilot.py config_lensfusion_acs_pathb_nonoise.py "$OUT" --n "$N" --seed "$GENSEED"
    $PY hybrid_combine.py --run "$OUT" --empty empty_cutouts_4k.h5 \
        --real /home/user/nurkyz/einstein_cnn/real_dapool_images.h5 \
        --out "$H5" --seed "$COMBSEED" \
        --deflector_stamps "$STAMPS" --deflector_augment \
        --deflector_mag_csv lens_light_empirical.csv \
        --companion_stamps source_stamps_clean.h5 \
        --companion_rate_lo 8 --companion_rate_hi 26 --companion_flux_pct 35
    rm -f "$OUT"/image_*.npy
done
echo "SHARD_DONE $I"
