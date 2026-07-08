"""Generate ellipticity (and centre) labels from IllustrisTNG kappa maps. Self-contained
(numpy + scipy + h5py; NO lenstronomy). Two methods, both validated on synthetic EPLs:

  PRIMARY   = EPL/SIE fit to log(kappa) in an annulus around theta_E, centre fixed to a
              2-pass kappa-centroid, theta_E free in the amplitude (shape-only). Outputs
              e1_fit,e2_fit in the Tessore-Metcalf convention e=(1-q)/(1+q)*exp(2i*phi).
  CROSS-CHECK = iterative ELLIPTICAL-aperture kappa-weighted 2nd moments within ~theta_E.

Measure NEAR theta_E (the arc-relevant region); global moments are biased (LITERATURE.md).
Labels are keyed by kappa_index = row in the kappa file, matching the theta_E labels.
"""
import argparse, h5py, numpy as np
from scipy.optimize import least_squares

def _q_phi_from_e(e1, e2):
    e = min(np.hypot(e1, e2), 0.999)
    return (1.0 - e)/(1.0 + e), 0.5*np.arctan2(e2, e1)

def centroid(kappa):
    m = np.clip(kappa, 0, None).astype("float64")
    yy, xx = np.indices(m.shape); s = m.sum() + 1e-12
    return (xx*m).sum()/s, (yy*m).sum()/s

def einstein_radius_pixels(kappa, cx, cy):
    yy, xx = np.indices(kappa.shape)
    r = np.hypot(xx-cx, yy-cy).ravel(); k = np.clip(kappa,0,None).ravel()
    o = np.argsort(r); r_s, k_s = r[o], k[o]
    mean_enc = np.cumsum(k_s)/np.arange(1, len(k_s)+1)
    below = np.where(mean_enc < 1.0)[0]
    if len(below) == 0 or below[0] == 0: return np.nan
    i = below[0]; r0,r1 = r_s[i-1],r_s[i]; m0,m1 = mean_enc[i-1],mean_enc[i]
    return r1 if m1==m0 else r0 + (1.0-m0)*(r1-r0)/(m1-m0)

def centroid_2pass(kappa, r_factor=1.5):
    cx, cy = centroid(kappa); th = einstein_radius_pixels(kappa, cx, cy)
    if not np.isfinite(th): return cx, cy, th
    yy, xx = np.indices(kappa.shape)
    for _ in range(3):
        r = np.hypot(xx-cx, yy-cy)
        m = np.where(r <= r_factor*th, np.clip(kappa,0,None), 0.0).astype("float64")
        s = m.sum()+1e-12; cxn, cyn = (xx*m).sum()/s, (yy*m).sum()/s
        if np.hypot(cxn-cx, cyn-cy) < 0.05: cx, cy = cxn, cyn; break
        cx, cy = cxn, cyn
    return cx, cy, einstein_radius_pixels(kappa, cx, cy)

def fit_epl_ellipticity(kappa, cx, cy, theta_px, gamma=2.0, fit_gamma=False,
                        a_lo=0.5, a_hi=1.5, kfloor=1e-4, min_pix=30):
    yy, xx = np.indices(kappa.shape)
    X = (xx-cx).astype("float64"); Y = (yy-cy).astype("float64"); r = np.hypot(X, Y)
    mask = (r >= a_lo*theta_px) & (r <= a_hi*theta_px) & (kappa > kfloor)
    if mask.sum() < min_pix: return dict(ok=False)
    Xm, Ym, logk = X[mask], Y[mask], np.log(kappa[mask].astype("float64"))
    def model_logk(p):
        logC, e1, e2 = p[0], p[1], p[2]; g = p[3] if fit_gamma else gamma
        q, phi = _q_phi_from_e(e1, e2)
        Xr =  Xm*np.cos(phi)+Ym*np.sin(phi); Yr = -Xm*np.sin(phi)+Ym*np.cos(phi)
        return logC - 0.5*(g-1.0)*np.log(q*Xr**2 + Yr**2/q + 1e-6)
    p0 = [float(np.median(logk)), 0.0, 0.0] + ([gamma] if fit_gamma else [])
    lo = [-50,-0.95,-0.95] + ([1.2] if fit_gamma else [])
    hi = [ 50, 0.95, 0.95] + ([2.8] if fit_gamma else [])
    try:
        sol = least_squares(lambda p: model_logk(p)-logk, p0, bounds=(lo,hi),
                            method="trf", max_nfev=2000)
    except Exception:
        return dict(ok=False)
    e1, e2 = float(sol.x[1]), float(sol.x[2]); q, phi = _q_phi_from_e(e1, e2)
    return dict(ok=True, e1=e1, e2=e2, q=q, phi=phi,
                gamma=float(sol.x[3]) if fit_gamma else gamma,
                rms=float(np.sqrt(np.mean(sol.fun**2))), npix=int(mask.sum()))

