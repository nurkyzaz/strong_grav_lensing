#!/bin/bash
# Stage-3 v3 companion dataset in 3 sequential waves (QOS caps 8 jobs).
# Run from ~/cosmos_acs/tiles: nohup bash submit_gen3.sh > submit_gen3.log 2>&1 &
set -e
mkdir -p /home/user/nurkyz/paltas_shards3
echo "wave 1: tasks 0-7 (sub-shards 0-31, train)"
sbatch --wait --array=0-7 --export=ALL,OFFSET=0  generate_stage3_companions.sbatch
echo "wave 2: tasks 8-15 (sub-shards 32-63, train)"
sbatch --wait --array=0-7 --export=ALL,OFFSET=8  generate_stage3_companions.sbatch
echo "wave 3: tasks 16-21 (sub-shards 64-79 train, 80-87 val)"
sbatch --wait --array=0-5 --export=ALL,OFFSET=16 generate_stage3_companions.sbatch
echo "ALL_WAVES_DONE"
