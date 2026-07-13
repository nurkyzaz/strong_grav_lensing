#!/bin/bash
#SBATCH --job-name=lf_genG4n
#SBATCH --partition=normal
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=2
#SBATCH --mem=8G
#SBATCH --time=08:00:00
#SBATCH --output=/home/user/nurkyz/paltas_shards_g4/slurmn_%A_%a.out

# GEN4 Track-N: native-HST arm from the SAME retained population manifests as
# the Euclid arm (P5 "one population, N renderings" made literal). Per
# sub-shard: reuse manifest_XX.csv -> re-render (same seeds; join assert
# catches any desync) -> combine native (same seed -> same backdrops) ->
# euclidise + arc-select (reproduces the Euclid selection mask) ->
# g4_native_select keeps the SAME systems in the native rendering.
# STAGED ONLY — do not submit before a quota check (~+8 GB transient/kept);
# decide post-eval-#17 what to delete first.
set -e
PY=/home/user/nurkyz/miniconda3/envs/Stronglensing/bin/python
TILES=/home/user/nurkyz/cosmos_acs/tiles
EC=/home/user/nurkyz/einstein_cnn
SHARDS=/home/user/nurkyz/paltas_shards_g4
cd "$TILES"

OFFSET=${OFFSET:-0}
I=$((OFFSET + SLURM_ARRAY_TASK_ID))
for j in 0 1 2 3; do
    S=$((4 * I + j))
    if [ "$I" -lt 20 ]; then N=3000; else N=1500; fi
    KERNEL=$(printf 'psf_bank_v2/kernel_%02d_extended.npy' "$S")
    MAN="$SHARDS/manifest_$(printf '%02d' "$S").csv"
    test -s "$MAN"   # retained manifests are the population; never regenerate
    OUT="$SHARDS/subn_$(printf '%02d' "$S")"
    ARCE="$SHARDS/arcsn_euclid_$(printf '%02d' "$S")"
    NATIVE="$SHARDS/native_$(printf '%02d' "$S").h5"
    EUC="$SHARDS/euclidn_$(printf '%02d' "$S").h5"
    EUCSEL="$SHARDS/euclidn_sel_$(printf '%02d' "$S").h5"
    SEL="$SHARDS/native_shard_$(printf '%02d' "$S").h5"
    ASSIGN="$SHARDS/assignn_$(printf '%02d' "$S").csv"
    echo "native sub-shard $S: n=$N kernel=$KERNEL"
    export LF_PSF_KERNEL="$KERNEL"
    export LF_G2_MANIFEST="$MAN"
    $PY run_paltas_pilot.py config_lensfusion_acs_g2.py "$OUT" --n "$N" --seed $((10100 + S))
    $PY g2_join_assign.py "$OUT" "$MAN" "$ASSIGN"
    cmp -s "$ASSIGN" "$SHARDS/assign_$(printf '%02d' "$S").csv" \
        && echo "assign identical to Euclid-arm run (deterministic re-render confirmed)" \
        || echo "WARN: assign differs from original run — native set is self-consistent but not draw-identical; disclose"
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
    $PY arc_visibility_select.py --arcs "$ARCE" --sim "$EUC" --out "$EUCSEL" \
        --thresh 0.7 --min_extent 150
    cd "$TILES"
    $PY g4_native_select.py --native "$NATIVE" --euclid-sel "$EUCSEL" --out "$SEL"
    rm -f "$OUT"/image_*.npy
    rm -rf "$ARCE"
    rm -f "$NATIVE" "$EUC" "$EUCSEL"
done
echo "NATIVE_SHARD_DONE $I"
