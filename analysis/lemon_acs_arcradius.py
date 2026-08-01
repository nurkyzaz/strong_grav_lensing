"""Score OURS vs LEMON on the ACS subsample against the Pawase 2014 arc radius.

Arc radius is a PROXY, not theta_E (systematically larger); reported separately
from the theta_E aggregate. See DECISIONS_LOG 2026-08-01 for the interpretation.
Run from the repo root: python analysis/lemon_acs_arcradius.py
"""
import os
import numpy as np, pandas as pd, re, glob

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# --- Pawase arc radius GT ---
arc = pd.read_csv(f"{ROOT}/tables/pawase_arc_radius.csv")
def norm_coord(s):  # normalize coord string to digits-only key
    return re.sub(r"[^0-9]", "", str(s))
arc["key"] = arc["coord"].map(norm_coord)
arc_map = dict(zip(arc["key"], arc["arc_radius_arcsec"]))

CHIPGAP = norm_coord("221501.12-135822.9")  # excluded (chip gap)

# --- our preds: id like ACS_001423p02M302109p8 -> digits ---
def id_to_key(name):
    m = name.replace("ACS_", "")
    m = m.replace("p", ".").replace("P", "+").replace("M", "-")
    return norm_coord(m)

def load_ensemble(pattern):
    files = sorted(glob.glob(pattern))
    dfs = [pd.read_csv(f)[["name", "theta_E_pred_arcsec"]].rename(columns={"theta_E_pred_arcsec": f}) for f, in [(f,) for f in files]]
    m = dfs[0]
    for d in dfs[1:]:
        m = m.merge(d, on="name")
    predcols = [c for c in m.columns if c != "name"]
    m["pred"] = m[predcols].mean(axis=1)
    m["key"] = m["name"].map(id_to_key)
    return m[["key", "pred"]]

our_euclid = load_ensemble(f"{ROOT}/results/preds_lemonq1b_g4_cnv2_s*_ACS_euclid.csv")
our_native = load_ensemble(f"{ROOT}/results/preds_lemonq1b_g4n_cnv2_s*_ACS_native.csv")

# --- LEMON preds ---
lem = pd.read_csv(f"{ROOT}/tables/lemon_predictions/lemon_acs_predictions.csv")
def lemon_key(fn):
    m = re.search(r"ACS([0-9]{6}\.[0-9]{2}[+-][0-9]{6}\.[0-9])", fn)
    return norm_coord(m.group(1)) if m else None
lem["key"] = lem["Name"].map(lemon_key)
lem = lem.rename(columns={"Einstein_radius(arcsec)": "pred"})[["key", "pred"]]

def metrics(df, label):
    df = df.dropna(subset=["pred", "gt"])
    p, g = df["pred"].values, df["gt"].values
    bias = np.mean(p - g)
    rmse = np.sqrt(np.mean((p - g) ** 2))
    frac = (p - g) / g
    nmad = 1.4826 * np.median(np.abs(frac - np.median(frac)))
    ss_res = np.sum((p - g) ** 2)
    ss_tot = np.sum((g - g.mean()) ** 2)
    r2 = 1 - ss_res / ss_tot
    fail = np.mean(np.abs(frac) > 0.15)
    medfrac = np.median(np.abs(frac))
    print(f"{label:28s} N={len(df):2d}  bias={bias:+.3f}  RMSE={rmse:.3f}  NMAD={nmad:.3f}  R2={r2:+.2f}  medfrac={medfrac:.3f}  fail>15%={fail*100:.0f}%")

def score(preds, label, exclude_chipgap=True):
    d = preds.copy()
    d["gt"] = d["key"].map(arc_map)
    if exclude_chipgap:
        d = d[d["key"] != CHIPGAP]
    metrics(d, label)

# --- per-lens dump (12 usable) ---
def key_to_coord(k):
    return arc.set_index("key").loc[k, "coord"] if k in set(arc["key"]) else k
merged = arc[arc["key"] != CHIPGAP][["key", "coord", "arc_radius_arcsec"]].copy()
merged = merged.merge(lem.rename(columns={"pred": "lemon_pred"}), on="key", how="left")
merged = merged.merge(our_euclid.rename(columns={"pred": "our_euclid_pred"}), on="key", how="left")
merged = merged.merge(our_native.rename(columns={"pred": "our_native_pred"}), on="key", how="left")
merged.drop(columns=["key"]).to_csv(f"{ROOT}/results/lemon_vs_ours_acs_arcradius.csv", index=False)
print("wrote results/lemon_vs_ours_acs_arcradius.csv")

print("=== ACS vs Pawase arc radius — 12 usable lenses (chip-gap excluded) ===")
score(lem, "LEMON (12)")
score(our_euclid, "OURS euclid-arm (12)")
score(our_native, "OURS native-arm (12)")
print()
print("=== ACS vs arc radius — all 13 (LEMON's Table-3 footing, incl chip-gap) ===")
score(lem, "LEMON (13)", exclude_chipgap=False)
# our files have no chip-gap row anyway (12), so 'all 13' N/A for us
