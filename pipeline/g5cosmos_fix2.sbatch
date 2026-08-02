#!/bin/bash
#SBATCH --job-name=g5cos_fx2
#SBATCH --partition=normal
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=02:00:00
#SBATCH --output=/home/user/nurkyz/cosmos_acs/tiles/g5cosmos_fix2.out
# GEN5-COSMOS FIX ROUND 2 (Nurkyz eyeball 2026-08-02):
#  - arcs brighter ~0.7 mag: LF_SRC_ABSMAG -24.0 -> -24.5 (apparent ~23.7-24.0)
#  - companions: rmin 18->30 px + NEW --companion_area_uniform (uniform per AREA,
#    edges-heavy like real; legacy uniform-in-r piled them onto the arc)
#  - background: LF_EUC_NOISE_CORR=0.6 (drizzle-correlated noise, same RMS;
#    real neighbor-corr 0.758 vs our white 0.697)
#  - deflector: sharpen sweep {0.5, 1.0} (1.5 over-compact vs real diffuse+bright)
set -e
set -o pipefail
PY=/home/user/nurkyz/miniconda3/envs/Stronglensing/bin/python
TILES=/home/user/nurkyz/cosmos_acs/tiles
EC=/home/user/nurkyz/einstein_cnn
P=/home/user/nurkyz/paltas_g5cosmos_fix2
M=/home/user/nurkyz/paltas_g5_c21_pilot/manifest_pilot.csv
Q1REAL=/home/user/nurkyz/cosmos_acs/q1_slde/q1_slde_eval_f2p85_zoom.h5
mkdir -p "$P"
cd "$TILES"
export LF_PSF_KERNEL=psf_bank_v2/kernel_00_extended.npy
export LF_G2_MANIFEST="$M"
export LF_SB_CUT=21.5
export LF_SRC_ABSMAG=-24.5
export LF_MIN_FLUX_RADIUS=1.0
export LF_MIN_SIZE_PX=8
$PY run_paltas_pilot.py config_lensfusion_acs_g5cosmos.py "$P/sub" --n 120 --seed 951
$PY g2_join_assign.py "$P/sub" "$M" "$P/assign.csv"

variant () {
  SH=$1; ST=$2
  echo "########## sharpen $SH ($ST) + companion fix + corr noise ##########"
  cd "$TILES"
  $PY hybrid_combine.py --run "$P/sub" --empty empty_cutouts_expanded_screened.h5 \
      --real "$EC/real_dapool_images.h5" \
      --out "$P/native_$ST.h5" --seed 952 \
      --deflector_stamps deflector_stamps_lrg2b_raw.h5 \
      --deflector_manifest "$P/assign.csv" --deflector_jitter 1.0 \
      --deflector_sharpen "$SH" --deflector_sharpen_sigma 1.5 \
      --companion_stamps source_stamps_clean.h5 \
      --companion_rate_lo 2 --companion_rate_hi 9 --companion_flux_pct 35 \
      --companion_rmin 30 --companion_area_uniform --arc_poisson
  cd "$EC"; export LF_EUC_SKY_SCALE=2.2; export LF_EUC_NOISE_CORR=0.6
  $PY euclidise.py --inp "$P/native_$ST.h5" --out "$P/euclid_$ST.h5" --seed 955
  cd "$TILES"
  echo "--- gates (sharpen $SH) ---"
  $PY gate_stage0.py --sim "$P/euclid_$ST.h5" --real "$Q1REAL" --csv failure_features_slacs.csv \
      --meta "$P/sub/metadata.csv" --out "$P/gate_$ST.png" || echo GATE_NZ
  $PY ar0_arc_gate.py --sim "$P/euclid_$ST.h5" --real "$Q1REAL" --n 120 --tag fx2_$ST || echo AR0_NZ
  $PY side_by_side_real_sim.py --real "$Q1REAL" --sim "$P/euclid_$ST.h5" --n 8 --seed 5 \
      --out "$P/sbs_$ST.png"
}
variant 0.5 s05
variant 1.0 s10
echo "G5COSMOS_FIX2_DONE"
