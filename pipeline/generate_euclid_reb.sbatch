#!/bin/bash
#SBATCH --job-name=lf_genREB
#SBATCH --partition=normal
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=2
#SBATCH --mem=8G
#SBATCH --time=08:00:00
#SBATCH --output=/home/user/nurkyz/paltas_shards_euclid_reb/slurm_%A_%a.out

# EUCLID-ARM REBALANCED dataset (plan 2b, pilot 47451 PASS + Nurkyz visual OK):
# production recipe + theta_E prior oc 1/pass (post-selection ~flat) + aux
# labels (mass_e1/e2) + provenance carried. Pass ~51% -> N=2450 train
# (~1250 selected each), 1250 val (~640 each). Seeds 8701+/9101+/9601+
# (disjoint from all prior generations: max prior base 7101+87).
set -e
PY=/home/user/nurkyz/miniconda3/envs/Stronglensing/bin/python
TILES=/home/user/nurkyz/cosmos_acs/tiles
EC=/home/user/nurkyz/einstein_cnn
SHARDS=/home/user/nurkyz/paltas_shards_euclid_reb
mkdir -p "$SHARDS"
cd "$TILES"

OFFSET=${OFFSET:-0}
I=$((OFFSET + SLURM_ARRAY_TASK_ID))
for j in 0 1 2 3; do
    S=$((4 * I + j))
    if [ "$I" -lt 20 ]; then N=2450; else N=1250; fi
    if [ "$S" -lt 80 ]; then STAMPS=deflector_stamps_lrg_v6_train.h5; else STAMPS=deflector_stamps_lrg_v6_val.h5; fi
    GENSEED=$((8701 + S))
    COMBSEED=$((9101 + S))
    KERNEL=$(printf 'psf_bank_v2/kernel_%02d_extended.npy' "$S")
    OUT="$SHARDS/sub_$(printf '%02d' "$S")"
    ARCE="$SHARDS/arcs_euclid_$(printf '%02d' "$S")"
    NATIVE="$SHARDS/native_$(printf '%02d' "$S").h5"
    EUC="$SHARDS/euclid_$(printf '%02d' "$S").h5"
    SEL="$SHARDS/hybrid_shard_$(printf '%02d' "$S").h5"
    echo "sub-shard $S: n=$N genseed=$GENSEED kernel=$KERNEL stamps=$STAMPS"
    export LF_PSF_KERNEL="$KERNEL"
    $PY run_paltas_pilot.py config_lensfusion_acs_pathb_euclid.py "$OUT" --n "$N" --seed "$GENSEED"
    $PY hybrid_combine.py --run "$OUT" --empty empty_cutouts_expanded_screened.h5 \
        --real "$EC/real_dapool_images.h5" \
        --out "$NATIVE" --seed "$COMBSEED" \
        --deflector_stamps "$STAMPS" --deflector_augment --deflector_jitter 1.0 \
        --deflector_mag_csv lens_light_empirical.csv \
        --companion_stamps source_stamps_clean.h5 \
        --companion_rate_lo 8 --companion_rate_hi 26 --companion_flux_pct 35
    cd "$EC"
    $PY euclidise.py --inp "$NATIVE" --out "$EUC" --seed $((9601 + S))
    $PY euclidise_arcs.py "$OUT" "$ARCE"
    $PY arc_visibility_select.py --arcs "$ARCE" --sim "$EUC" --out "$SEL" \
        --thresh 0.7 --min_extent 150
    cd "$TILES"
    rm -f "$OUT"/image_*.npy
    rm -rf "$ARCE"
    rm -f "$NATIVE" "$EUC"
done
echo "SHARD_DONE $I"
