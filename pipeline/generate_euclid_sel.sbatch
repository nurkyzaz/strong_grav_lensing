#!/bin/bash
#SBATCH --job-name=lf_geneuc
#SBATCH --partition=normal
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=2
#SBATCH --mem=8G
#SBATCH --time=08:00:00
#SBATCH --output=/home/user/nurkyz/paltas_shards_euclid/slurm_%A_%a.out

# EUCLID-ARM full dataset (R1.2b final recipe, 2026-07-09, pilots v2j1/B2/C/C2):
# high-SB COSMOS sources (SB<=21) + SLACS source-z (truncN(0.65,0.15,[0.55,1.1]))
# + pathb real deflector light (jitter 1px) + screened backdrops + DA-pool noise
# -> Euclidise -> arc-visibility selection (SNR>0.7 + extent>=150, prominence-matched).
# Sub-shard S=4*I+j; S 0-79 train (2500 renders -> ~1275 selected each),
# S 80-87 val (1250 -> ~640 each; kernel- AND stamp-disjoint).
# Seeds 5701+/6101+ (disjoint from every prior generation).
set -e
PY=/home/user/nurkyz/miniconda3/envs/Stronglensing/bin/python
TILES=/home/user/nurkyz/cosmos_acs/tiles
EC=/home/user/nurkyz/einstein_cnn
SHARDS=/home/user/nurkyz/paltas_shards_euclid
mkdir -p "$SHARDS"
cd "$TILES"

OFFSET=${OFFSET:-0}
I=$((OFFSET + SLURM_ARRAY_TASK_ID))
for j in 0 1 2 3; do
    S=$((4 * I + j))
    if [ "$I" -lt 20 ]; then N=2100; else N=1050; fi
    if [ "$S" -lt 80 ]; then STAMPS=deflector_stamps_lrg_v6_train.h5; else STAMPS=deflector_stamps_lrg_v6_val.h5; fi
    GENSEED=$((5701 + S))
    COMBSEED=$((6101 + S))
    KERNEL=$(printf 'psf_bank_v2/kernel_%02d_extended.npy' "$S")
    OUT="$SHARDS/sub_$(printf '%02d' "$S")"
    ARCE="$SHARDS/arcs_euclid_$(printf '%02d' "$S")"
    NATIVE="$SHARDS/native_$(printf '%02d' "$S").h5"
    EUC="$SHARDS/euclid_$(printf '%02d' "$S").h5"
    SEL="$SHARDS/hybrid_shard_$(printf '%02d' "$S").h5"   # name matches merge_hybrid_shards.py's glob
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
    $PY euclidise.py --inp "$NATIVE" --out "$EUC" --seed $((7101 + S))
    $PY euclidise_arcs.py "$OUT" "$ARCE"
    $PY arc_visibility_select.py --arcs "$ARCE" --sim "$EUC" --out "$SEL" \
        --thresh 0.7 --min_extent 150
    cd "$TILES"
    rm -f "$OUT"/image_*.npy
    rm -rf "$ARCE"
    rm -f "$NATIVE" "$EUC"
done
echo "SHARD_DONE $I"
