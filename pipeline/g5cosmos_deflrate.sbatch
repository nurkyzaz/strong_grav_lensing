#!/bin/bash
#SBATCH --job-name=g5cos_dr
#SBATCH --partition=normal
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=02:00:00
#SBATCH --output=/home/user/nurkyz/cosmos_acs/tiles/g5cosmos_deflrate.out
# LOCKED source = COSMOS SB cut 22.5 (Nurkyz). Render 120, then re-combine at
# 3 deflector-sharpen levels (0 / 1.5 / 3.0) for Nurkyz to EYEBALL + rate the
# deflector. Cheap re-combines after one render.
set -e
set -o pipefail
PY=/home/user/nurkyz/miniconda3/envs/Stronglensing/bin/python
TILES=/home/user/nurkyz/cosmos_acs/tiles
EC=/home/user/nurkyz/einstein_cnn
P=/home/user/nurkyz/paltas_g5cosmos_deflrate
M=/home/user/nurkyz/paltas_g5_c21_pilot/manifest_pilot.csv
Q1REAL=/home/user/nurkyz/cosmos_acs/q1_slde/q1_slde_eval_f2p85_zoom.h5
mkdir -p "$P"
cd "$TILES"
export LF_PSF_KERNEL=psf_bank_v2/kernel_00_extended.npy
export LF_G2_MANIFEST="$M"
export LF_SB_CUT=22.5
export LF_SRC_MAG_MED=22.7
$PY run_paltas_pilot.py config_lensfusion_acs_g5cosmos.py "$P/sub" --n 120 --seed 951
$PY g2_join_assign.py "$P/sub" "$M" "$P/assign.csv"

combine_sharp () {
  SH=$1; ST=$2
  cd "$TILES"
  $PY hybrid_combine.py --run "$P/sub" --empty empty_cutouts_expanded_screened.h5 \
      --real "$EC/real_dapool_images.h5" \
      --out "$P/native_${ST}.h5" --seed 952 \
      --deflector_stamps deflector_stamps_lrg2b_raw.h5 \
      --deflector_manifest "$P/assign.csv" --deflector_jitter 1.0 \
      --deflector_sharpen "$SH" --deflector_sharpen_sigma 1.5 \
      --companion_stamps source_stamps_clean.h5 \
      --companion_rate_lo 2 --companion_rate_hi 9 --companion_flux_pct 35 --arc_poisson
  cd "$EC"; export LF_EUC_SKY_SCALE=2.2
  $PY euclidise.py --inp "$P/native_${ST}.h5" --out "$P/euclid_${ST}.h5" --seed 955
}
combine_sharp 0    s0
combine_sharp 1.5  s15
combine_sharp 3.0  s30
echo "G5COSMOS_DEFLRATE_DONE"
