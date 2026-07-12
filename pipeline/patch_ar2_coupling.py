#!/usr/bin/env python
"""AR2 (COMMITMENTS C1) + C10: flag-gated ΔPA↔γ_ext coupling in the manifest
generator, manifest-driven shear in the G2 config, and a PHYSICS SPEC block.

- g2_make_manifest.py gains --couple_shear (DEFAULT OFF): |γ| = min(
  Rayleigh(0.03) + 0.0012·|ΔPA°|, 0.25), shear PA ~ U(0,π) (direction left
  uncorrelated — disclosed); marginal stays close to the legacy independent
  N(0,0.04)² draw (median |γ| ≈ 0.043 vs 0.047). Always prints a PHYSICS SPEC
  block (C10) so pilots surface unimplemented physics mechanically.
- config_lensfusion_acs_g2.py reads gamma1/gamma2 from the manifest IFF the
  columns exist (old manifests keep the legacy independent draw).
Backups .bak_ar2; pattern asserts; smoke test at the end.
"""
import difflib
import os
import shutil

TI = os.path.expanduser("~/cosmos_acs/tiles")


def patch(fn, subs):
    p = os.path.join(TI, fn)
    src = open(p).read()
    for a, b in subs:
        assert a in src, "missing pattern in %s: %r" % (fn, a[:90])
        src = src.replace(a, b)
    shutil.copy2(p, p + ".bak_ar2")
    open(p, "w").write(src)
    print("patched", fn)
    return src


# ---------- manifest generator ----------
patch("g2_make_manifest.py", [
    ('ap.add_argument("--nbin", type=int, default=37)',
     'ap.add_argument("--nbin", type=int, default=37)\n'
     'ap.add_argument("--couple_shear", action="store_true",\n'
     '                help="AR2: gamma_ext coupled to |dPA| (C1); default OFF")'),
    ("""        dpa = float(np.clip(rng.normal(0, 10.0), -30, 30))""",
     """        dpa = float(np.clip(rng.normal(0, 10.0), -30, 30))
        if a.couple_shear:
            gam = float(min(rng.rayleigh(0.03) + 0.0012 * abs(dpa), 0.25))
            phig = float(rng.uniform(0, np.pi))
            g1 = round(gam * np.cos(2 * phig), 6)
            g2 = round(gam * np.sin(2 * phig), 6)"""),
    ("""                         pa_light_eff=round(pa_l, 2), dpa=round(dpa, 2)))""",
     """                         pa_light_eff=round(pa_l, 2), dpa=round(dpa, 2),
                         **(dict(gamma1=g1, gamma2=g2)
                            if a.couple_shear else {})))"""),
    ('''print("manifest rho(stamp mag, theta_E) = %+.2f (physical FJ channel; real ~ -0.3..-0.5)"
      % rho)''',
     '''print("manifest rho(stamp mag, theta_E) = %+.2f (physical FJ channel; real ~ -0.3..-0.5)"
      % rho)
print("PHYSICS SPEC: fj_channel=ON misalignment=ON(N10,clip30) "
      "q_scatter=adhoc0.08(C2-open) gamma_coupling=%s multipoles=OFF(AR3) "
      "tempered_alpha=swept" % ("ON" if a.couple_shear else "OFF(AR2)"))'''),
])

# ---------- config ----------
patch("config_lensfusion_acs_g2.py", [
    ("""config_dict['main_deflector']['parameters']['theta_E'] = _g2_theta_e""",
     """def _g2_gamma1():
    return float(_g2_row("g1")["gamma1"])


def _g2_gamma2():
    return float(_g2_row("g2")["gamma2"])


config_dict['main_deflector']['parameters']['theta_E'] = _g2_theta_e
if _ROWS and "gamma1" in _ROWS[0]:
    # AR2 manifest: shear coupled to the row's misalignment (C1)
    config_dict['main_deflector']['parameters']['gamma1'] = _g2_gamma1
    config_dict['main_deflector']['parameters']['gamma2'] = _g2_gamma2"""),
])

# ---------- smoke: build a tiny coupled manifest and check stats ----------
import subprocess  # noqa: E402
PY = os.path.expanduser("~/miniconda3/envs/Stronglensing/bin/python")
r = subprocess.run(
    [PY, os.path.join(TI, "g2_make_manifest.py"), "--kine",
     os.path.join(TI, "g2_kinematics_unified.csv"), "--n", "400",
     "--seed", "99", "--out", "/tmp_smoke_ar2.csv".replace("/tmp_smoke", TI + "/smoke"),
     "--couple_shear"], capture_output=True, text=True, timeout=900)
print(r.stdout[-600:])
assert "PHYSICS SPEC" in r.stdout and "gamma_coupling=ON" in r.stdout
import csv  # noqa: E402
import numpy as np  # noqa: E402
rows = list(csv.DictReader(open(TI + "/smoke_ar2.csv")))
g = np.hypot([float(x["gamma1"]) for x in rows], [float(x["gamma2"]) for x in rows])
dpa = np.abs([float(x["dpa"]) for x in rows])
hi = g[dpa > 12].mean()
lo = g[dpa < 5].mean()
print("smoke: median|gamma|=%.3f  mean|gamma| (dpa>12)=%.3f vs (dpa<5)=%.3f "
      "(coupling should raise the first)" % (np.median(g), hi, lo))
assert hi > lo, "coupling not present"
os.remove(TI + "/smoke_ar2.csv")
print("AR2_PATCH_OK")
