#!/bin/bash
# GEN4-G1b phase-1 fetch: 800 ACS/WFC targets (lens-crossmatched), chunks of
# 20 with cache purge (tighter than G1a's 40 — less quota headroom).
# Run: nohup bash g1b_fetch_driver.sh > g1b_fetch.log 2>&1 &   (login node)
set -e
PY=/home/user/nurkyz/miniconda3/envs/Stronglensing/bin/python
cd /home/user/nurkyz/einstein_cnn

$PY g1b_fetch_precheck.py
N=$(tail -n +2 lrgdefl2b_phase1.csv | wc -l)
echo "phase-1 targets: $N"
CHUNK=20
i=0
start=0
while [ "$start" -lt "$N" ]; do
    end=$((start + CHUNK)); if [ "$end" -gt "$N" ]; then end=$N; fi
    $PY - "$start" "$end" <<'EOF'
import csv, sys
s, e = int(sys.argv[1]), int(sys.argv[2])
rows = list(csv.DictReader(open('lrgdefl2b_phase1.csv')))
with open('lrgdefl2b_chunk.csv', 'w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    w.writeheader()
    for r in rows[s:e]:
        w.writerow(r)
print('chunk rows', e - s)
EOF
    echo "=== chunk $i (rows $start-$end) $(date) ==="
    USED_MB=$(quota 2>/dev/null | awk '/sda1/ {getline; print int($1)}')
    if [ -n "$USED_MB" ] && [ "$USED_MB" -gt 100000 ]; then
        echo "PAUSE: quota ${USED_MB}MB > 100G guard — stopping fetch cleanly"; break
    fi
    $PY fetch_real_lens_images.py --labels lrgdefl2b_chunk.csv --survey LRGDEFL2B \
        --box 12.8 --npix 256 --cache mast_cache_g1b \
        --out real_lrgdefl2b_chunk$(printf '%03d' $i).h5 || echo "CHUNK $i HAD ERRORS (continuing)"
    rm -rf mast_cache_g1b
    i=$((i + 1)); start=$end
done
$PY g1_concat_h5.py "real_lrgdefl2b_chunk*.h5" real_lrgdefl2b_images_256.h5 && rm -f real_lrgdefl2b_chunk*.h5
echo "G1B_FETCH_DONE $(date)"
quota -s 2>/dev/null | tail -1
