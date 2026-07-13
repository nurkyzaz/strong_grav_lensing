#!/bin/bash
# GEN4-G3 Euclid-arm regeneration, 3 waves under the QOS-8 cap. No auto-merge.
# Run: nohup bash submit_g3.sh > submit_g3.log 2>&1 &
set -e
mkdir -p /home/user/nurkyz/paltas_shards_g3
cd /home/user/nurkyz/cosmos_acs/tiles
echo "wave 1: tasks 0-7  $(date)"
sbatch --wait --array=0-7 --export=ALL,OFFSET=0  generate_g3.sbatch
echo "wave 2: tasks 8-15  $(date)"
sbatch --wait --array=0-7 --export=ALL,OFFSET=8  generate_g3.sbatch
echo "wave 3: tasks 16-21  $(date)"
sbatch --wait --array=0-5 --export=ALL,OFFSET=16 generate_g3.sbatch
echo "G3_ALL_WAVES_DONE $(date)"
quota -s 2>/dev/null | tail -1
