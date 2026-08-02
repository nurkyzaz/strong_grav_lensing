#!/bin/bash
#SBATCH --job-name=g5q1_dsharp
#SBATCH --partition=normal
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=01:00:00
#SBATCH --output=/home/user/nurkyz/cosmos_acs/tiles/g5q1_deflsharpen.out
# GEN5-Q1 TRACK B: deflector too soft-cored (peak/sky 60 vs real 172; double-PSF).
# Sweep --deflector_sharpen (unsharp mask on the deflector stamp) to raise the
# central peak. RE-COMBINES the existing g5q1_pilot renders (no re-render).
# Keeps the calibrated arc recipe (arc_flux_scale 0.5, companion 2-9, sky 2.2).
set -e
set -o pipefail
PY=/home/user/nurkyz/miniconda3/envs/Stronglensing/bin/python
TILES=/home/user/nurkyz/cosmos_acs/tiles
EC=/home/user/nurkyz/einstein_cnn
P=/home/user/nurkyz/paltas_g5q1_pilot
Q1REAL=/home/user/nurkyz/cosmos_acs/q1_slde/q1_slde_eval_f2p85_zoom.h5
export LF_EUC_SKY_SCALE=2.2

run_sharp () {
  SH=$1; ST=$2
  echo "########## deflector_sharpen $SH ($ST) ##########"
  cd "$TILES"
  $PY hybrid_combine.py --run "$P/sub" --empty empty_cutouts_expanded_screened.h5 \
      --real "$EC/real_dapool_images.h5" \
      --out "$P/native_ds${ST}.h5" --seed 952 \
      --deflector_stamps deflector_stamps_lrg2b_raw.h5 \
      --deflector_manifest "$P/assign.csv" --deflector_jitter 1.0 \
      --deflector_sharpen "$SH" --deflector_sharpen_sigma 1.5 \
      --companion_stamps source_stamps_clean.h5 \
      --companion_rate_lo 2 --companion_rate_hi 9 --companion_flux_pct 35 \
      --arc_poisson --arc_flux_scale 0.5
  cd "$EC"
  $PY euclidise.py --inp "$P/native_ds${ST}.h5" --out "$P/euclid_ds${ST}.h5" --seed 955
  cd "$TILES"
  echo "--- stage0 (sharpen $SH) [deflector peak/sky target real 103-727] ---"
  $PY gate_stage0.py --sim "$P/euclid_ds${ST}.h5" --real "$Q1REAL" \
      --csv failure_features_slacs.csv --meta "$P/sub/metadata.csv" \
      --out "$P/gate_ds${ST}.png" || echo GATE_NZ
  $PY side_by_side_real_sim.py --real "$Q1REAL" --sim "$P/euclid_ds${ST}.h5" \
      --n 8 --seed 5 --out "$P/sbs_ds${ST}.png"
}

run_sharp 0.6 06
run_sharp 1.2 12
run_sharp 2.0 20
echo "G5Q1_DEFLSHARPEN_DONE"
