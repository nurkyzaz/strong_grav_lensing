#!/bin/bash
# Stage-2 v2 waves (QOS caps 8 concurrent jobs). Run from ~/cosmos_acs/tiles:
#   nohup bash submit_stage2_v2.sh > submit_stage2_v2.log 2>&1 &
set -e

echo "wave 1: tasks 0-7 (sub-shards 0-31, train)"
sbatch --wait --array=0-7 --export=ALL,OFFSET=0  generate_stage2_v2.sbatch

echo "wave 2: tasks 8-15 (sub-shards 32-63, train)"
sbatch --wait --array=0-7 --export=ALL,OFFSET=8  generate_stage2_v2.sbatch

echo "wave 3: tasks 16-21 (sub-shards 64-79 train, 80-87 val)"
sbatch --wait --array=0-5 --export=ALL,OFFSET=16 generate_stage2_v2.sbatch

echo "ALL_WAVES_DONE"
