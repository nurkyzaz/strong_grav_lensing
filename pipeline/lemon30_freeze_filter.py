# Freeze the Q1b fetch (C18) and exclude the one confirmed-bad ACS cutout
# (ACS_221501p12M135822p9: chip-gap/edge cutout, ~62% zero-pixel field,
# diagnosed via three-stretch 2026-07-15).
import h5py
import numpy as np

EC = "/home/user/nurkyz/einstein_cnn"
EXCLUDE = {"ACS_221501p12M135822p9"}

for sub in ("EEL", "COSMOS", "ACS"):
    src = "%s/real_LEMON%s_images.h5" % (EC, sub)
    dst = "%s/real_LEMON%s_frozen.h5" % (EC, sub)
    with h5py.File(src, "r") as f:
        names = [n.decode() if isinstance(n, bytes) else str(n) for n in f["names"][:]]
        keep = [i for i, n in enumerate(names) if n not in EXCLUDE]
        with h5py.File(dst, "w") as g:
            for k in f.keys():
                if f[k].shape == ():
                    g.create_dataset(k, data=f[k][()])
                else:
                    g.create_dataset(k, data=f[k][:][keep])
    print("%s: %d -> %d (excluded %d)" % (sub, len(names), len(keep), len(names) - len(keep)))
print("FROZEN (C18): real_LEMON{EEL,COSMOS,ACS}_frozen.h5")
