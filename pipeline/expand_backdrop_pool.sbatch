#!/bin/bash
#SBATCH --job-name=lf_pool
#SBATCH --partition=normal
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=24G
#SBATCH --time=03:00:00
#SBATCH --output=/home/user/nurkyz/cosmos_acs/tiles/expand_backdrop_pool.out

# Q5 (2026-07-09): harvest empty cutouts from the NEW tiles 066+074 only
# (symlinked subdir; tile 073 already harvested), gradient-screen the new
# harvest at the real-95% threshold (2.85, same as screen_empty_pool.py),
# and concatenate with the existing screened pool -> expanded pool for the
# Euclid-arm full run (backdrop reuse drops ~3x).
set -e
PY=/home/user/nurkyz/miniconda3/envs/Stronglensing/bin/python
cd /home/user/nurkyz/cosmos_acs/tiles

echo "[1/3] harvest new tiles ..."
mkdir -p tiles_new_066_074
ln -sf ~/cosmos_acs/tiles/acs_I_030mas_066_sci.fits tiles_new_066_074/
ln -sf ~/cosmos_acs/tiles/acs_I_030mas_066_wht.fits tiles_new_066_074/
ln -sf ~/cosmos_acs/tiles/acs_I_030mas_074_sci.fits tiles_new_066_074/
ln -sf ~/cosmos_acs/tiles/acs_I_030mas_074_wht.fits tiles_new_066_074/
$PY harvest_empty_cutouts.py --tiles_dir tiles_new_066_074 \
    --out empty_cutouts_new066074.h5 --n 3000 --seed 42

echo "[2/3] gradient-screen the new harvest + concat with existing screened pool ..."
$PY screen_and_concat_pools.py

echo "[3/3] summary ..."
$PY -c "import h5py; f=h5py.File('empty_cutouts_expanded_screened.h5','r'); print('expanded pool:', f['empty'].shape); f.close()"
echo "POOL_EXPAND_DONE"
