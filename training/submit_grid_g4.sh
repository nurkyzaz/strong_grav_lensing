#!/bin/bash
# G4 training grid: quick-train sanity gate, then 17 members in waves, then
# arbitration. Run: nohup bash submit_grid_g4.sh > submit_grid_g4.log 2>&1 &
set -e
cd /home/user/nurkyz/einstein_cnn

echo "WAVE 0 (quick-train sanity) $(date)"
sbatch --wait --export=ALL,ARCH=resnet,SEED=0,LR=1e-3,CKPT=qt_g4_resnet.pt,EPOCHS=10,LIMIT=20000 train_g4_member.sbatch
MAE=$(grep "epoch  10" slurm_g4_*.out | tail -1 | sed 's/.*val_MAE \([0-9.]*\).*/\1/')
echo "quick-train val_MAE: $MAE"
ok=$(python3 -c "print(1 if float('$MAE' or 1) < 0.25 else 0)" 2>/dev/null || echo 0)
if [ "$ok" != "1" ]; then echo "G4_QUICKTRAIN_FAIL ($MAE) — STOP"; exit 1; fi

wave () {
    pids=()
    for spec in "$@"; do
        read -r A S L C <<< "$spec"
        sbatch --wait --export=ALL,ARCH=$A,SEED=$S,LR=$L,CKPT=$C train_g4_member.sbatch &
        pids+=($!); sleep 2
    done
    for p in "${pids[@]}"; do wait "$p"; done
}
echo "WAVE 1 $(date)"
wave "resnet 1 1e-3 g4_resnet_s1.pt" "resnet 2 1e-3 g4_resnet_s2.pt" \
     "resnet 3 1e-3 g4_resnet_s3.pt" "inceptionnext 1 1e-3 g4_incnext_s1.pt" \
     "inceptionnext 2 1e-3 g4_incnext_s2.pt" "inceptionnext 3 1e-3 g4_incnext_s3.pt" \
     "convnextv2 1 3e-4 g4_cnv2_s1.pt" "resnet50 1 1e-3 g4_r50_s1.pt"
echo "WAVE 2 $(date)"
wave "resnet 4 1e-3 g4_resnet_s4.pt" "resnet 5 1e-3 g4_resnet_s5.pt" \
     "inceptionnext 4 1e-3 g4_incnext_s4.pt" "inceptionnext 5 1e-3 g4_incnext_s5.pt" \
     "convnextv2 2 3e-4 g4_cnv2_s2.pt" "convnextv2 3 3e-4 g4_cnv2_s3.pt" \
     "resnet50 2 1e-3 g4_r50_s2.pt" "resnet50 3 1e-3 g4_r50_s3.pt"
echo "WAVE 3 (logpolar low-priority seat) $(date)"
sbatch --wait --export=ALL,ARCH=logpolar,SEED=1,LR=1e-3,CKPT=g4_logpolar_s1.pt train_g4_member.sbatch
echo "ARBITRATION $(date)"
sbatch --wait g4_arbitrate.sbatch
echo "G4_GRID_ALL_DONE $(date)"
