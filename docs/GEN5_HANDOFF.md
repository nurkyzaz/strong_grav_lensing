# GEN5 Realism — SESSION HANDOFF (2026-08-12)

**For the next agent.** This session tried to make the GEN5 Euclid-realistic lens
simulator match real Euclid Q1 by eye. Many properties now match; **the deflectors
still look like tiny dots and the background still reads too noisy to Nurkyz's eye
— UNRESOLVED.** Read the GOTCHAS section first: this agent's numeric measurements
were repeatedly WRONG and contradicted the eye. **Trust the gallery/eyeball, not
derived metrics.**

---
## 0. THE GOAL
Build a simulator that makes fake Euclid images of strong lenses realistic enough
that a CNN trained on them measures θ_E on REAL Euclid Q1. A real Euclid lens =
a BIG BRIGHT foreground elliptical (deflector) that DOMINATES the image, with a
THIN, FAINTER arc partially wrapped around it. Our sim keeps producing the
INVERSION: a tiny faint deflector dot + a bright dominating arc.

## 1. THE UNRESOLVED PROBLEM (start here)
Nurkyz's eye, repeatedly, on the served gallery (localhost:8899):
- **"deflectors are all just dots"** — they do not look like big bright galaxies.
- **"background is visibly noisy"** — noise too prominent.
- Earlier: arcs too thick/circular on some; a few deflectors invisible.

What this agent tried for the deflector and why it DID NOT satisfy the eye:
- **Half-light Re matches** real (0.72 vs 0.68) — but the galaxy still looks like a dot.
- **de Vaucouleurs envelope** (hybrid_combine `--deflector_envelope`, adds Sersic
  n≈4.4 wings): barely changed the look.
