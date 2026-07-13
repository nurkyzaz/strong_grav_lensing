#!/bin/bash
# GEN4-G1b: batched MAST fetch of the LRGDEFL2 expansion targets.
# Chunks of 40 with mast_cache purge between chunks (84 targets grew the cache
# to ~32 GB last time -> ~400 would blow quota without purging).
# Run: nohup bash g1_fetch_driver.sh > g1_fetch.log 2>&1 &   (login node)
set -e
PY=/home/user/nurkyz/miniconda3/envs/Stronglensing/bin/python
cd /home/user/nurkyz/einstein_cnn

N=$($PY - <<'EOF'
import csv
rows=list(csv.DictReader(open('lrgdefl2_labels.csv')))
print(len(rows))
EOF
)
echo "targets: $N"
CHUNK=40
i=0
start=0
while [ "$start" -lt "$N" ]; do
    end=$((start + CHUNK)); if [ "$end" -gt "$N" ]; then end=$N; fi
    $PY - "$start" "$end" <<'EOF'
import csv, sys
s, e = int(sys.argv[1]), int(sys.argv[2])
rows = list(csv.DictReader(open('lrgdefl2_labels.csv')))
with open('lrgdefl2_chunk.csv', 'w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    w.writeheader()
    for r in rows[s:e]:
        w.writerow(r)
print('chunk rows', e - s)
EOF
    echo "=== chunk $i (rows $start-$end) $(date) ==="
    $PY fetch_real_lens_images.py --labels lrgdefl2_chunk.csv --survey LRGDEFL2 \
        --box 12.8 --npix 256 --cache mast_cache_g1 \
        --out real_lrgdefl2_chunk$(printf '%02d' $i).h5 || echo "CHUNK $i HAD ERRORS (continuing)"
    rm -rf mast_cache_g1
    quota -s 2>/dev/null | tail -1
    i=$((i + 1)); start=$end
done
$PY g1_concat_h5.py "real_lrgdefl2_chunk*.h5" real_lrgdefl2_images_256.h5 && rm -f real_lrgdefl2_chunk*.h5
echo "G1_FETCH_DONE $(date)"
