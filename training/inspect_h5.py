import h5py, glob, os
for path in sorted(glob.glob("*.h5")):
    print(f"\n=== {path}  ({os.path.getsize(path)/1e6:.0f} MB) ===")
    with h5py.File(path, "r") as f:
        for k in f.keys():
            d = f[k]
            print(f"  {k:16s} shape={d.shape} dtype={d.dtype}")
        if len(f.attrs):
            print("  attrs:", {k: f.attrs[k] for k in list(f.attrs)[:8]})
