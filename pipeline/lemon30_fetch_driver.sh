#!/bin/bash
# Q1b full 30-lens MAST fetch (12 EEL + 5 COSMOS + 13 ACS/Pawase), pilot-3
# already passed all sanity previews. Same box/npix as the SLACS benchmark.
set -e
PY=/home/user/nurkyz/miniconda3/envs/Stronglensing/bin/python
cd /home/user/nurkyz/einstein_cnn
$PY fetch_real_lens_images.py --labels lemon30_labels.csv --survey LEMONEEL \
    --box 6.4 --npix 128 --cache mast_cache_lemon30 --out real_LEMONEEL_images.h5
echo EEL_DONE
$PY fetch_real_lens_images.py --labels lemon30_labels.csv --survey LEMONCOSMOS \
    --box 6.4 --npix 128 --cache mast_cache_lemon30 --out real_LEMONCOSMOS_images.h5
echo COSMOS_DONE
$PY fetch_real_lens_images.py --labels lemon30_labels.csv --survey LEMONACS \
    --box 6.4 --npix 128 --cache mast_cache_lemon30 --out real_LEMONACS_images.h5
echo ACS_DONE
echo LEMON30_FETCH_ALL_DONE
