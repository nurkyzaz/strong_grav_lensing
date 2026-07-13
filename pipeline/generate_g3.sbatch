#!/bin/bash
#SBATCH --job-name=lf_genG3
#SBATCH --partition=normal
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=2
#SBATCH --mem=8G
#SBATCH --time=08:00:00
#SBATCH --output=/home/user/nurkyz/paltas_shards_g3/slurm_%A_%a.out

# GEN4-G3 full Euclid arm: SAME retained population manifests as the G4 run
# (paltas_shards_g4/manifest_XX.csv), euclidise now uses the REAL ACS->VIS
# matching kernel (pilot A gates PASS, job 47606). Same seeds as G4 ->
# deterministic re-render; assign cmp check verifies.
set -e
PY=/home/user/nurkyz/miniconda3/envs/Stronglensing/bin/python
TILES=/home/user/nurkyz/cosmos_acs/tiles
EC=/home/user/nurkyz/einstein_cnn
G4=/home/user/nurkyz/paltas_shards_g4
SHARDS=/home/user/nurkyz/paltas_shards_g3
mkdir -p "$SHARDS"
cd "$TILES"

OFFSET=${OFFSET:-0}
I=$((OFFSET + SLURM_ARRAY_TASK_ID))
for j in 0 1 2 3; do
    S=$((4 * I + j))
    if [ "$I" -lt 20 ]; then N=3000; else N=1500; fi
    KERNEL=$(printf 'psf_bank_v2/kernel_%02d_extended.npy' "$S")
    MAN="$G4/manifest_$(printf '%02d' "$S").csv"
    test -s "$MAN"   # retained manifests ARE the population; never regenerate
    OUT="$SHARDS/sub_$(printf '%02d' "$S")"
    ARCE="$SHARDS/arcs_euclid_$(printf '%02d' "$S")"
    NATIVE="$SHARDS/native_$(printf '%02d' "$S").h5"
    EUC="$SHARDS/euclid_$(printf '%02d' "$S").h5"
    SEL="$SHARDS/hybrid_shard_$(printf '%02d' "$S").h5"
    ASSIGN="$SHARDS/assign_$(printf '%02d' "$S").csv"
    echo "sub-shard $S: n=$N kernel=$KERNEL (manifest reused from G4)"
    export LF_PSF_KERNEL="$KERNEL"
    export LF_G2_MANIFEST="$MAN"
    $PY run_paltas_pilot.py config_lensfusion_acs_g2.py "$OUT" --n "$N" --seed $((10100 + S))
    $PY g2_join_assign.py "$OUT" "$MAN" "$ASSIGN"
    cmp -s "$ASSIGN" "$G4/assign_$(printf '%02d' "$S").csv" \
        && echo "assign identical to G4 run (deterministic re-render confirmed)" \
        || echo "WARN: assign differs from G4 run — self-consistent but not draw-identical; disclose"
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
