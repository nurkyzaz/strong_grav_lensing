# C15c: theta_SIS(sigma_fiber) vs b_SIE on the benchmark — VALIDATION ONLY
# (normalization 0.948 is literature, never fitted here).
# Kinematics: Bolton 2008 table4 (VizieR J/ApJ/682/964/table4): Name zFG zBG sigma e_sigma Lens
import csv, numpy as np
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from astropy.cosmology import FlatLambdaCDM
cosmo = FlatLambdaCDM(H0=70, Om0=0.3)
C_KMS = 299792.458

kin = {}
for line in open('/home/user/nurkyz/cosmos_acs/q1_slde/bolton08_table4_kinematics.tsv'):
    if line.startswith('#') or line.startswith('-') or not line.strip(): continue
    p = [x.strip() for x in line.rstrip('\n').split('\t')]
    if not p[0].startswith('J'): continue
    try:
        kin[p[0]] = dict(zl=float(p[1]), zs=float(p[2]), sig=float(p[3]), esig=float(p[4]))
    except (ValueError, IndexError):
        continue  # blank sigma rows dropped

rows = []
for r in csv.DictReader(open('/home/user/nurkyz/cosmos_acs/q1_slde/bolton08_table5.csv')):
    n = r['system']
    if n == 'J0955+0101': continue  # excluded benchmark cutout
    if n not in kin:
        print('no kinematics:', n); continue
    a = kin[n]
    dls = cosmo.angular_diameter_distance_z1z2(a['zl'], a['zs']).value
    ds = cosmo.angular_diameter_distance(a['zs']).value
    for corr, tag in ((1.0, 'raw'), (1/0.948, 'c15a')):
        sig = a['sig'] * corr
        th = 4*np.pi*(sig/C_KMS)**2 * (dls/ds) * 206265.0
        a[tag] = th
    rows.append((n, float(r['b_SIE_arcsec']), a['raw'], a['c15a'], a['sig'], a['esig']))

b = np.array([r[1] for r in rows]); raw = np.array([r[2] for r in rows]); cor = np.array([r[3] for r in rows])
for tag, th in (('RAW (sigma_fiber)', raw), ('C15a (sigma/0.948)', cor)):
    fr = th/b - 1
    print('%s: N=%d  median offset %+.1f%%  NMAD scatter %.1f%%' % (tag, len(b), 100*np.median(fr), 100*1.4826*np.median(np.abs(fr-np.median(fr)))))
fig, ax = plt.subplots(1, 2, figsize=(10, 4.6), sharey=True)
for i, (tag, th) in enumerate((('raw sigma_fiber', raw), ('corrected sigma_fiber/0.948', cor))):
    ax[i].scatter(b, th, s=18)
    lim = [0.4, 2.2]; ax[i].plot(lim, lim, 'k--', lw=1)
    ax[i].set_xlabel('b_SIE (Bolton 2008) [arcsec]'); ax[i].set_title(tag + '  (median %+.1f%%)' % (100*np.median(th/b-1)))
ax[0].set_ylabel('theta_SIS from SDSS sigma_v [arcsec]')
plt.tight_layout(); plt.savefig('/home/user/nurkyz/cosmos_acs/q1_slde/c15c_validation.png', dpi=140)
print('figure written')
np.savetxt('/home/user/nurkyz/cosmos_acs/q1_slde/c15c_table.csv',
           np.array([[r[1], r[2], r[3], r[4], r[5]] for r in rows]),
           header='b_SIE_arcsec,theta_SIS_raw,theta_SIS_c15a,sigma_kms,e_sigma_kms', delimiter=',', comments='')
print('per-lens table written (%d rows)' % len(rows))
