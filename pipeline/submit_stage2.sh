#!/bin/bash
# Submit the 22-shard Stage-2 generation in THREE SEQUENTIAL waves (this
# cluster's QOS "normal" caps MaxJobs/MaxSubmit at 8, so more than 8 array
# tasks can be in flight at once -- each wave must fully finish before the
# next is submitted). `sbatch --wait` blocks until the whole array completes.
# Run from ~/cosmos_acs/tiles, nohup'd so it survives an SSH disconnect:
#   nohup bash submit_stage2.sh > submit_stage2.log 2>&1 &
set -e

echo "wave 1: shards 0-7 (train)"
sbatch --wait --array=0-7 --export=ALL,OFFSET=0  generate_stage2.sbatch

echo "wave 2: shards 8-15 (train)"
sbatch --wait --array=0-7 --export=ALL,OFFSET=8  generate_stage2.sbatch

echo "wave 3: shards 16-21 (16-19 train, 20-21 val)"
sbatch --wait --array=0-5 --export=ALL,OFFSET=16 generate_stage2.sbatch

echo "ALL_WAVES_DONE"
