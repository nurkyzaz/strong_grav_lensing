#!/bin/bash
#SBATCH --job-name=lf_genG4
#SBATCH --partition=normal
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=2
#SBATCH --mem=8G
#SBATCH --time=08:00:00
#SBATCH --output=/home/user/nurkyz/paltas_shards_g4/slurm_%A_%a.out

# GEN4-G4 full dataset (Euclid arm): tempered self-consistent population
# (G2 pilot v4 PASS). Per sub-shard: manifest -> render (manifest config) ->
# join -> combine (manifest mode, native amplitude) -> euclidise -> select
# (0.7,150) -> cleanup. Sub-shards 0-79 train (3000 renders -> ~1260 sel),
# 80-87 val (1500 -> ~630; VAL stamps + val kernels 80-87 + disjoint seeds).
set -e
PY=/home/user/nurkyz/miniconda3/envs/Stronglensing/bin/python
TILES=/home/user/nurkyz/cosmos_acs/tiles
EC=/home/user/nurkyz/einstein_cnn
SHARDS=/home/user/nurkyz/paltas_shards_g4
mkdir -p "$SHARDS"
cd "$TILES"

OFFSET=${OFFSET:-0}
I=$((OFFSET + SLURM_ARRAY_TASK_ID))
for j in 0 1 2 3; do
    S=$((4 * I + j))
    if [ "$I" -lt 20 ]; then N=3000; else N=1500; fi
    if [ "$S" -lt 80 ]; then KINE=g4_kine_train.csv; else KINE=g4_kine_val.csv; fi
    MROWS=$((N * 115 / 100))
    KERNEL=$(printf 'psf_bank_v2/kernel_%02d_extended.npy' "$S")
    MAN="$SHARDS/manifest_$(printf '%02d' "$S").csv"
    OUT="$SHARDS/sub_$(printf '%02d' "$S")"
    ARCE="$SHARDS/arcs_euclid_$(printf '%02d' "$S")"
    NATIVE="$SHARDS/native_$(printf '%02d' "$S").h5"
    EUC="$SHARDS/euclid_$(printf '%02d' "$S").h5"
    SEL="$SHARDS/hybrid_shard_$(printf '%02d' "$S").h5"
    ASSIGN="$SHARDS/assign_$(printf '%02d' "$S").csv"
    echo "sub-shard $S: n=$N kine=$KINE kernel=$KERNEL"
    $PY g2_make_manifest.py --kine "$KINE" --n "$MROWS" --seed $((9700 + S)) --out "$MAN"
    export LF_PSF_KERNEL="$KERNEL"
    export LF_G2_MANIFEST="$MAN"
    $PY run_paltas_pilot.py config_lensfusion_acs_g2.py "$OUT" --n "$N" --seed $((10100 + S))
    $PY g2_join_assign.py "$OUT" "$MAN" "$ASSIGN"
    $PY hybrid_combine.py --run "$OUT" --empty empty_cutouts_expanded_screened.h5 \
        --real "$EC/real_dapool_images.h5" \
        --out "$NATIVE" --seed $((10600 + S)) \
        --deflector_stamps deflector_stamps_g4_all.h5 \
        --deflector_manifest "$ASSIGN" --deflector_jitter 1.0 \
        --companion_stamps source_stamps_clean.h5 \
        --companion_rate_lo 8 --companion_rate_hi 26 --companion_flux_pct 35
    cd "$EC"
    $PY euclidise.py --inp "$NATIVE" --out "$EUC" --seed $((11100 + S))
    $PY euclidise_arcs.py "$OUT" "$ARCE"
    $PY arc_visibility_select.py --arcs "$ARCE" --sim "$EUC" --out "$SEL" \
        --thresh 0.7 --min_extent 150
    cd "$TILES"
    rm -f "$OUT"/image_*.npy
    rm -rf "$ARCE"
    rm -f "$NATIVE" "$EUC"
done
echo "SHARD_DONE $I"
