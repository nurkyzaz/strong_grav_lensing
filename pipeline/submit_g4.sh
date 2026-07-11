#!/bin/bash
# GEN4-G4 generation, 3 waves under the QOS-8 cap. No auto-merge (quota).
# Run: nohup bash submit_g4.sh > submit_g4.log 2>&1 &
set -e
mkdir -p /home/user/nurkyz/paltas_shards_g4
cd /home/user/nurkyz/cosmos_acs/tiles
python_bin=/home/user/nurkyz/miniconda3/envs/Stronglensing/bin/python
$python_bin g4_split_kine.py
echo "wave 1: tasks 0-7  $(date)"
sbatch --wait --array=0-7 --export=ALL,OFFSET=0  generate_g4.sbatch
echo "wave 2: tasks 8-15  $(date)"
sbatch --wait --array=0-7 --export=ALL,OFFSET=8  generate_g4.sbatch
echo "wave 3: tasks 16-21  $(date)"
sbatch --wait --array=0-5 --export=ALL,OFFSET=16 generate_g4.sbatch
echo "G4_ALL_WAVES_DONE $(date)"
quota -s 2>/dev/null | tail -1
