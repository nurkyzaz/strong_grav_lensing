import h5py, numpy as np, sys
path = sys.argv[1]
sigma_n = float(sys.argv[2]) if len(sys.argv) > 2 else 0.01
snr_floor = 5.0
with h5py.File(path, "a") as f:
    img = f["lensed"]; N = img.shape[0]
    for k in ("peak_snr", "n_bright_pix"):
        if k in f: del f[k]
    d_ps = f.create_dataset("peak_snr", (N,), dtype="float32")
    d_nb = f.create_dataset("n_bright_pix", (N,), dtype="int64")
    bs = 512
    for s in range(0, N, bs):
        e = min(s + bs, N)
        x = img[s:e].reshape(e - s, -1)
        d_ps[s:e] = x.max(axis=1) / sigma_n
        d_nb[s:e] = (x > snr_floor * sigma_n).sum(axis=1)
    ps = f["peak_snr"][:]
    print("peak_snr percentiles:")
    for q in [5, 10, 25, 50, 75, 90]:
        print(f"  {q:2d}th = {np.percentile(ps, q):.2f}")
print("added peak_snr, n_bright_pix to", path)
