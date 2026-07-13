#!/bin/bash
# GEN4 Track-N native-arm generation, 3 waves under the QOS-8 cap.
# STAGED — submit only after: (1) eval #17 decisions, (2) quota check
# (needs ~8 GB headroom; `quota -s` first, delete superseded data if tight).
# Run: nohup bash submit_g4_native.sh > submit_g4_native.log 2>&1 &
set -e
cd /home/user/nurkyz/cosmos_acs/tiles
quota -s 2>/dev/null | tail -1
echo "wave 1: tasks 0-7  $(date)"
sbatch --wait --array=0-7 --export=ALL,OFFSET=0  generate_g4_native.sbatch
echo "wave 2: tasks 8-15  $(date)"
sbatch --wait --array=0-7 --export=ALL,OFFSET=8  generate_g4_native.sbatch
echo "wave 3: tasks 16-21  $(date)"
sbatch --wait --array=0-5 --export=ALL,OFFSET=16 generate_g4_native.sbatch
echo "G4_NATIVE_ALL_WAVES_DONE $(date)"
quota -s 2>/dev/null | tail -1
