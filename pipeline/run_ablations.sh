#!/bin/bash
# MASTER_PLAN D1 ablation campaign (2026-07-06): four dataset variants, each
# identical to the v2 reference except ONE ingredient; generate -> merge ->
# train -> evaluate on the frozen benchmark (evals logged as the pre-approved
# ablation bundle) -> delete the variant's dataset (quota).
# Run from ~/cosmos_acs/tiles:  nohup bash run_ablations.sh > ablations.log 2>&1 &
set -e
PY=/home/user/nurkyz/miniconda3/envs/Stronglensing/bin/python
TILES=/home/user/nurkyz/cosmos_acs/tiles
EIN=/home/user/nurkyz/einstein_cnn
cd "$TILES"

run_variant () {
    NAME=$1; CONFIG=$2; KDIR=$3; KFIX=$4; CFLAGS=$5; SEEDBASE=$6
    SHARDS=/home/user/nurkyz/paltas_abl/$NAME
    echo "=== ABLATION $NAME: config=$CONFIG kdir=$KDIR kfix='$KFIX' cflags='$CFLAGS' ==="
    mkdir -p "$SHARDS"
    for WAVE in "0-7:0" "0-7:8" "0-5:16"; do
        ARR=${WAVE%%:*}; OFF=${WAVE##*:}
        sbatch --wait --array="$ARR" \
            --export=ALL,CONFIG="$CONFIG",SHARDS="$SHARDS",KERNEL_DIR="$KDIR",KERNEL_FIXED="$KFIX",COMBINE_FLAGS="$CFLAGS",SEEDBASE="$SEEDBASE",OFFSET="$OFF" \
            generate_ablation.sbatch
    done
    $PY merge_hybrid_shards.py --shards "$SHARDS" --train-max-id 80 \
        --train-out "$EIN/abl_${NAME}_100k.h5" --val-out "$EIN/abl_${NAME}_5k.h5"
    rm -f "$SHARDS"/hybrid_shard_*.h5
    TRAIN_H5="$EIN/abl_${NAME}_100k.h5" VAL_H5="$EIN/abl_${NAME}_5k.h5" \
        CKPT="$EIN/einstein_cnn_abl_${NAME}.pt" \
        sbatch --wait --export=ALL,TRAIN_H5="$EIN/abl_${NAME}_100k.h5",VAL_H5="$EIN/abl_${NAME}_5k.h5",CKPT="$EIN/einstein_cnn_abl_${NAME}.pt" \
        train_ablation.sbatch
    cd "$EIN"
    $PY predict_real_lenses_paltas.py --ckpt "einstein_cnn_abl_${NAME}.pt" \
        --real real_slacs_images.h5 --tta --outdir brian_run --out "theta_E_slacs_abl_${NAME}.csv"
    $PY predict_real_lenses_paltas.py --ckpt "einstein_cnn_abl_${NAME}.pt" \
        --real real_s4tm_images.h5 --tta --outdir brian_run --out "theta_E_s4tm_abl_${NAME}.csv"
    $PY metrics_real.py "brian_run/theta_E_slacs_abl_${NAME}.csv" \
        "brian_run/theta_E_s4tm_abl_${NAME}.csv" --exclude J0955+0101 \
        --out "brian_run/scatter_abl_${NAME}.png"
    # keep ckpt + prediction CSVs; drop the 7 GB dataset (quota)
    rm -f "$EIN/abl_${NAME}_100k.h5" "$EIN/abl_${NAME}_5k.h5"
    cd "$TILES"
    echo "=== ABLATION $NAME DONE ==="
}

# A3 first: the causal spine (flat vs m3-like skewed theta_E prior)
run_variant A3_skewprior config_ablation_A3_nonoise.py psf_bank_v2 "" "" 301

# A1: empirical focus-diverse ePSF bank -> single Gaussian FWHM 0.10" kernel
run_variant A1_gausspsf config_lensfusion_acs_nonoise.py psf_bank_v2 gaussian_fwhm2px_47.npy "" 1301

# A2: real empty-cutout backdrops -> pure Gaussian noise, same RMS draws
run_variant A2_gaussnoise config_lensfusion_acs_nonoise.py psf_bank_v2 "" "--no-backdrop" 2301

# A4: benchmark-matched ePSF pool -> broad (non-benchmark) pool
run_variant A4_broadpool config_lensfusion_acs_nonoise.py psf_bank_broad "" "" 3301

echo "ALL_ABLATIONS_DONE"
