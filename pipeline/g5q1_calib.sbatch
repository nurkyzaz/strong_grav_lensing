#!/bin/bash
#SBATCH --job-name=g5q1_calib
#SBATCH --partition=normal
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=02:00:00
#SBATCH --output=/home/user/nurkyz/cosmos_acs/tiles/g5q1_calib.out
# GEN5 C37 calibration sweep: real Q1 sources gave bright but OVERSHOT arcs
# (too thick/bright). Sweep arc THICKNESS (LF_Q1_PIXSCALE, needs re-render) x
# BRIGHTNESS (hybrid_combine --arc_flux_scale, cheap at combine). Target real
# AR0 arc_width ~6px, arc_contrast ~7.75. 48 renders per pixscale.
set -e
set -o pipefail
PY=/home/user/nurkyz/miniconda3/envs/Stronglensing/bin/python
TILES=/home/user/nurkyz/cosmos_acs/tiles
EC=/home/user/nurkyz/einstein_cnn
BASE=/home/user/nurkyz/paltas_g5q1_calib
M=/home/user/nurkyz/paltas_g5_c21_pilot/manifest_pilot.csv
Q1REAL=/home/user/nurkyz/cosmos_acs/q1_slde/q1_slde_eval_f2p85_zoom.h5
mkdir -p "$BASE"
export LF_PSF_KERNEL=psf_bank_v2/kernel_00_extended.npy
export LF_G2_MANIFEST="$M"
export LF_Q1_SRC=/home/user/nurkyz/cosmos_acs/q1_slde/q1_sources_smooth.h5

render_pix () {
  PIX=$1; PT=$2
  echo "########## RENDER pixscale $PIX ($PT) ##########"
  cd "$TILES"
  export LF_Q1_PIXSCALE="$PIX"
  $PY run_paltas_pilot.py config_lensfusion_acs_g5q1.py "$BASE/sub_$PT" --n 48 --seed 951
  $PY g2_join_assign.py "$BASE/sub_$PT" "$M" "$BASE/assign_$PT.csv"
}

combine_scale () {
  PT=$1; S=$2; ST=$3
  cd "$TILES"
  $PY hybrid_combine.py --run "$BASE/sub_$PT" --empty empty_cutouts_expanded_screened.h5 \
      --real "$EC/real_dapool_images.h5" \
      --out "$BASE/native_${PT}_${ST}.h5" --seed 952 \
      --deflector_stamps deflector_stamps_lrg2b_raw.h5 \
      --deflector_manifest "$BASE/assign_$PT.csv" --deflector_jitter 1.0 \
      --companion_stamps source_stamps_clean.h5 \
      --companion_rate_lo 2 --companion_rate_hi 9 --companion_flux_pct 35 \
      --arc_poisson --arc_flux_scale "$S"
  cd "$EC"; export LF_EUC_SKY_SCALE=2.2
  $PY euclidise.py --inp "$BASE/native_${PT}_${ST}.h5" --out "$BASE/euclid_${PT}_${ST}.h5" --seed 955
  cd "$TILES"
  echo "===== AR0 gate  pixscale=$PT  arc_flux_scale=$S  [target width~6 contrast~7.75] ====="
  $PY ar0_arc_gate.py --sim "$BASE/euclid_${PT}_${ST}.h5" --real "$Q1REAL" --n 48 --tag q1_${PT}_${ST} || echo AR0_NZ
  $PY side_by_side_real_sim.py --real "$Q1REAL" --sim "$BASE/euclid_${PT}_${ST}.h5" \
      --n 8 --seed 5 --out "$BASE/sbs_${PT}_${ST}.png"
}

for spec in "0.02 p02" "0.03 p03" "0.04 p04"; do
  set -- $spec; render_pix "$1" "$2"
  combine_scale "$2" 1.0 s10
  combine_scale "$2" 0.5 s05
done
echo "G5Q1_CALIB_DONE"
