#!/usr/bin/env python
"""GEN4-G2: add --deflector_manifest mode to hybrid_combine.py.
Manifest mode: per image i, paste EXACTLY the assigned stamp with the assigned
dihedral at NATIVE amplitude (the real galaxy's own photometry IS the light —
no mag draw, no scaling). Backup .bak_g2."""
import os
import shutil

F = os.path.expanduser("~/cosmos_acs/tiles/hybrid_combine.py")
src = open(F).read()
if "deflector_manifest" in src:
    raise SystemExit("already patched")

A_ARG = 'p.add_argument("--deflector_mag_csv", default="lens_light_empirical.csv",'
A_DEF = "    def inject_deflector(sim):"
A_CALL = "            di, dmag = inject_deflector(sim)"
for a in (A_ARG, A_DEF, A_CALL):
    if a not in src:
        raise SystemExit("anchor missing: %r" % a[:50])

shutil.copy(F, F + ".bak_g2")

src = src.replace(A_ARG, '''p.add_argument("--deflector_manifest", default=None,
                   help="GEN4-G2 assignment csv (file_row,stamp_id,dihedral_k): "
                        "paste EXACTLY that stamp/orientation at NATIVE amplitude")
    ''' + A_ARG, 1)

src = src.replace(A_DEF, '''    g2_assign = None
    if args.deflector_manifest:
        import csv as _csv
        g2_assign = {int(r["file_row"]): (int(r["stamp_id"]), int(r["dihedral_k"]))
                     for r in _csv.DictReader(open(args.deflector_manifest))}
        print("G2 manifest mode: %d assignments, native amplitude, no mag draw"
              % len(g2_assign))

    def inject_deflector_g2(sim, i):
        """GEN4-G2: the assigned real galaxy at its own brightness."""
        di, k = g2_assign[i]
        st = deflectors[di]
        st = np.rot90(st, k % 4)
        if k >= 4:
            st = np.fliplr(st)
        st = np.ascontiguousarray(st).copy()
        sp = st.shape[0]
        jy = int(round(rng.uniform(-args.deflector_jitter, args.deflector_jitter)))
        jx = int(round(rng.uniform(-args.deflector_jitter, args.deflector_jitter)))
        if sp >= n_px:
            c0 = (sp - n_px) // 2
            y0, x0 = c0 + jy, c0 + jx
            sim += st[y0:y0 + n_px, x0:x0 + n_px]
        else:
            y0 = (n_px - sp) // 2 + jy
            x0 = (n_px - sp) // 2 + jx
            ys, xs = max(y0, 0), max(x0, 0)
            ye, xe = min(y0 + sp, n_px), min(x0 + sp, n_px)
            sim[ys:ye, xs:xe] += st[ys - y0:ye - y0, xs - x0:xe - x0]
        mag_native = args.zeropoint - 2.5 * np.log10(max(float(np.clip(st, 0, None).sum()), 1e-9))
        return di, mag_native

''' + A_DEF, 1)

src = src.replace(A_CALL, '''            if g2_assign is not None:
                di, dmag = inject_deflector_g2(sim, i)
            else:
                di, dmag = inject_deflector(sim)''', 1)

open(F, "w").write(src)
print("patched hybrid_combine.py (backup .bak_g2): +--deflector_manifest")
