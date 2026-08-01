#!/usr/bin/env python
"""C10 HARD GATE (Nurkyz ruling 2026-07-13): a pilot must FAIL IMMEDIATELY
if the manifest's physics-spec sidecar is missing, or if any --require'd
physics axis is not ON. AR3/z-migration pilots do not launch without it.

Usage: c10_check.py <manifest.csv> --require multipoles z_migration [...]
"""
import argparse
import json
import sys

ap = argparse.ArgumentParser()
ap.add_argument("manifest")
ap.add_argument("--require", nargs="+", default=[])
a = ap.parse_args()

fn = a.manifest + ".physics_spec.json"
try:
    spec = json.load(open(fn))
except (IOError, OSError):
    sys.exit("C10 GATE FAIL: sidecar %s MISSING — pilot aborted" % fn)

print("C10 sidecar %s (spec %s):" % (fn, spec.get("spec_version", "?")))
bad = []
for key in a.require:
    val = str(spec.get(key, "ABSENT"))
    ok = val.startswith("ON")
    print("  %-24s %s  [%s]" % (key, "PASS" if ok else "FAIL", val[:90]))
    if not ok:
        bad.append(key)
if bad:
    sys.exit("C10 GATE FAIL: required physics not ON: %s" % ", ".join(bad))
print("C10 GATE PASS (%d axes verified)" % len(a.require))
