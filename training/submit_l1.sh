#!/bin/bash
# L1 submit chain (run under nohup on the login node; established wave pattern).
# 10 member trainings in waves under the QOS-8 cap, then the sim-val
# arbitration job. Sequential `sbatch --wait` per wave; this script SUBMITS,
# nothing else does (no monitor side-effects).
set -e
cd /home/user/nurkyz/einstein_cnn

wave () {  # args: list of "ARCH SEED CKPT INIT" strings
    pids=()
    for spec in "$@"; do
        read -r A S C I <<< "$spec"
        sbatch --wait --export=ALL,ARCH=$A,SEED=$S,CKPT=$C,INIT=$I train_l1_member.sbatch &
        pids+=($!)
        sleep 2
    done
    for p in "${pids[@]}"; do wait "$p"; done
}

echo "WAVE 1 start $(date)"
wave "inceptionnext 1 einstein_cnn_euclid_sel_inceptionnext_s1.pt " \
     "inceptionnext 2 einstein_cnn_euclid_sel_inceptionnext_s2.pt " \
     "resnet 1 einstein_cnn_euclid_sel_resnet_s1.pt " \
     "resnet 2 einstein_cnn_euclid_sel_resnet_s2.pt " \
     "inceptionnext 3 einstein_cnn_euclid_sel_inceptionnext_s3.pt " \
     "resnet 3 einstein_cnn_euclid_sel_resnet_s3.pt "

echo "WAVE 2 start $(date)"
wave "inceptionnext 4 einstein_cnn_euclid_sel_inceptionnext_s4.pt " \
     "resnet 4 einstein_cnn_euclid_sel_resnet_s4.pt " \
     "inceptionnext 5 einstein_cnn_euclid_sel_inceptionnext_tinit.pt einstein_cnn_v3_inceptionnext.pt" \
     "resnet 5 einstein_cnn_euclid_sel_resnet_tinit.pt einstein_cnn_v3_resnet.pt"

echo "ARBITRATION start $(date)"
sbatch --wait l1_arbitrate.sbatch
echo "L1_ALL_DONE $(date)"
