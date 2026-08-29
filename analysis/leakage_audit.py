#!/usr/bin/env python3
"""Leakage audit (reviewer concern R2): does any training lens-light library
galaxy coincide with a benchmark lens? Cross-matches library sky positions
against benchmark positions, and also checks J-name overlap.

Benchmark positions: tables/manifest_benchmark.csv (source=J-name, ra, dec).
Library positions:  tables/g0_stamp_kinematics.csv (name, ra, dec) and
                    tables/g1b_lens_candidates.csv (stamp_id, ra_deg, dec_deg).
"""
import csv, math

def load_benchmark():
    seen = {}
    with open('tables/manifest_benchmark.csv') as f:
        for r in csv.DictReader(f):
            try:
                seen[r['source']] = (float(r['ra']), float(r['dec']))
            except (KeyError, ValueError):
                continue
    return seen  # J-name -> (ra,dec)

def load_library():
    lib = []  # (id, ra, dec)
    with open('tables/g0_stamp_kinematics.csv') as f:
        for r in csv.DictReader(f):
            try:
                lib.append((r['name'], float(r['ra']), float(r['dec'])))
            except (KeyError, ValueError):
                continue
    try:
        with open('tables/g1b_lens_candidates.csv') as f:
            for r in csv.DictReader(f):
                try:
                    lib.append((r['stamp_id'], float(r['ra_deg']), float(r['dec_deg'])))
                except (KeyError, ValueError):
                    continue
    except FileNotFoundError:
        pass
    return lib

def sep_arcsec(ra1, dec1, ra2, dec2):
    # small-angle separation in arcsec
    dra = (ra1 - ra2) * math.cos(math.radians((dec1 + dec2) / 2))
    ddec = dec1 - dec2
    return math.hypot(dra, ddec) * 3600.0

if __name__ == "__main__":
    bench = load_benchmark()
    lib = load_library()
    print(f"benchmark systems (with coords): {len(bench)}")
    print(f"library galaxies (with coords):  {len(lib)}")

    # J-name overlap
    bench_names = set(bench)
    lib_names = set(n for n, _, _ in lib)
    print(f"J-name overlap library∩benchmark: {len(bench_names & lib_names)}")

    # position cross-match: nearest benchmark to each library galaxy
    TOL = 5.0  # arcsec
    hits = []
    min_sep_overall = 1e9
    for lid, lra, ldec in lib:
        best = min(((sep_arcsec(lra, ldec, bra, bdec), bn)
                    for bn, (bra, bdec) in bench.items()), default=(1e9, None))
        min_sep_overall = min(min_sep_overall, best[0])
        if best[0] < TOL:
            hits.append((lid, best[1], best[0]))
    print(f"closest library-to-benchmark separation: {min_sep_overall:.1f} arcsec")
    print(f"library galaxies within {TOL}\" of a benchmark lens (potential leakage): {len(hits)}")
    for lid, bn, s in hits:
        print(f"   {lid}  <->  {bn}   ({s:.2f}\")")
    print("RESULT:", "NO positional overlap -> no leakage detected"
          if not hits else "OVERLAP FOUND -> investigate")
