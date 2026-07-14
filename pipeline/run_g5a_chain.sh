#!/bin/bash
# G5 PATH-A CHAIN (Nurkyz ruling 2026-07-14: option c, 3-band in scope).
# Disconnected-safe: nohup on the login node; every hop gated; abort marker
# on failure; nothing here touches the unlabeled test set with a model.
# Chain: convert -> quick-train gate (f106) -> wave1 6x f106 -> wave2 6x
# 3band. Model selection later uses val_rung0_* ONLY (challenge-val).
set -e
cd /home/user/nurkyz/einstein_cnn
MARK=/home/user/nurkyz/einstein_cnn/G5A_ABORT

fail() { echo "$1" | tee "$MARK"; exit 1; }

echo "CONVERT $(date)"
sbatch --wait /home/user/nurkyz/cosmos_acs/roman_dc/rung0_convert.sbatch \
    || fail "G5A_ABORT: converter failed"
grep -q RUNG0_CONVERT_DONE $(ls -t slurm_rung0_conv_*.out | head -1) \
    || fail "G5A_ABORT: converter marker missing"

echo "QUICK-TRAIN GATE $(date)"
sbatch --wait --export=ALL,ARCH=convnextv2,SEED=0,LR=3e-4,CKPT=qt_rung0_cnv2.pt,VARIANT=f106,EPOCHS=10 \
    train_rung0_member.sbatch || fail "G5A_ABORT: quick-train failed"
MAE=$(grep "epoch  10" $(ls -t slurm_rung0_*.out | head -1) | tail -1 | sed 's/.*val_MAE \([0-9.]*\).*/\1/')
echo "quick-train val_MAE: $MAE"
ok=$(python3 -c "print(1 if float('$MAE' or 1) < 0.25 else 0)" 2>/dev/null || echo 0)
[ "$ok" = "1" ] || fail "G5A_ABORT: quick-train val_MAE $MAE >= 0.25"

wave () {
    pids=()
    for spec in "$@"; do
        read -r A S L C V <<< "$spec"
        sbatch --wait --export=ALL,ARCH=$A,SEED=$S,LR=$L,CKPT=$C,VARIANT=$V \
            train_rung0_member.sbatch &
        pids+=($!); sleep 2
    done
    for p in "${pids[@]}"; do wait "$p" || fail "G5A_ABORT: member failed in wave"; done
}

echo "WAVE 1 (f106) $(date)"
wave "convnextv2 1 3e-4 rung0_f106_cnv2_s1.pt f106" \
     "convnextv2 2 3e-4 rung0_f106_cnv2_s2.pt f106" \
     "convnextv2 3 3e-4 rung0_f106_cnv2_s3.pt f106" \
     "resnet50 1 1e-3 rung0_f106_r50_s1.pt f106" \
     "resnet50 2 1e-3 rung0_f106_r50_s2.pt f106" \
     "resnet50 3 1e-3 rung0_f106_r50_s3.pt f106"

echo "WAVE 2 (3band) $(date)"
wave "convnextv2 1 3e-4 rung0_3band_cnv2_s1.pt 3band" \
     "convnextv2 2 3e-4 rung0_3band_cnv2_s2.pt 3band" \
     "convnextv2 3 3e-4 rung0_3band_cnv2_s3.pt 3band" \
     "resnet50 1 1e-3 rung0_3band_r50_s1.pt 3band" \
     "resnet50 2 1e-3 rung0_3band_r50_s2.pt 3band" \
     "resnet50 3 1e-3 rung0_3band_r50_s3.pt 3band"

echo "G5A_CHAIN_ALL_DONE $(date)"
