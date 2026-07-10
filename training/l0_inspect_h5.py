#!/usr/bin/env python
"""L0 helper: print keys/shapes/name ordering of the benchmark h5 files."""
import h5py

for p in ["/home/user/nurkyz/einstein_cnn/euclid_slacs_images.h5",
          "/home/user/nurkyz/einstein_cnn/real_slacs_images.h5",
          "/home/user/nurkyz/einstein_cnn/euclid_s4tm_images.h5",
          "/home/user/nurkyz/einstein_cnn/real_s4tm_images.h5"]:
    try:
        f = h5py.File(p, "r")
    except Exception as e:
        print(p, "OPEN FAILED:", e)
        continue
    print(p.split("/")[-1])
    for k in f.keys():
        print("   %-12s %s %s" % (k, f[k].shape, f[k].dtype))
    for cand in ("names", "name", "lens_names"):
        if cand in f:
            v = f[cand][:4]
            v = [x.decode() if hasattr(x, "decode") else str(x) for x in v]
            print("   first %s: %s" % (cand, v))
    f.close()
