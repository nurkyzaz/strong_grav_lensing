#!/bin/bash
#SBATCH --job-name=g5_p1comp
#SBATCH --partition=normal
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=01:00:00
#SBATCH --output=/home/user/nurkyz/cosmos_acs/tiles/g5_phase1_companion.out
# GEN5 Phase 1 — FIRM FIX #1: cut the companion injection rate.
# Phase 0 measured GEN5 v4 field companions ~4x too many in the tail (real med 2
# / frac>4 8% vs GEN5 med 3 / 33%); a same-estimator diagnostic showed detected
# field companions scale with the INJECTED rate (injected[0,6)->1.55 detected,
# [20,40)->4.81), i.e. injection is the driver, not the backdrop. v4 used
# --companion_rate_lo 8 --companion_rate_hi 26. Here we bracket the real target:
#   v5a: rate 2-9  (predict detected ~2.0 = real median)
#   v5b: rate 0-5  (predict detected ~1.5 = lower bound)
# REUSES the v4 paltas renders (sub_pilot, 200) + the same manifest (assign_pilot)
# -> deflectors/arcs are IDENTICAL to v4; only companions change. No GPU re-render.
# One knob changed (companion rate). evo_q / deflector-dominance is a SEPARATE
# next pilot per "one config change -> one pilot -> gates".
set -e
set -o pipefail
PY=/home/user/nurkyz/miniconda3/envs/Stronglensing/bin/python
TILES=/home/user/nurkyz/cosmos_acs/tiles
EC=/home/user/nurkyz/einstein_cnn
P=/home/user/nurkyz/paltas_g5_c21_pilot
Q1REAL=/home/user/nurkyz/cosmos_acs/q1_slde/q1_slde_eval_f2p85_zoom.h5
# NB script locations: hybrid_combine/gate_stage0/ar0_arc_gate live in $TILES;
# euclidise/euclidise_arcs/arc_visibility_select live in $EC.
export LF_EUC_SKY_SCALE=2.2

# arc images for the visibility selection (sub_pilot only -> once, reused)
cd "$EC"
$PY euclidise_arcs.py "$P/sub_pilot" "$P/sub_pilot_euclid_arcs"

run_variant () {
  TAG=$1; LO=$2; HI=$3
  echo "=== variant $TAG: companion_rate ${LO}-${HI} ==="
  cd "$TILES"
  $PY hybrid_combine.py --run "$P/sub_pilot" --empty empty_cutouts_expanded_screened.h5 \
      --real "$EC/real_dapool_images.h5" \
      --out "$P/native_p1${TAG}.h5" --seed 952 \
      --deflector_stamps deflector_stamps_lrg2b_raw.h5 \
      --deflector_manifest "$P/assign_pilot.csv" --deflector_jitter 1.0 \
      --companion_stamps source_stamps_clean.h5 \
      --companion_rate_lo "$LO" --companion_rate_hi "$HI" --companion_flux_pct 35 \
      --arc_poisson
  cd "$EC"
  $PY euclidise.py --inp "$P/native_p1${TAG}.h5" --out "$P/euclid_p1${TAG}.h5" --seed 955
  $PY arc_visibility_select.py --arcs "$P/sub_pilot_euclid_arcs" \
      --sim "$P/euclid_p1${TAG}.h5" --out "$P/euclid_p1${TAG}_sel.h5" \
      --thresh 0.8 --min_extent 150
  cd "$TILES"
  echo "--- stage0 gate (variant $TAG) vs real Q1 ---"
  $PY gate_stage0.py --sim "$P/euclid_p1${TAG}.h5" --real "$Q1REAL" \
      --csv failure_features_slacs.csv --meta "$P/sub_pilot/metadata.csv" \
      --out "$P/gate_q1_p1${TAG}.png" || echo "GATE_Q1_NONZERO (read numbers)"
  echo "--- AR0 arc gate (variant $TAG) ---"
  $PY ar0_arc_gate.py --sim "$P/euclid_p1${TAG}.h5" --real "$Q1REAL" \
      --n 200 --tag g5_p1${TAG} || echo "AR0_NONZERO (read numbers)"
}

run_variant a 2 9
run_variant b 0 5
echo "GEN5_PHASE1_COMPANION_DONE"
