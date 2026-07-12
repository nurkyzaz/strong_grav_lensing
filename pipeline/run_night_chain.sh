#!/bin/bash
# NIGHT DRIVER (Nurkyz 2026-07-12: cleanup + AR1/AR2 + G1b fetch, all
# automatic after the AB chain; nothing may endanger current results).
# Sequence:
#   0  wait for AB_CHAIN_ALL_DONE + empty queue (abort and TOUCH NOTHING on
#      AB_CHAIN_ABORT)
#   1  bank AB results into ~/night_bank/ (copies, never moves)
#   2  cleanup of the four superseded old-generation training sets + pilot
#      render dirs (approved by Nurkyz 2026-07-12 "you can do the cleanup";
#      NEVER touches: real_*, euclid_*, train_g3b*, train_g4native*, val_*,
#      checkpoints, retained manifests/assigns, euclid_sky pool)
#   3  launch G1b phase-1 fetch (login-node nohup, parallel to SLURM work)
#   4  AR1 pilot -> gates; AR2 pilot -> gates (each ONE change vs g3b)
#   5  if both PASS: g4ar combined regen -> merge+gates -> grid+arbitration
#      -> EVAL #22
# Run: nohup bash run_night_chain.sh > run_night_chain.log 2>&1 &
set -e
EC=/home/user/nurkyz/einstein_cnn
TI=/home/user/nurkyz/cosmos_acs/tiles

abort () { echo "NIGHT_ABORT: $1  $(date)"; exit 1; }

pilot_gates_ok () {  # $1 = pilot .out file
    grep -q "FJ gate: .*PASS" "$1" || return 1
    [ "$(grep -c '\[PASS' "$1")" -ge 3 ] || return 1
    return 0
}

echo "STAGE 0: waiting for the AB chain  $(date)"
for i in $(seq 1 600); do
    grep -q AB_CHAIN_ABORT "$EC/run_ab_chain.log" 2>/dev/null && abort "AB chain aborted — touching nothing"
    grep -q AB_CHAIN_ALL_DONE "$EC/run_ab_chain.log" 2>/dev/null && break
    sleep 60
done
grep -q AB_CHAIN_ALL_DONE "$EC/run_ab_chain.log" || abort "timeout on AB chain"
for i in $(seq 1 60); do
    [ "$(squeue -u nurkyz -h | wc -l)" -eq 0 ] && break
    sleep 30
done

echo "STAGE 1: banking AB results  $(date)"
BANK=/home/user/nurkyz/night_bank
mkdir -p "$BANK"
cp -p "$EC"/slurm_l20_eval_*.out "$EC"/slurm_l21_eval_*.out "$BANK"/ 2>/dev/null || true
cp -p "$EC"/g3b_recal.json "$EC"/g4n_recal.json "$EC"/run_ab_chain.log "$BANK"/ 2>/dev/null || true
cp -p "$EC"/slurm_g3b_arbitrate_*.out "$EC"/slurm_g4n_arbitrate_*.out "$BANK"/ 2>/dev/null || true
cp -p "$TI"/merge_gate_g4native.out "$TI"/merge_gate_g3b.out "$BANK"/ 2>/dev/null || true
ls "$BANK" | wc -l

echo "STAGE 2: cleanup (approved list ONLY)  $(date)"
quota -s 2>/dev/null | tail -1
rm -f "$EC/train_euclid_sel_100k.h5" "$EC/train_euclid_100k_v3.h5" \
      "$EC/train_hybrid_100k_v3.h5" "$EC/train_hybrid_100k_pathb_v2.h5"
rm -rf /home/user/nurkyz/paltas_g2_pilot /home/user/nurkyz/paltas_g2_pilot_euclid \
       /home/user/nurkyz/paltas_g3_pilot /home/user/nurkyz/paltas_g3_pilot_euclid
rm -f "$EC"/g2_pilot_*.h5 "$EC"/g3_pilot_*.h5
quota -s 2>/dev/null | tail -1

echo "STAGE 3: G1b phase-1 fetch (login node, parallel)  $(date)"
cd "$EC"
nohup bash g1b_fetch_driver.sh > g1b_fetch.log 2>&1 &

echo "STAGE 4a: AR1 pilot  $(date)"
cd "$TI"
sbatch --wait ar1_pilot.sbatch || true
grep -q AR1_PILOT_DONE "$TI/ar1_pilot.out" || abort "AR1 pilot crashed"
pilot_gates_ok "$TI/ar1_pilot.out" || abort "AR1 pilot gates FAIL — stopping before any regen"
echo "AR1 gates PASS"

echo "STAGE 4b: AR2 pilot  $(date)"
sbatch --wait ar2_pilot.sbatch || true
grep -q AR2_PILOT_DONE "$TI/ar2_pilot.out" || abort "AR2 pilot crashed"
pilot_gates_ok "$TI/ar2_pilot.out" || abort "AR2 pilot gates FAIL — stopping before any regen"
echo "AR2 gates PASS"

echo "STAGE 5: g4ar combined regeneration  $(date)"
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

echo "NIGHT_CHAIN_ALL_DONE  $(date)"
quota -s 2>/dev/null | tail -1
