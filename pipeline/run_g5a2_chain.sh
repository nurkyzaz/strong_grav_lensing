#!/bin/bash
# G5a v2 chain (Nurkyz 2026-07-14): retrain on 10,660 (fresh 500 calib
# holdout), 12 members, harvest + submission2 CSVs. Disconnected-safe.
set -e
cd /home/user/nurkyz/einstein_cnn
MARK=/home/user/nurkyz/einstein_cnn/G5A2_ABORT
fail() { echo "$1" | tee "$MARK"; exit 1; }

echo "CONVERT v2 $(date)"
sbatch --wait /home/user/nurkyz/cosmos_acs/roman_dc/rung0v2_convert.sbatch \
    || fail "G5A2_ABORT: converter failed"

wave () {
    pids=()
    for spec in "$@"; do
        read -r A S L C V <<< "$spec"
        sbatch --wait --export=ALL,ARCH=$A,SEED=$S,LR=$L,CKPT=$C,VARIANT=$V,DATA_PREFIX=rung0v2 \
            train_rung0_member.sbatch &
        pids+=($!); sleep 2
    done
    for p in "${pids[@]}"; do wait "$p" || fail "G5A2_ABORT: member failed"; done
}
echo "WAVE 1 (f106 v2) $(date)"
wave "convnextv2 1 3e-4 rung0v2_f106_cnv2_s1.pt f106" \
     "convnextv2 2 3e-4 rung0v2_f106_cnv2_s2.pt f106" \
     "convnextv2 3 3e-4 rung0v2_f106_cnv2_s3.pt f106" \
     "resnet50 1 1e-3 rung0v2_f106_r50_s1.pt f106" \
     "resnet50 2 1e-3 rung0v2_f106_r50_s2.pt f106" \
     "resnet50 3 1e-3 rung0v2_f106_r50_s3.pt f106"
echo "WAVE 2 (3band v2) $(date)"
wave "convnextv2 1 3e-4 rung0v2_3band_cnv2_s1.pt 3band" \
     "convnextv2 2 3e-4 rung0v2_3band_cnv2_s2.pt 3band" \
     "convnextv2 3 3e-4 rung0v2_3band_cnv2_s3.pt 3band" \
     "resnet50 1 1e-3 rung0v2_3band_r50_s1.pt 3band" \
     "resnet50 2 1e-3 rung0v2_3band_r50_s2.pt 3band" \
     "resnet50 3 1e-3 rung0v2_3band_r50_s3.pt 3band"

echo "HARVEST + SUBMISSION2 $(date)"
sbatch --wait /home/user/nurkyz/cosmos_acs/roman_dc/g5a2_harvest.sbatch \
    || fail "G5A2_ABORT: harvest failed"
echo "G5A2_CHAIN_ALL_DONE $(date)"
