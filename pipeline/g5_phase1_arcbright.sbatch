#!/bin/bash
#SBATCH --job-name=g5_p1arc
#SBATCH --partition=normal
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=01:30:00
#SBATCH --output=/home/user/nurkyz/cosmos_acs/tiles/g5_phase1_arcbright.out
# GEN5 Phase 1 C36 — ARC-BRIGHTNESS batch. The source is over-dimmed (no LF
# evolution) -> arcs faint/invisible (AR0 contrast 2.8 vs real 7.75). hybrid_combine
# --arc_flux_scale multiplies the NOISELESS lensed source before Poisson+combine =
# physically brightening the source (arc SB linear in source flux). Re-combine only,
# NO GPU re-render. Companion rate fixed at the variant-a winner (2-9). Test 3 levels
# to bracket real arc contrast; AR0 gate + side-by-side per level for the eyeball.
set -e
set -o pipefail
PY=/home/user/nurkyz/miniconda3/envs/Stronglensing/bin/python
TILES=/home/user/nurkyz/cosmos_acs/tiles
EC=/home/user/nurkyz/einstein_cnn
P=/home/user/nurkyz/paltas_g5_c21_pilot
Q1REAL=/home/user/nurkyz/cosmos_acs/q1_slde/q1_slde_eval_f2p85_zoom.h5
export LF_EUC_SKY_SCALE=2.2

cd "$EC"
$PY euclidise_arcs.py "$P/sub_pilot" "$P/sub_pilot_euclid_arcs"

run_scale () {
  TAG=$1; S=$2
  echo "############ arc_flux_scale = $S (tag $TAG) ############"
  cd "$TILES"
  $PY hybrid_combine.py --run "$P/sub_pilot" --empty empty_cutouts_expanded_screened.h5 \
      --real "$EC/real_dapool_images.h5" \
      --out "$P/native_ab${TAG}.h5" --seed 952 \
      --deflector_stamps deflector_stamps_lrg2b_raw.h5 \
      --deflector_manifest "$P/assign_pilot.csv" --deflector_jitter 1.0 \
      --companion_stamps source_stamps_clean.h5 \
      --companion_rate_lo 2 --companion_rate_hi 9 --companion_flux_pct 35 \
      --arc_poisson --arc_flux_scale "$S"
  cd "$EC"
  $PY euclidise.py --inp "$P/native_ab${TAG}.h5" --out "$P/euclid_ab${TAG}.h5" --seed 955
  $PY arc_visibility_select.py --arcs "$P/sub_pilot_euclid_arcs" \
      --sim "$P/euclid_ab${TAG}.h5" --out "$P/euclid_ab${TAG}_sel.h5" \
      --thresh 0.8 --min_extent 150 || echo "SELECT_NOTE"
  cd "$TILES"
  echo "--- AR0 arc gate (scale $S) vs real Q1 [target arc_contrast ~7.75] ---"
  $PY ar0_arc_gate.py --sim "$P/euclid_ab${TAG}.h5" --real "$Q1REAL" \
      --n 200 --tag g5_ab${TAG} || echo "AR0_NONZERO (read numbers)"
  $PY side_by_side_real_sim.py --real "$Q1REAL" --sim "$P/euclid_ab${TAG}.h5" \
      --n 8 --seed 5 --out "$P/real_vs_sim_ab${TAG}.png"
}

run_scale 2 2.0
run_scale 3 3.0
run_scale 5 5.0
echo "GEN5_PHASE1_ARCBRIGHT_DONE"
