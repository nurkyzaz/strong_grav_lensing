#!/bin/bash
#SBATCH --job-name=g5rom_pilot
#SBATCH --partition=normal
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=2
#SBATCH --mem=8G
#SBATCH --time=02:00:00
#SBATCH --output=/home/user/nurkyz/cosmos_acs/tiles/slurm_g5rom_pilot_%j.out

# G5c PATH-B PILOT (standing rule: one config change -> 200-image pilot ->
# gates -> only then scale). Chain: extended-support manifest (C10 sidecar)
# -> native render (same GEN4/g4ar recipe) -> romanise -> stats gate vs the
# measured Rung 0 targets (sky 0.454, skyRMS 0.0205, peak/sky 7/32/149) +
# three-stretch previews. NO full generation from this job.
set -e
PY=/home/user/nurkyz/miniconda3/envs/Stronglensing/bin/python
TILES=/home/user/nurkyz/cosmos_acs/tiles
EC=/home/user/nurkyz/einstein_cnn
P=/home/user/nurkyz/paltas_g5rom_pilot
mkdir -p "$P"
cd "$TILES"

$PY build_acs2roman_kernel.py

$PY g2_make_manifest.py --kine g4_kine_train.csv --n 240 --seed 20260715 \
    --tmin 0.15 --tmax 3.70 --couple_shear --out "$P/manifest_pilot.csv"

export LF_PSF_KERNEL=psf_bank_v2/kernel_00_extended.npy
export LF_G2_MANIFEST="$P/manifest_pilot.csv"
$PY run_paltas_pilot.py config_lensfusion_acs_g2.py "$P/sub_pilot" --n 200 --seed 20260716
$PY g2_join_assign.py "$P/sub_pilot" "$P/manifest_pilot.csv" "$P/assign_pilot.csv"
$PY hybrid_combine.py --run "$P/sub_pilot" --empty empty_cutouts_expanded_screened.h5 \
    --real "$EC/real_dapool_images.h5" \
    --out "$P/native_pilot.h5" --seed 20260717 \
    --deflector_stamps deflector_stamps_g4_all.h5 \
    --deflector_manifest "$P/assign_pilot.csv" --deflector_jitter 1.0 \
    --companion_stamps source_stamps_clean.h5 \
    --companion_rate_lo 8 --companion_rate_hi 26 --companion_flux_pct 35 --arc_poisson

$PY romanise.py --inp "$P/native_pilot.h5" --out "$P/roman_pilot.h5" --seed 20260718
$PY g5rom_pilot_gate.py
echo G5ROM_PILOT_DONE
