#!/bin/bash
# Download 2 additional COSMOS ACS mosaic tiles for a larger empty-cutout
# harvest (backdrop-reuse reduction, next dataset iteration).
#
# 2026-07-09 fix: tiles 071/072 DO NOT EXIST in the IRSA archive (the tile
# sequence jumps 069 -> 073; verified against the directory listing) — the old
# script wgot 404s silently because of -q and then "gunzip: No such file".
# Replaced with tiles 066 and 074 (verified HTTP 200), removed -q so failures
# are visible, and added hard existence checks before gunzip.
# Resumable (wget -c); deletes each .gz after unpack to spare quota.
# QUOTA NOTE: ~4-5 GB unpacked. Run only when quota headroom allows
# (check `quota -s`; wait until the pathb_v2 shards are merged+deleted).
set -e
cd /home/user/nurkyz/cosmos_acs/tiles
BASE=https://irsa.ipac.caltech.edu/data/COSMOS/images/acs_mosaic_2.0/tiles
for T in 066 074; do
    for KIND in sci wht; do
        F="acs_I_030mas_${T}_${KIND}.fits.gz"
        echo "fetching $F ..."
        wget -c "$BASE/$F"
        [ -s "$F" ] || { echo "FAILED: $F missing/empty after wget"; exit 1; }
        gunzip -f "$F"
        [ -s "${F%.gz}" ] || { echo "FAILED: ${F%.gz} missing after gunzip"; exit 1; }
    done
done
echo TILES_DONE
