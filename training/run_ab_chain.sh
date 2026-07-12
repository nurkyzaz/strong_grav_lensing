#!/bin/bash
# MASTER DRIVER for the parallel program (Nurkyz 2026-07-12: "do 1 then 2,
# run a in parallel"; 1 = eval #19, done). Serializes everything under the
# QOS-8 cap and the quota choke points:
#   native waves (running) -> native merge -> g3b regen waves -> g3b merge
#   -> g3b grid+arbitration -> native grid+arbitration
#   -> EVAL #20 (g3b, Euclid) -> EVAL #21 (native).
# Explicit-submit-script pattern; no other submitter while this runs.
# Run: nohup bash run_ab_chain.sh > run_ab_chain.log 2>&1 &
set -e
EC=/home/user/nurkyz/einstein_cnn
TI=/home/user/nurkyz/cosmos_acs/tiles

abort () { echo "AB_CHAIN_ABORT: $1  $(date)"; exit 1; }

wait_marker () {  # file, marker, driver-pgrep-pattern (optional), max-minutes
    local f=$1 m=$2 pat=$3 max=${4:-360}
    for i in $(seq 1 "$max"); do
        grep -q "$m" "$f" 2>/dev/null && return 0
        if [ -n "$pat" ] && ! pgrep -f "$pat" >/dev/null; then
            sleep 30
            grep -q "$m" "$f" 2>/dev/null && return 0
            abort "$pat died without $m"
        fi
        sleep 60
    done
    abort "timeout waiting for $m in $f"
}

echo "STAGE A1: waiting for native generation waves  $(date)"
wait_marker "$TI/submit_g4_native.log" G4_NATIVE_ALL_WAVES_DONE submit_g4_native.sh 300
N=$(ls /home/user/nurkyz/paltas_shards_g4n/hybrid_shard_*.h5 2>/dev/null | wc -l)
[ "$N" -eq 88 ] || abort "native shards: $N/88"
echo "native shards 88/88  $(date)"

echo "STAGE A2: native merge + gates  $(date)"
cd "$TI"
sbatch --wait merge_gate_g4native.sbatch
grep -q MERGE_GATE_G4NATIVE_DONE "$TI/merge_gate_g4native.out" || abort "native merge incomplete"
grep -q MERGE_LABELS_OK "$TI/merge_gate_g4native.out" || abort "native labels"
NP=$(grep -c "\[PASS" "$TI/merge_gate_g4native.out" || true)
[ "$NP" -ge 2 ] || abort "native realism gates: only $NP PASS"
echo "native merge gates OK ($NP PASS)"

echo "STAGE B1: g3b regeneration waves  $(date)"
cd "$TI"
bash submit_g3b.sh 2>&1 | tee submit_g3b.log
grep -q G3B_ALL_WAVES_DONE submit_g3b.log || abort "g3b generation incomplete"
N=$(ls /home/user/nurkyz/paltas_shards_g3b/hybrid_shard_*.h5 2>/dev/null | wc -l)
[ "$N" -eq 88 ] || abort "g3b shards: $N/88"

echo "STAGE B2: g3b merge + gates  $(date)"
sbatch --wait merge_gate_g3b.sbatch
grep -q MERGE_GATE_G3B_DONE "$TI/merge_gate_g3b.out" || abort "g3b merge incomplete"
grep -q MERGE_LABELS_OK "$TI/merge_gate_g3b.out" || abort "g3b labels"
grep -q "FJ gate: .*PASS" "$TI/merge_gate_g3b.out" || abort "g3b FJ gate"
NP=$(grep -c "\[PASS" "$TI/merge_gate_g3b.out" || true)
[ "$NP" -ge 2 ] || abort "g3b realism gates: only $NP PASS"
echo "g3b merge gates OK"

echo "STAGE B3: g3b grid + arbitration  $(date)"
cd "$EC"
bash submit_grid_g3b.sh 2>&1 | tee submit_grid_g3b.log
grep -q G3B_GRID_ALL_DONE submit_grid_g3b.log || abort "g3b grid incomplete"
test -s "$EC/g3b_recal.json" || abort "g3b_recal.json missing"

echo "STAGE A3: native grid + arbitration  $(date)"
bash submit_grid_g4n.sh 2>&1 | tee submit_grid_g4n.log
grep -q G4N_GRID_ALL_DONE submit_grid_g4n.log || abort "native grid incomplete"
test -s "$EC/g4n_recal.json" || abort "g4n_recal.json missing"

echo "STAGE B4: EVAL #20 (g3b, Euclid real-op benchmark)  $(date)"
sbatch --wait l20_eval.sbatch
tail -1 "$(ls -t $EC/slurm_l20_eval_*.out | head -1)" | grep -q EVAL20_DONE || abort "eval20"

echo "STAGE A4: EVAL #21 (native benchmark)  $(date)"
sbatch --wait l21_eval.sbatch
tail -1 "$(ls -t $EC/slurm_l21_eval_*.out | head -1)" | grep -q EVAL21_DONE || abort "eval21"

echo "AB_CHAIN_ALL_DONE  $(date)"
