# C17 gate (Q2c): compare preprocessed real-Q1 cutouts vs the frozen Euclid
# benchmark (euclid_slacs_images_g3.h5) the model evaluates on — sky RMS,
# peak/sky, and gross flux scale. gate_stage0-style distribution check.
import glob, os, numpy as np, h5py
from astropy.io import fits

def stats(im):
    n = im.shape[0]; k = max(8, n // 10)
    corner = np.concatenate([im[:k,:k].ravel(), im[:k,-k:].ravel(), im[-k:,:k].ravel(), im[-k:,-k:].ravel()])
    sky = np.median(corner); rms = 1.4826 * np.median(np.abs(corner - sky))
    peak = np.percentile(im, 99.99)
    return sky, rms, (peak - sky) / max(rms, 1e-12)

# benchmark side
bench = '/home/user/nurkyz/einstein_cnn/euclid_slacs_images_g3.h5'
with h5py.File(bench, 'r') as f:
    print('datasets:', {k: (f[k].shape, str(f[k].dtype)) for k in f.keys()})
    key = max((k for k in f.keys() if f[k].ndim >= 3), key=lambda k: np.prod(f[k].shape))
    ims = f[key][:]
print('benchmark %s: key=%s shape=%s dtype=%s' % (os.path.basename(bench), key, ims.shape, ims.dtype))
bs = np.array([stats(np.squeeze(im).astype(float)) for im in ims])
print('BENCH  skyRMS: med %.4g [10-90%%: %.4g..%.4g]   peak/sky: med %.0f [%.0f..%.0f]' % (
    np.median(bs[:,1]), *np.percentile(bs[:,1], [10,90]), np.median(bs[:,2]), *np.percentile(bs[:,2], [10,90])))

# Q1 pilot side (same 10 lenses, same preprocessing as q2_pilot.py)
base = '/home/user/nurkyz/cosmos_acs/q1_slde/lens/lens'
qs = []
for d in sorted(glob.glob(base + '/*'))[:10]:
    name = os.path.basename(d)
    vis = fits.open(os.path.join(d, name + '.fits'))['VIS_FLUX'].data.astype(float)
    c = vis.shape[0]//2
    crop = vis[c-32:c+32, c-32:c+32]
    up = np.repeat(np.repeat(crop, 2, 0), 2, 1) / 4.0
    qs.append(stats(up))
qs = np.array(qs)
print('Q1x10  skyRMS: med %.4g [min..max: %.4g..%.4g]   peak/sky: med %.0f [%.0f..%.0f]' % (
    np.median(qs[:,1]), qs[:,1].min(), qs[:,1].max(), np.median(qs[:,2]), qs[:,2].min(), qs[:,2].max()))
print('RATIO Q1/bench: skyRMS %.2fx   peak/sky %.2fx' % (
    np.median(qs[:,1]) / np.median(bs[:,1]), np.median(qs[:,2]) / np.median(bs[:,2])))
print('sky level: bench med %.4g   Q1 med %.4g' % (np.median(bs[:,0]), np.median(qs[:,0])))
