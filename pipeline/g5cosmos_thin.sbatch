#!/bin/bash
#SBATCH --job-name=g5cos_thin
#SBATCH --partition=normal
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=02:30:00
#SBATCH --output=/home/user/nurkyz/cosmos_acs/tiles/g5cosmos_thin.out
# GEN5-COSMOS: Nurkyz "arcs too thick + bright". Fainter source mag (24, was 22.7)
# + tighter SB cut (more compact source -> thinner arc). Sweep SB cut
# {20.5,21.5,22.5} at src_mag 24, deflector_sharpen 1.5. 60 renders/cut.
set -e
set -o pipefail
PY=/home/user/nurkyz/miniconda3/envs/Stronglensing/bin/python
TILES=/home/user/nurkyz/cosmos_acs/tiles
EC=/home/user/nurkyz/einstein_cnn
BASE=/home/user/nurkyz/paltas_g5cosmos_thin
M=/home/user/nurkyz/paltas_g5_c21_pilot/manifest_pilot.csv
Q1REAL=/home/user/nurkyz/cosmos_acs/q1_slde/q1_slde_eval_f2p85_zoom.h5
mkdir -p "$BASE"
export LF_PSF_KERNEL=psf_bank_v2/kernel_00_extended.npy
export LF_G2_MANIFEST="$M"
export LF_SRC_MAG_MED=24.0

run_cut () {
  CUT=$1; CT=$2
  echo "########## SB cut $CUT src_mag 24 ($CT) ##########"
  cd "$TILES"; export LF_SB_CUT="$CUT"
  $PY run_paltas_pilot.py config_lensfusion_acs_g5cosmos.py "$BASE/sub_$CT" --n 60 --seed 951
  $PY g2_join_assign.py "$BASE/sub_$CT" "$M" "$BASE/assign_$CT.csv"
  $PY hybrid_combine.py --run "$BASE/sub_$CT" --empty empty_cutouts_expanded_screened.h5 \
      --real "$EC/real_dapool_images.h5" \
      --out "$BASE/native_$CT.h5" --seed 952 \
      --deflector_stamps deflector_stamps_lrg2b_raw.h5 \
      --deflector_manifest "$BASE/assign_$CT.csv" --deflector_jitter 1.0 \
      --deflector_sharpen 1.5 --deflector_sharpen_sigma 1.5 \
      --companion_stamps source_stamps_clean.h5 \
      --companion_rate_lo 2 --companion_rate_hi 9 --companion_flux_pct 35 --arc_poisson
  cd "$EC"; export LF_EUC_SKY_SCALE=2.2
  $PY euclidise.py --inp "$BASE/native_$CT.h5" --out "$BASE/euclid_$CT.h5" --seed 955
  cd "$TILES"
  echo "===== AR0 (cut $CUT, mag 24) vs real [contrast~7.75 width~6] ====="
  $PY ar0_arc_gate.py --sim "$BASE/euclid_$CT.h5" --real "$Q1REAL" --n 60 --tag thin_$CT || echo AR0_NZ
  $PY side_by_side_real_sim.py --real "$Q1REAL" --sim "$BASE/euclid_$CT.h5" \
      --n 8 --seed 5 --out "$BASE/sbs_thin_$CT.png"
}
run_cut 20.5 c205
run_cut 21.5 c215
run_cut 22.5 c225
echo "G5COSMOS_THIN_DONE"