- **Brightness** FJ `mag0 21.39 -> 19.2` (peak/sky 38 -> 277, "matching" real eval
  cutouts' 248): Nurkyz says STILL dots + noisy. So even the peak/sky match did
  not translate to the eye.
- Diagnosed the HST deflector stamps are SHALLOW — the faint de Vauc wings are not
  in the raw data (R(1% of peak)/Re = 1.3 vs real 3.1), so "rebuild keeping wings"
  cannot work (no wings to keep).

**Strong recommendation for the deflector:** stop trusting derived numbers. Either
(a) use REAL Euclid deflector light directly — the `sersic_lens_light.fits` models
in `q1_slde/lens/lens/<id>/result/` (322 lenses) have the correct profile/peak/sky
by construction — or (b) match by DIRECT visual comparison: render one deflector,
put it beside a real eval cutout at the same asinh stretch, and tune (brightness,
size, PSF, envelope) until they are indistinguishable by eye. Nurkyz previously
preferred real galaxy images over smooth models, but nothing else has worked, so
option (a) is worth revisiting with them.
**Also re-open the NOISE by eye:** sky-RMS "matched" numerically (0.0057 vs 0.0059)
but the eye says too noisy. Consider LF_EUC_SKY_SCALE (currently 2.2) too high, or
the deflector faintness leaving noise uncovered. Compare our background to a real
eval cutout's background directly.

## 2. ⚠️ GOTCHAS (read before measuring anything)
1. **This agent's measurements were UNRELIABLE and contradicted each other and the
   eye.** Pixel-scale confusion (native render 0.05″/px, euclidised 0.10″/px via
   2×2 bin; an arc-geometry estimate gave 0.0457; the deflector-only renders were
   contaminated by backdrop galaxies). Do NOT trust a metric until it's cross-
   checked against the eye on the gallery.
2. **Flux-system mismatch:** the PyAutoLens catalog magnitudes (modeling_*.csv,
   e.g. deflector VIS 21.4) are NOT in the same flux units as the eval cutouts
   (`q1_slde_eval_f2p85_zoom.h5`) that the CNN/eye see. Matching the catalog mag
   made deflectors too faint. **The eval cutouts are the brightness ground truth.**
3. **Robust metric that IS trustworthy:** deflector **peak / sky-RMS** (unit-safe).
   Real Euclid eval ~248 (SLACS gate diagnostic ~841). But note even matching it
   did not satisfy the eye — so it's necessary, not sufficient.
4. **Remote shell is csh** — `ssh nurkyz@gpus` lands in csh. Nested quoting breaks
   constantly ("Unmatched", "Badly placed ()'s", "Ambiguous output redirect").
   ALWAYS `ssh nurkyz@gpus 'bash -lc "..."'`, and for anything non-trivial WRITE A
   SCRIPT LOCALLY and `scp` it, then run the file. Do not inline complex Python.
5. **SSH rate-limiting:** rapid-fire connections trip fail2ban ("Connection closed
   by ... port 1922" BEFORE auth). It's not the cluster being down. Batch commands
   into few SSH calls; wait if it starts refusing.

## 3. INFRASTRUCTURE / HOW TO RUN
- Cluster: `ssh nurkyz@gpus` (CUHK gpus.phy.cuhk.edu.hk:1922, csh, SLURM).
- Python: `/home/user/nurkyz/miniconda3/envs/Stronglensing/bin/python`.
- Work dir (scripts, configs, stamps): `/home/user/nurkyz/cosmos_acs/tiles`.
- Pilots land in `/home/user/nurkyz/paltas_g5cosmos_fjNN/` with `sub/` (paltas
  arc-only renders, native 0.05″/px), `assign.csv` (per-image θ_E/stamp/mig_scale),
  `native.h5` (composited), `euclid.h5` (euclidised = final), `euclid_sel.h5`
  (arc-visibility selected = the training set).
- Real Q1: `/home/user/nurkyz/cosmos_acs/q1_slde/` — `modeling_*.csv` (θ_E, mags,
  magnification, arc S/N, Sersic Re/n/q), `q1_slde_eval_f2p85_zoom.h5` (real eval
  cutouts = ground truth), `lens/lens/<id>/result/*.fits` (per-lens model images:
  `source_light.fits` = arc-only, `sersic_lens_light.fits` = deflector-only).
- Deflector stamp library: `deflector_stamps_lrg2b_raw.h5` (shallow HST LRGs).
- Manifests: `/home/user/nurkyz/paltas_g5_c21_pilot/manifest_match*.csv`
  (`manifest_match_abs.csv` = absolute source offset r_max 0.4).
- Local repo (worktree): `/Users/nurkyz/code/LensFusion`. Pipeline code in
  `pipeline/`, analysis scripts in `analysis/`, docs in `docs/`.
- **Gallery (how Nurkyz eyeballs):** `_local/reviews/<name>/` has `build.py`
  (reads `raw/euclid.h5` + `raw/euclid_sel.h5`, writes per-card thumbs/details +
  a side-by-side), served with `python3 -m http.server 8899 --bind 127.0.0.1`.
  Nurkyz opens localhost:8899, rates by card number + issue. ALWAYS put a
  real-vs-sim side-by-side (`side_by_side_real_sim.py`) at the top.
- Pilot pattern: edit manifest/config/hybrid_combine → sbatch a pilot (render →
  g2_join_assign → hybrid_combine → euclidise → euclidise_arcs →
  arc_visibility_select) → build+serve gallery → Nurkyz eyeballs. A re-composite
  (no re-render) is fast: reuse `sub/` + `assign.csv`, just re-run hybrid_combine
  onward. Full re-render ~15-20 min; re-composite ~5 min.

## 4. THE COMPLETE RECIPE (current best = fj18/fj13; carry ALL of it, change one knob)
- **Manifest:** `--match_theta` (θ_E→real Q1 0.70/0.88/1.13); e1,e2 from real q;
  z_source ~N(2.0,0.6); isophote m3,m4 multipoles; z-migration mig_scale/mig_sb +
  evo_q 1.2; **ABSOLUTE source offset** r_max 0.4 (`add_src_offset.py absolute 0.4`).
- **Render** (`config_lensfusion_acs_g5cosmos.py`): LF_SB_CUT 21.5,
  LF_MIN_FLUX_RADIUS 1.0, LF_MIN_SIZE_PX 8, LF_SRC_ABSMAG −24.5, LF_SRC_MAX_RE_ARCSEC
  0.3, **LF_MAG_CUT 2.0**, PSF kernel_00_extended.
- **Composite** (`hybrid_combine.py`): `--deflector_fj --fj_mag0 19.2 --fj_slope 4.5
  --fj_theta0 0.88 --fj_scatter 1.15 --fj_mag_min 17.0 --fj_mag_max 21.2`
  (**NOTE: mag0 19.2 raises peak/sky but Nurkyz still sees dots — this knob is NOT
  settled**); `--deflector_envelope 4.4` (de Vauc wings, weak effect);
  `--deflector_edgesmooth 1.5`; `--deflector_jitter 1.0`; companions
  `--companion_rate_lo 0 --companion_rate_hi 3 --companion_flux_pct 35
  --companion_rmin 30 --companion_area_uniform`; `--arc_poisson`.
- **Euclidise** (`euclidise.py`, in ~/einstein_cnn): LF_EUC_SKY_SCALE 2.2 (**maybe
  too high — Nurkyz says noisy**), LF_EUC_NOISE_CORR 0.45.
- **Selection** (`arc_visibility_select.py`): `--thresh 6 --min_extent 100
  --min_sky_snr 7.6`.

## 5. WHAT IS MATCHED (the wins — keep these, don't regress)
- θ_E distribution (--match_theta).
- Arc VIS mag ≈ real (~22.3-22.5).
- **Arc↔deflector magnification COUPLING** — real physics restored via the
  ABSOLUTE source offset (C49): big lens → bright arc; small lens → faint arc.
  rho(arc,θ_E) −0.15 ≈ real −0.11; small-θ arc-brighter-than-deflector ~30% = real.
- Arc completeness (partial arcs, ~15% near-full ring vs real 17%) — via absolute
  offset placing the source off-axis.
- Deflector faint-tail truncated to real's range (no invisible-deflector tail).
- Companions sparse (~1/img); backdrop noise correlation 0.45; multipoles.
- Square postage-stamp edge fixed (peak-preserving edge-smooth, NOT a taper).

## 6. FIX INVENTORY (C-rows; details in COMMITMENTS.md)
- C40/C44 Faber-Jackson deflector brightness (mag0, slope 4.5, scatter 1.15).
- C43 deflector edge-smooth 1.5 (peak-preserving; square-cut fix).
- C45 mag_cut 2.0 (magnification → real median 2.6).
- C46 completeness match (emergent from C45+C49).
- C48 selection sky-SNR floor 7.6 (real-comparable arc S/N; drops diffuse blobs).
- C49 ABSOLUTE source offset r_max 0.4 (the magnification–θ_E coupling fix — the
  most important physics win; do NOT revert to θ_E-scaled).
- C50 FJ faint-tail truncated-normal [mag_min,mag_max].
- C51 source max-Re 0.3″ (thins arcs; partial).
- C52 Q1SourceCatalog swap — TRIED (fj15/16) to fix arc thickness/clumpiness;
  REGRESSED brightness+coupling (compact real sources over-magnify); reverted.
- C54 deflector envelope + mag0 19.2 — TRIED to fix the dots; peak/sky improved but
  **Nurkyz still sees dots → NOT solved.**

## 7. RECOMMENDED NEXT STEPS (new agent)
1. **Deflector appearance is the blocker.** Work visually only. Render a few
   deflectors, montage beside real eval cutouts at identical stretch, and iterate
   until indistinguishable. Seriously try REAL deflector light (sersic_lens_light).
2. **Noise:** compare our euclidised background to real eval-cutout background by
   eye; if ours is louder, lower LF_EUC_SKY_SCALE.
3. Only after the deflector + noise look right by eye, re-judge arc thickness /
   selection rate (the arc-visibility metric shifts when the deflector changes).
4. Keep the §5 wins frozen; change ONE knob per pilot; always serve a real-vs-sim
   gallery for Nurkyz.

## 8. Broader project context (not GEN5-blocking, but live)
- Post-GEN5 plan: train CNN on GEN5 → evaluate on real Euclid Q1 (does realism
  close the sim-to-real gap?) → domain adaptation (C22) → LEMON native-Euclid
  head-to-head (C34) → UQ paper section (C23) → Roman arm (§2R). See MASTER_PLAN
  §1R endgame ladder + GEN5_REALISM_PLAN.md.
- Roman uncertainty (prof question, answered): the submitted θ_E_sigma is a learned
  aleatoric (μ, logσ²) NLL head + test-time-augmentation spread, recalibrated by a
  single scale fit on our OWN sim-val split — NOT from the challenge data. Code:
  training/train_cnn_paltas.py (NLL), predict_real_lenses_paltas.py (TTA+sigma),
  recalibrate_sigma.py. Returned Goodness≈0.95 confirms calibration transferred.
- Pre-generation blockers still open: C2 (q_mass–q_light fit), C31 (evo_q confirm),
  plus these deflector/noise realism issues, then Nurkyz >1k-image sign-off.

## 9. Key docs
- `docs/GEN5_FIX_LIST.md` — the physically-ordered fix list (deflector = #0).
- `docs/GEN5_REALISM_PLAN.md` — property-by-property checklist + complete recipe.
- `docs/COMMITMENTS.md` — full C-row ledger.
- `docs/MASTER_PLAN.md` — overall project + endgame ladder.
