#!/bin/bash
# Download 2 additional COSMOS ACS mosaic tiles (071, 072) for a larger
# empty-cutout harvest (backdrop-reuse reduction, next dataset iteration).
# Resumable (wget -c); deletes the .gz after unpack to spare quota.
cd /home/user/nurkyz/cosmos_acs/tiles
BASE=https://irsa.ipac.caltech.edu/data/COSMOS/images/acs_mosaic_2.0/tiles
for T in 071 072; do
    wget -cq "$BASE/acs_I_030mas_${T}_sci.fits.gz"
    wget -cq "$BASE/acs_I_030mas_${T}_wht.fits.gz"
done
gunzip -f acs_I_030mas_071_sci.fits.gz acs_I_030mas_071_wht.fits.gz \
          acs_I_030mas_072_sci.fits.gz acs_I_030mas_072_wht.fits.gz
echo TILES_DONE
