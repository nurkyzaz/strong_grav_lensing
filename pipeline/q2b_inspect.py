import glob, json, os
import numpy as np
from astropy.io import fits
from astropy.wcs import WCS

base = os.path.expanduser('~/cosmos_acs/q1_slde/lens/lens')
dirs = sorted(glob.glob(base + '/*'))
print('n_dirs:', len(dirs))
d = dirs[0]
name = os.path.basename(d)
print('example:', name)
# info.json
with open(os.path.join(d, 'info.json')) as f:
    info = json.load(f)
print('info.json keys:', list(info.keys()))
print(json.dumps(info, indent=1)[:600])
# main fits
hdul = fits.open(os.path.join(d, name + '.fits'))
print('n_hdus:', len(hdul))
for i, h in enumerate(hdul):
    shape = getattr(h.data, 'shape', None)
    print(f'  HDU{i}: name={h.name} shape={shape}')
h0 = hdul[0] if hdul[0].data is not None else hdul[1]
hdr = h0.header
for k in ('CDELT1','CDELT2','CD1_1','CD2_2','PC1_1','BUNIT','EXPTIME','MAGZERO','ZP','PHOTZP','FILTER','INSTRUME'):
    if k in hdr: print(f'  {k} = {hdr[k]}')
try:
    w = WCS(hdr)
    scale = np.abs(np.diag(w.pixel_scale_matrix)) * 3600
    print('  pixel scale (arcsec):', scale)
except Exception as e:
    print('  WCS err:', e)
img = h0.data
print('  image stats: shape', img.shape, 'min %.4g max %.4g median %.4g' % (np.nanmin(img), np.nanmax(img), np.nanmedian(img)))
# mass model json
with open(os.path.join(d, 'result_lens_mass.json')) as f:
    mass = json.load(f)
print('result_lens_mass keys:', list(mass.keys())[:20])
