#!/bin/bash
#SBATCH --job-name=lf_pathb_pilot5
#SBATCH --partition=normal
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=03:00:00
#SBATCH --output=/home/user/nurkyz/cosmos_acs/tiles/pathb_pilot_v5.out

# PATH B pilot v5 (2026-07-09, P2): ONLY change vs pilot v4b = deflector
# library v6 (deflector_stamps_lrg_v6.h5) from the 256px/12.8" LRG refetch:
# corner background is TRUE sky (r~180px) so the de Vauc wings survive
# subtraction; combine pastes the CENTRE 128px crop -> the visible frame sits
# entirely inside real galaxy light (no edge possible by construction).
# 49 stamps after visual prune on the central-crop preview (drop list grew:
# 256px data reveals central spirals/edge-on disks/mergers that the 128px
# over-subtraction had hidden). Aperture-mag scaling (P1b) unchanged.
set -e
PY=/home/user/nurkyz/miniconda3/envs/Stronglensing/bin/python
cd /home/user/nurkyz/cosmos_acs/tiles

echo "[1/6] generate 200 ARC-ONLY images (seed 111, identical to pilots v3/v4/v4b) ..."
export LF_PSF_KERNEL=psf_bank_v2/kernel_00_extended.npy
$PY run_paltas_pilot.py config_lensfusion_acs_pathb_nonoise.py \
    /home/user/nurkyz/paltas_pathb_pilot_v5 --n 200 --seed 111

echo "[2/6] combine: APERTURE-mag-scaled real LRG deflector + companions + backdrop + noise ..."
$PY hybrid_combine.py --run /home/user/nurkyz/paltas_pathb_pilot_v5 \
    --empty empty_cutouts_4k.h5 \
    --real /home/user/nurkyz/einstein_cnn/real_slacs_images.h5 \
    --out /home/user/nurkyz/einstein_cnn/pathb_pilot_v5.h5 \
    --deflector_stamps deflector_stamps_lrg_v6.h5 --deflector_mag_csv lens_light_empirical.csv \
    --companion_stamps source_stamps_clean.h5 \
    --companion_rate_lo 8 --companion_rate_hi 26 --companion_flux_pct 35 --seed 112

echo "[3/6] three-stretch preview ..."
$PY preview_three_stretch.py /home/user/nurkyz/einstein_cnn/pathb_pilot_v5.h5 --n 16

echo "[4/6] realism gate ..."
$PY gate_stage0.py --sim /home/user/nurkyz/einstein_cnn/pathb_pilot_v5.h5 \
    --real /home/user/nurkyz/einstein_cnn/real_slacs_images.h5 \
    --csv failure_features_slacs.csv \
    --meta /home/user/nurkyz/paltas_pathb_pilot_v5/metadata.csv \
    --out gate_pathb_pilot_v5.png

echo "[5/6] real-vs-sim side-by-side ..."
$PY side_by_side_real_sim.py --real /home/user/nurkyz/einstein_cnn/real_slacs_images.h5 \
    --sim /home/user/nurkyz/einstein_cnn/pathb_pilot_v5.h5 --n 8 --seed 5 \
    --out real_vs_pathb_pilot_v5run.png

echo "[6/6] radial profile compare (shape + absolute brightness) ..."
$PY radial_profile_compare.py --sim /home/user/nurkyz/einstein_cnn/pathb_pilot_v5.h5 \
    --lib deflector_stamps_lrg_v6.h5 --label "SIM pilot v5" \
    --out /home/user/nurkyz/cosmos_acs/tiles/radial_profile_v5.png

rm -f /home/user/nurkyz/paltas_pathb_pilot_v5/image_*.npy
echo "PATHB_PILOT_V5_DONE"
