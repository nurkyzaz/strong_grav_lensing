# Q2 preprocessing pilot: 10 lenses -> 128px@0.05" grid + C17 flux gate stats
import glob, json, os, numpy as np
from astropy.io import fits
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt

base = '/home/user/nurkyz/cosmos_acs/q1_slde/lens/lens'
dirs = sorted(glob.glob(base + '/*'))[:10]
# catalog fluxes for the C17 gate
import csv
cat = {r['id_str']: r for r in csv.DictReader(open('/home/user/nurkyz/cosmos_acs/q1_slde/q1_discovery_engine_lens_catalog.csv'))}
MAGZERO = 24.6
fig, axes = plt.subplots(3, 10, figsize=(26, 8))
print('id_str            skyRMS    peak/sky  m_aper(2as)  m_cat_1fwhm  dm')
for j, d in enumerate(dirs):
    name = os.path.basename(d)
    hdul = fits.open(os.path.join(d, name + '.fits'))
    vis = hdul['VIS_FLUX'].data.astype(float)
    c = vis.shape[0]//2
    crop = vis[c-32:c+32, c-32:c+32]                      # 64px @ 0.1" = 6.4"
    up = np.repeat(np.repeat(crop, 2, 0), 2, 1) / 4.0      # 128px @ 0.05", flux-conserving
    # stats
    corner = np.concatenate([up[:12,:12].ravel(), up[:12,-12:].ravel(), up[-12:,:12].ravel(), up[-12:,-12:].ravel()])
    sky = np.median(corner); rms = 1.4826*np.median(np.abs(corner-sky))
    peak = np.percentile(up, 99.99)
    # aperture photometry r=2" on the ORIGINAL 0.1" grid (r=20px)
    yy, xx = np.mgrid[:vis.shape[0], :vis.shape[1]]
    rr = np.hypot(yy-c, xx-c)
    ap = vis[rr < 20].sum() - np.median(vis[(rr>40)&(rr<60)])*(rr<20).sum()
    m_ap = MAGZERO - 2.5*np.log10(max(ap, 1e-9))
    fcat = float(cat[name]['flux_vis_1fwhm_aper']) if name in cat and cat[name]['flux_vis_1fwhm_aper'] else np.nan
    m_cat = MAGZERO - 2.5*np.log10(fcat) if np.isfinite(fcat) and fcat > 0 else np.nan
    print('%s  %8.4f  %8.0f  %6.2f  %6.2f  %+5.2f' % (name[:16], rms, (peak-sky)/max(rms,1e-9), m_ap, m_cat, m_ap - m_cat if np.isfinite(m_cat) else 0))
    for i, (stretch, im) in enumerate((('linear', up), ('pct', np.clip(up, np.percentile(up,1), np.percentile(up,99))), ('asinh', np.arcsinh(up/max(rms,1e-9))))):
        axes[i, j].imshow(im, origin='lower', cmap='gray'); axes[i, j].axis('off')
        if i == 0: axes[i, j].set_title(name[:9], fontsize=6)
plt.tight_layout(); plt.savefig('/home/user/nurkyz/cosmos_acs/q1_slde/q2_pilot_preview.png', dpi=110)
print('preview written')
