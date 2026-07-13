#!/bin/bash
# Step-2 sweep: arc-visibility thresholds on the retained G3 pilot (real-PSF
# arcs), looking for the pair that restores the G4-era selection profile
# (overall ~42%; per-theta-bin pass ~26/37/53/64%). Login-node safe (600 imgs).
set -e
PY=/home/user/nurkyz/miniconda3/envs/Stronglensing/bin/python
cd /home/user/nurkyz/einstein_cnn
for SPEC in "0.7 150" "0.9 150" "0.9 200" "1.0 170" "1.1 200" "1.2 170" ; do
    read -r T E <<< "$SPEC"
    echo "=== thresh=$T extent=$E ==="
    $PY arc_visibility_select.py --arcs /home/user/nurkyz/paltas_g3_pilot_euclid \
        --sim g3_pilot_euclid.h5 --out /home/user/nurkyz/g3_scratch/sweep_tmp.h5 \
        --thresh "$T" --min_extent "$E" 2>/dev/null \
        | grep -E "selection:|theta_E (0|survivors)"
done
rm -f /home/user/nurkyz/g3_scratch/sweep_tmp.h5
echo SWEEP_DONE
