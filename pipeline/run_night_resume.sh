#!/bin/bash
# NIGHT CHAIN RESUME (2026-07-13): both AR pilots PASSED all gates on 07-12;
# the abort was a marker typo (ar2 script printed AR1_PILOT_DONE; fixed).
# Resumes at STAGE 5: g4ar combined regen -> merge+gates -> grid+arbitration
# -> EVAL #22. Same gate checks as run_night_chain.sh.
# Run: nohup bash run_night_resume.sh > run_night_resume.log 2>&1 &
set -e
EC=/home/user/nurkyz/einstein_cnn
TI=/home/user/nurkyz/cosmos_acs/tiles
abort () { echo "RESUME_ABORT: $1  $(date)"; exit 1; }

echo "STAGE 5: g4ar combined regeneration  $(date)"
cd "$TI"
bash submit_g4ar.sh 2>&1 | tee submit_g4ar.log
grep -q G4AR_ALL_WAVES_DONE submit_g4ar.log || abort "g4ar generation incomplete"
N=$(ls /home/user/nurkyz/paltas_shards_g4ar/hybrid_shard_*.h5 2>/dev/null | wc -l)
[ "$N" -eq 88 ] || abort "g4ar shards: $N/88"

echo "STAGE 5b: g4ar merge + gates  $(date)"
sbatch --wait merge_gate_g4ar.sbatch
grep -q MERGE_GATE_G4AR_DONE "$TI/merge_gate_g4ar.out" || abort "g4ar merge incomplete"
grep -q MERGE_LABELS_OK "$TI/merge_gate_g4ar.out" || abort "g4ar labels"
grep -q "FJ gate: .*PASS" "$TI/merge_gate_g4ar.out" || abort "g4ar FJ gate"
[ "$(grep -c '\[PASS' "$TI/merge_gate_g4ar.out")" -ge 2 ] || abort "g4ar realism gates"

echo "STAGE 5c: g4ar grid + arbitration  $(date)"
cd "$EC"
bash submit_grid_g4ar.sh 2>&1 | tee submit_grid_g4ar.log
grep -q G4AR_GRID_ALL_DONE submit_grid_g4ar.log || abort "g4ar grid incomplete"
test -s "$EC/g4ar_recal.json" || abort "g4ar_recal.json missing"

echo "STAGE 6: EVAL #22  $(date)"
sbatch --wait l22_eval.sbatch
tail -1 "$(ls -t $EC/slurm_l22_eval_*.out | head -1)" | grep -q EVAL22_DONE || abort "eval22"
echo "NIGHT_RESUME_ALL_DONE  $(date)"