def moment_ellipticity_iter(kappa, cx, cy, theta_px, aperture=1.5, n_iter=8, kfloor=0.0):
    yy, xx = np.indices(kappa.shape)
    X = (xx-cx).astype("float64"); Y = (yy-cy).astype("float64")
    q, phi = 1.0, 0.0; R = aperture*theta_px; e1=e2=0.0
    for _ in range(n_iter):
        Xr =  X*np.cos(phi)+Y*np.sin(phi); Yr = -X*np.sin(phi)+Y*np.cos(phi)
        xi = np.sqrt(q*Xr**2 + Yr**2/q)
        m = np.where((xi<=R)&(kappa>kfloor), np.clip(kappa,0,None), 0.0).astype("float64")
        s = m.sum()+1e-12
        Qxx=(m*X*X).sum()/s; Qyy=(m*Y*Y).sum()/s; Qxy=(m*X*Y).sum()/s
        denom = Qxx+Qyy+2.0*np.sqrt(max(Qxx*Qyy-Qxy**2,0.0))
        if denom<=0: return dict(ok=False)
        e1=(Qxx-Qyy)/denom; e2=(2.0*Qxy)/denom; qn, phi = _q_phi_from_e(e1, e2)
        if abs(qn-q) < 1e-4: q=qn; break
        q=qn
    return dict(ok=True, e1=float(e1), e2=float(e2), q=float(q), phi=float(phi))

