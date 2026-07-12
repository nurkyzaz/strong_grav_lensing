#!/bin/bash
# G3 MASTER DRIVER — runs the remaining chain unattended, one stage at a time:
#   [wait for merge 47631] -> gate check -> training grid (quick-train gate +
#   2 waves + arbitration, via submit_grid_g3.sh inline) -> eval #18.
# Explicit-submit-script pattern (sbatch --wait); no other submitter may act
# while this runs. Any gate failure stops the chain with a CHAIN_ABORT marker.
# Run: nohup bash run_g3_chain.sh > run_g3_chain.log 2>&1 &
set -e
EC=/home/user/nurkyz/einstein_cnn
MERGE_OUT=/home/user/nurkyz/cosmos_acs/tiles/merge_gate_g3.out

abort () { echo "CHAIN_ABORT: $1  $(date)"; exit 1; }

echo "STAGE 0: waiting for merge+gates (job 47631)  $(date)"
for i in $(seq 1 240); do
    grep -q MERGE_GATE_G3_DONE "$MERGE_OUT" 2>/dev/null && break
    if ! squeue -h -j 47631 2>/dev/null | grep -q . ; then
        sleep 30   # let the filesystem settle, then final check
        grep -q MERGE_GATE_G3_DONE "$MERGE_OUT" 2>/dev/null && break
        abort "merge job ended without MERGE_GATE_G3_DONE (see $MERGE_OUT)"
    fi
    sleep 60
done
grep -q MERGE_GATE_G3_DONE "$MERGE_OUT" || abort "merge wait timed out"

echo "STAGE 0b: gate verification  $(date)"
NPASS=$(grep -c "PASS" "$MERGE_OUT" || true)
grep -q "FJ gate: .*PASS" "$MERGE_OUT" || abort "FJ gate not PASS"
grep -q "MERGE_LABELS_OK" "$MERGE_OUT" || abort "label verification missing"
[ "$NPASS" -ge 3 ] || abort "fewer than 3 PASS marks in merge gates"
echo "gates verified ($NPASS PASS marks)"

echo "STAGE 1: training grid + arbitration  $(date)"
cd "$EC"
bash submit_grid_g3.sh 2>&1 | tee submit_grid_g3.log
grep -q G3_GRID_ALL_DONE submit_grid_g3.log || abort "grid driver did not finish"
test -s "$EC/g3_recal.json" || abort "g3_recal.json missing after arbitration"

echo "STAGE 2: EVAL #18 (authorized; count 18)  $(date)"
sbatch --wait l18_eval.sbatch
tail -1 "$(ls -t $EC/slurm_l18_eval_*.out | head -1)" | grep -q EVAL18_DONE \
    || abort "eval job ended without EVAL18_DONE"
echo "G3_CHAIN_ALL_DONE  $(date)"
