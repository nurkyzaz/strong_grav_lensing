#!/bin/bash
# REBALANCED Euclid-arm generation, 3 sequential waves (QOS cap 8).
# Run: nohup bash submit_euclid_reb.sh > submit_euclid_reb.log 2>&1 &
# Deliberately does NOT auto-submit the merge: quota is tight (83.9 GB at
# launch) — merge is submitted by the session after a quota check / cleanup.
set -e
mkdir -p /home/user/nurkyz/paltas_shards_euclid_reb
echo "wave 1: tasks 0-7 (sub-shards 0-31, train)  $(date)"
sbatch --wait --array=0-7 --export=ALL,OFFSET=0  generate_euclid_reb.sbatch
echo "wave 2: tasks 8-15 (sub-shards 32-63, train)  $(date)"
sbatch --wait --array=0-7 --export=ALL,OFFSET=8  generate_euclid_reb.sbatch
echo "wave 3: tasks 16-21 (sub-shards 64-79 train, 80-87 val)  $(date)"
sbatch --wait --array=0-5 --export=ALL,OFFSET=16 generate_euclid_reb.sbatch
echo "ALL_WAVES_DONE $(date)"
quota -s 2>/dev/null | tail -2 || df -h ~ | tail -1
echo "NEXT: quota check -> merge_gate submission by the session (NOT auto)"
