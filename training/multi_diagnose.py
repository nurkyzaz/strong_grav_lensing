#!/usr/bin/env python
"""Visualize the multi-output model: theta_E / e1 / e2 scatter vs truth + centre error
quiver. Loads a train_cnn_multi checkpoint and a test set; uses the ckpt's stored stats."""
import argparse, numpy as np, torch
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from torch.utils.data import DataLoader
from train_cnn_multi import MultiDataset, EinsteinCNNMulti

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ckpt", required=True)
    ap.add_argument("--image_file", required=True)
    ap.add_argument("--label_file", required=True)
    ap.add_argument("--ellip_file", required=True)
    ap.add_argument("--out", default="multi_diag.png")
    ap.add_argument("--rms_cut", type=float, default=0.2)
    ap.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    args = ap.parse_args()
    device = torch.device(args.device)
    ck = torch.load(args.ckpt, map_location=device)
    stats = (ck["scale_mean"], ck["scale_std"], ck["ymean"], ck["ystd"])

    ds = MultiDataset(args.image_file, args.label_file, args.ellip_file,
                      norm=ck.get("norm","asinh"), asinh_a=ck.get("asinh_a",1.0),
                      rms_cut=args.rms_cut, stats=stats)
    model = EinsteinCNNMulti(channels=tuple(ck.get("channels",(32,64,128,256)))).to(device)
    model.load_state_dict(ck["state_dict"]); model.eval()

    P=[]
    with torch.no_grad():
        for img,s,y,m in DataLoader(ds, batch_size=128):
            P.append(model(img.to(device), s.to(device)).cpu().numpy())
    P=np.concatenate(P)
    Pu = P*ck["ystd"] + ck["ymean"]
    Yu = ds.Y
    V = ds.valid.astype(bool)

    def r2(t,p): return 1 - np.sum((t-p)**2)/np.sum((t-t.mean())**2)
    fig, ax = plt.subplots(2,2, figsize=(11,10))
    t,p = Yu[:,0], Pu[:,0]
    ax[0,0].scatter(t,p,s=5,alpha=.3); lim=[t.min(),t.max()]; ax[0,0].plot(lim,lim,'r--')
    ax[0,0].set_xlabel('true theta_E ["]'); ax[0,0].set_ylabel('pred')
    ax[0,0].set_title(f'theta_E  frac {100*np.median(np.abs(p-t)/t):.2f}%  R2 {r2(t,p):.3f}')
    for k,(ci,nm) in enumerate([(1,"e1"),(2,"e2")]):
        a=ax[0,1] if k==0 else ax[1,0]
        t,p = Yu[V,ci], Pu[V,ci]
        a.scatter(t,p,s=5,alpha=.3); a.plot([-.6,.6],[-.6,.6],'r--')
        a.set_xlabel(f'true {nm}'); a.set_ylabel(f'pred {nm}')
        a.set_title(f'{nm}  R2 {r2(t,p):.2f}  MAE {np.mean(np.abs(p-t)):.3f}')
    a=ax[1,1]; idx=np.where(V)[0]
    if len(idx)>300: idx=np.random.default_rng(0).choice(idx,300,replace=False)
    tdx,tdy=Yu[idx,3],Yu[idx,4]; pdx,pdy=Pu[idx,3],Pu[idx,4]
    a.quiver(tdx,tdy,pdx-tdx,pdy-tdy,angles='xy',scale_units='xy',scale=1,width=0.004,alpha=.6)
    a.scatter(tdx,tdy,s=6,c='green',label='true centre')
    med=np.median(np.hypot(Pu[V,3]-Yu[V,3],Pu[V,4]-Yu[V,4]))
    a.set_xlabel('dx [px]'); a.set_ylabel('dy [px]'); a.legend(fontsize=8)
    a.set_title(f'centre: arrow=true->pred  median err {med:.2f}px'); a.set_aspect('equal')
    plt.tight_layout(); plt.savefig(args.out, dpi=120); plt.close()
    print(f"[multi_diag] wrote {args.out}")

if __name__ == "__main__":
    main()
