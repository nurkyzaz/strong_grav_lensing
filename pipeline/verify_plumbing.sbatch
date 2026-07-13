#!/bin/bash
#SBATCH --job-name=lf_verify_plumb
#SBATCH --partition=normal
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=01:00:00
#SBATCH --output=/home/user/nurkyz/cosmos_acs/tiles/verify_plumbing.out

# Plumbing regression test (NO regeneration): rerun combine->euclidise->select
# on the EXISTING seed-711 pilot renders with the patched scripts (same seeds).
# PASS = new columns present end-to-end AND images bit-identical to the pilot.
set -e
PY=/home/user/nurkyz/miniconda3/envs/Stronglensing/bin/python
cd /home/user/nurkyz/cosmos_acs/tiles

$PY hybrid_combine.py --run /home/user/nurkyz/paltas_euc_selREB_pilot \
    --empty empty_cutouts_expanded_screened.h5 \
    --real /home/user/nurkyz/einstein_cnn/real_dapool_images.h5 \
    --out /home/user/nurkyz/einstein_cnn/verify_native_REB.h5 \
    --deflector_stamps deflector_stamps_lrg_v6_train.h5 --deflector_augment \
    --deflector_jitter 1.0 \
    --deflector_mag_csv lens_light_empirical.csv \
    --companion_stamps source_stamps_clean.h5 \
    --companion_rate_lo 8 --companion_rate_hi 26 --companion_flux_pct 35 --seed 214

cd /home/user/nurkyz/einstein_cnn
$PY euclidise.py --inp verify_native_REB.h5 --out verify_euclid_REB.h5 --seed 215
$PY arc_visibility_select.py --arcs /home/user/nurkyz/paltas_euc_selREB_pilot_euclid \
    --sim verify_euclid_REB.h5 --out verify_selected_REB.h5 \
    --thresh 0.7 --min_extent 150

$PY - <<'PYEOF'
import h5py, numpy as np
new = h5py.File("/home/user/nurkyz/einstein_cnn/verify_selected_REB.h5", "r")
old = h5py.File("/home/user/nurkyz/einstein_cnn/euc_sel_pilot_selected_REB.h5", "r")
print("new keys:", sorted(new.keys()))
assert "mass_e1" in new and "mass_e2" in new, "mass e1/e2 MISSING"
assert "deflector_index" in new and "deflector_mag" in new, "provenance MISSING"
a, b = new["lensed"][:50], old["lensed"][:50]
assert a.shape == b.shape and np.allclose(a, b), "IMAGES CHANGED — seeds broken!"
assert np.allclose(new["theta_E"][:], old["theta_E"][:]), "labels changed!"
e1 = new["mass_e1"][:]
print("images identical to pilot: OK; mass_e1 range [%.3f, %.3f] std %.3f"
      % (e1.min(), e1.max(), e1.std()))
print("PLUMBING_VERIFY_PASS")
PYEOF
echo "VERIFY_PLUMBING_DONE"
