#!/bin/bash
# REB seed-honest training grid: 5x resnet + 5x inceptionnext (lr 1e-3),
# 3x convnextv2 (lr 3e-4), 3x resnet50 (lr 1e-3). Two waves under QOS-8.
# Run: nohup bash submit_grid_reb.sh > submit_grid_reb.log 2>&1 &
set -e
cd /home/user/nurkyz/einstein_cnn

wave () {
    pids=()
    for spec in "$@"; do
        read -r A S L C <<< "$spec"
        sbatch --wait --export=ALL,ARCH=$A,SEED=$S,LR=$L,CKPT=$C train_reb_member.sbatch &
        pids+=($!)
        sleep 2
    done
    for p in "${pids[@]}"; do wait "$p"; done
}

echo "WAVE 1 start $(date)"
wave "resnet 1 1e-3 reb_resnet_s1.pt" \
     "resnet 2 1e-3 reb_resnet_s2.pt" \
     "resnet 3 1e-3 reb_resnet_s3.pt" \
     "inceptionnext 1 1e-3 reb_incnext_s1.pt" \
     "inceptionnext 2 1e-3 reb_incnext_s2.pt" \
     "inceptionnext 3 1e-3 reb_incnext_s3.pt" \
     "convnextv2 1 3e-4 reb_cnv2_s1.pt" \
     "resnet50 1 1e-3 reb_r50_s1.pt"

echo "WAVE 2 start $(date)"
wave "resnet 4 1e-3 reb_resnet_s4.pt" \
     "resnet 5 1e-3 reb_resnet_s5.pt" \
     "inceptionnext 4 1e-3 reb_incnext_s4.pt" \
     "inceptionnext 5 1e-3 reb_incnext_s5.pt" \
     "convnextv2 2 3e-4 reb_cnv2_s2.pt" \
     "convnextv2 3 3e-4 reb_cnv2_s3.pt" \
     "resnet50 2 1e-3 reb_r50_s2.pt" \
     "resnet50 3 1e-3 reb_r50_s3.pt"

echo "GRID_ALL_DONE $(date)"
quota -s 2>/dev/null | tail -1
