import h5py, numpy as np, argparse
ap = argparse.ArgumentParser()
ap.add_argument("--inputs", nargs="+", required=True)
ap.add_argument("--out", required=True)
args = ap.parse_args()

KEYS_1D = ["kappa_index", "source_index", "peak_snr", "n_bright_pix", "mag_proxy"]
sizes = []
for p in args.inputs:
    with h5py.File(p) as f:
        sizes.append(f["lensed"].shape[0])
total = sum(sizes)
with h5py.File(args.inputs[0]) as f0:
    H, W = f0["lensed"].shape[1:]
    present = [k for k in KEYS_1D if k in f0]
    dtypes = {k: f0[k].dtype for k in present}

with h5py.File(args.out, "w") as fo:
    d_img = fo.create_dataset("lensed", (total, H, W), dtype="float32")
    d1 = {k: fo.create_dataset(k, (total,), dtype=dtypes[k]) for k in present}
    off = 0
    for p in args.inputs:
        with h5py.File(p) as f:
            n = f["lensed"].shape[0]
            d_img[off:off+n] = f["lensed"][:]
            for k in present:
                d1[k][off:off+n] = f[k][:]
            off += n
print(f"combined {args.inputs} -> {args.out}  total={total}")