def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--kappa_file", required=True)
    ap.add_argument("--out_file", required=True)
    ap.add_argument("--n", type=int, default=None)
    ap.add_argument("--chunk", type=int, default=512)
    ap.add_argument("--gamma", type=float, default=2.0)
    ap.add_argument("--fit_gamma", action="store_true")
    ap.add_argument("--a_lo", type=float, default=0.5)
    ap.add_argument("--a_hi", type=float, default=1.5)
    ap.add_argument("--mom_aperture", type=float, default=1.5)
    ap.add_argument("--plot", default="ellip_compare.png")
    args = ap.parse_args()

    fk = h5py.File(args.kappa_file, "r"); kds = fk["kappa"]
    N = kds.shape[0] if args.n is None else min(args.n, kds.shape[0])
    cols = ["kappa_index","cx","cy","theta_E_pix","e1_fit","e2_fit","q_fit","phi_fit",
            "gamma_fit","rms_fit","npix_fit","ok_fit","e1_mom","e2_mom","q_mom","phi_mom","ok_mom"]
    out = {c: np.full(N, np.nan, dtype="float64") for c in cols}
    out["kappa_index"] = np.arange(N, dtype="float64")

    print(f"[ellip] {N} kappa maps | fit annulus [{args.a_lo},{args.a_hi}]xtheta_E | "
          f"gamma={'free' if args.fit_gamma else args.gamma} | mom aperture {args.mom_aperture}xtheta_E")
    for start in range(0, N, args.chunk):
        end = min(start+args.chunk, N)
        block = np.asarray(kds[start:end], dtype="float32")
        for r in range(end-start):
            g = start + r; kap = block[r]
            cx, cy, th = centroid_2pass(kap)
            out["cx"][g], out["cy"][g], out["theta_E_pix"][g] = cx, cy, th
            if not np.isfinite(th): continue
            A = fit_epl_ellipticity(kap, cx, cy, th, gamma=args.gamma,
                                    fit_gamma=args.fit_gamma, a_lo=args.a_lo, a_hi=args.a_hi)
            if A.get("ok"):
                out["e1_fit"][g],out["e2_fit"][g]=A["e1"],A["e2"]
                out["q_fit"][g],out["phi_fit"][g]=A["q"],A["phi"]
                out["gamma_fit"][g],out["rms_fit"][g],out["npix_fit"][g]=A["gamma"],A["rms"],A["npix"]
                out["ok_fit"][g]=1.0
            else: out["ok_fit"][g]=0.0
            B = moment_ellipticity_iter(kap, cx, cy, th, aperture=args.mom_aperture)
            if B.get("ok"):
                out["e1_mom"][g],out["e2_mom"][g]=B["e1"],B["e2"]
                out["q_mom"][g],out["phi_mom"][g]=B["q"],B["phi"]; out["ok_mom"][g]=1.0
            else: out["ok_mom"][g]=0.0
        print(f"  processed {end}/{N}")
    fk.close()

    with h5py.File(args.out_file, "w") as fo:
        for c in cols: fo.create_dataset(c, data=out[c])
        fo.attrs["note"]="ellipticity labels; e=(1-q)/(1+q)exp(2i phi); keyed by kappa_index"
        for k in ("gamma","fit_gamma","a_lo","a_hi","mom_aperture"):
            fo.attrs[k]=getattr(args,k)
    print(f"[ellip] wrote {args.out_file}")

    okf = out["ok_fit"]==1.0; okb = out["ok_mom"]==1.0; both = okf & okb
    e_fit = np.hypot(out["e1_fit"], out["e2_fit"])
    print(f"[ellip] fit ok {okf.mean()*100:.1f}% | median |e_fit| {np.nanmedian(e_fit[okf]):.3f} | "
          f"median q_fit {np.nanmedian(out['q_fit'][okf]):.3f} | median gamma_fit {np.nanmedian(out['gamma_fit'][okf]):.3f}")
    if both.sum() > 10:
        d = np.hypot(out["e1_fit"][both]-out["e1_mom"][both], out["e2_fit"][both]-out["e2_mom"][both])
        c1 = np.corrcoef(out["e1_fit"][both], out["e1_mom"][both])[0,1]
        c2 = np.corrcoef(out["e2_fit"][both], out["e2_mom"][both])[0,1]
        print(f"[ellip] fit-vs-moment: corr(e1)={c1:.3f} corr(e2)={c2:.3f} | median |de|={np.median(d):.3f}")
    try:
        import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
        fig, ax = plt.subplots(2,2, figsize=(11,10))
        for a,(xf,xm,lab) in zip(ax[0],[(out["e1_fit"],out["e1_mom"],"e1"),(out["e2_fit"],out["e2_mom"],"e2")]):
            a.scatter(xf[both], xm[both], s=4, alpha=.3); a.plot([-.6,.6],[-.6,.6],'r--',lw=1)
            a.set_xlabel(f"{lab} EPL fit"); a.set_ylabel(f"{lab} moments"); a.set_title(f"{lab}: fit vs moments")
        ax[1,0].hist(e_fit[okf], bins=50); ax[1,0].set_xlabel("|e| (EPL fit)"); ax[1,0].set_ylabel("count")
        ax[1,1].scatter(out["q_fit"][both], out["q_mom"][both], s=4, alpha=.3); ax[1,1].plot([0,1],[0,1],'r--',lw=1)
        ax[1,1].set_xlabel("q EPL fit"); ax[1,1].set_ylabel("q moments"); ax[1,1].set_title("axis ratio")
        plt.tight_layout(); plt.savefig(args.plot, dpi=110); plt.close()
        print(f"[ellip] wrote {args.plot}")
    except Exception as e:
        print(f"[ellip] plot skipped: {e}")

if __name__ == "__main__":
    main()
