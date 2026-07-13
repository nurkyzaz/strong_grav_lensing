#!/usr/bin/env python
"""Merge per-sub-shard paltas metadata.csv files (train sub-shards only)."""
import argparse
import glob
import os
import pandas as pd

ap = argparse.ArgumentParser()
ap.add_argument("--shards", required=True, help="shard root containing sub_*/metadata.csv")
ap.add_argument("--train-max-id", type=int, default=80,
                help="sub-shards with id < this are train")
ap.add_argument("--out", required=True)
a = ap.parse_args()

frames = []
for p in sorted(glob.glob(os.path.join(os.path.expanduser(a.shards), "sub_*", "metadata.csv"))):
    sid = int(os.path.basename(os.path.dirname(p)).split("_")[-1])
    if sid < a.train_max_id:
        frames.append(pd.read_csv(p))
if not frames:
    raise SystemExit("no train metadata found under " + a.shards)
merged = pd.concat(frames, ignore_index=True)
merged.to_csv(os.path.expanduser(a.out), index=False)
print("wrote %s: %d rows from %d sub-shards" % (a.out, len(merged), len(frames)))
