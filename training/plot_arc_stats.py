import h5py, numpy as np, sys
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
f = h5py.File(sys.argv[1], "r")
ps, mg = f["peak_snr"][:], f["mag_proxy"][:]
fig, ax = plt.subplots(1, 2, figsize=(10, 4))
ax[0].hist(ps, bins=80); ax[0].set_yscale("log"); ax[0].set_xlabel("peak_snr")
ax[1].hist(mg, bins=80); ax[1].set_yscale("log"); ax[1].set_xlabel("mag_proxy")
plt.tight_layout(); plt.savefig("arc_stats.png", dpi=120)
print("saved arc_stats.png")
for q in [5, 10, 25, 50]:
    print(f"  peak_snr {q}th pct = {np.percentile(ps, q):.2f}")
