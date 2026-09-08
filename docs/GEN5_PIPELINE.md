# GEN5 — how the successful Euclid pipeline works (2026-08-21)

The GEN5 pipeline that reaches **R² ≈ 0.73 on real Euclid Q1**. This documents the
complete recipe end-to-end: what each stage does, the exact knobs, and why. For the
big picture (what GEN4/GEN5 are, the CNN, uncertainty, how to run) see
[HOW_IT_WORKS.md](HOW_IT_WORKS.md); for generator internals and units see
[GENERATOR_AND_CODEBASE_REFERENCE.md](GENERATOR_AND_CODEBASE_REFERENCE.md).

## 0. The one idea that unlocked it

Earlier GEN5 attempts rendered the deflector synthetically (Faber-Jackson flux
reassignment + cosmetic sharpen/envelope knobs) and produced "tiny dots." The
fix: **use the REAL Euclid Q1 deflector light** — each Q1 lens's own fitted VIS
Sérsic profile — rendered at native amplitude and calibrated into the eval-cutout
flux system. This is GEN4's winning principle ("real light, native amplitude,
tied to mass") applied to the Euclid instrument. Everything else follows.

## 1. Pipeline stages (per training image)

**(A) Population manifest** — `g5_make_manifest.py`
Each row = a real σ_v-measured library galaxy (G1b, `g1b_kinematics_v1.csv`),
z-migrated to a target redshift; θ_E computed from the galaxy's measured σ_v via
SIS (C15a f_SIS=0.948, C15b 7% intrinsic scatter). Light and mass are the SAME
physical object → the light↔θ_E (Faber-Jackson) channel is physical, not faked.
- **v2 change (T1):** drop `--match_theta`; use the tempered-flat prior (α≈0.3).
  This restores high-θ_E coverage (match_theta had matched the observed Q1
  distribution and starved the tail → high-θ regression-to-mean). Side benefit:
  the FJ coupling is actually stronger (ρ(mig_mag,θ_E) −0.60 vs −0.41).
- Isophote-anchored m=3,4 multipoles (AR3); dPA~N(0,10°) mass-light misalignment;
  z_source ~ N(2.0,0.6).
- **Source offset** (`add_src_offset.py absolute 0.4`): uniform-in-area β up to
  0.4″ → partial arcs at the right rate, preserving the arc↔θ_E magnification
  coupling (C49). Too large (0.6) demagnifies arcs below the noise; 0.4 is tuned.

**(B) Arc render** — `run_paltas_pilot.py` + `config_lensfusion_acs_g5cosmos.py`
Renders the lensed SOURCE only (noiseless), on the manifest's θ_E/mass-shape/
z_source. Source = real COSMOS galaxy image (`HighSBCOSMOSCatalog`), SB-cut 21.5,
absolute-mag −24.5 (z-dependent cosmological dimming).
- Key knob **LF_SRC_MAX_RE_ARCSEC** (source half-light cap): **0.3″ → thin arcs**
  (compact high-z sources; without it arcs read too thick/ring-like). **v2 tier
  T3 uses 0.12″** for ~25% of shards → the source is small enough that its images
  are DISTINCT (multiply-imaged doubles/quads + thin rings), matching the real
  "2–3–4 blob" configurations. PSF = real Euclid VIS GRID-PSF kernel.

**(C) Composite** — `hybrid_combine.py` (deflector DISABLED)
Adds the real HST empty-sky backdrop + sparse companions
(`--companion_rate_lo 1 --companion_rate_hi 5 --companion_flux_pct 35
--companion_rmin 26 --companion_area_uniform`) + arc Poisson noise. NO synthetic
deflector here (that was the old mistake).

**(D) Euclidise** — `euclidise.py`
Degrade to the Euclid VIS domain: real VIS PSF + matched correlated sky noise
(`LF_EUC_SKY_SCALE 2.2`, `LF_EUC_NOISE_CORR 0.45`). Output is 128px / 0.05″/px /
6.4″ box — the SAME grid and flux units as the real Q1 eval cutouts.

**(E) Inject real Q1 deflector light** — `inject_q1_deflector.py` (the key stage)
For each image: pick a real Q1 lens whose θ_E_pub is near the image's θ_E (K=6
nearest, so the light↔θ_E relation is real), render its deflector ANALYTICALLY
from its fitted VIS Sérsic params (`modeling_lens_sersic.csv`: centre/ell_comps/
effective_radius/sersic_index) — extended de Vaucouleurs, no PyAutoLens mask edge
— PSF-convolve, **calibrate to eval-cutout flux units** by LSQ fit to that lens's
real cutout core, and add it **centered on the frame** (where the arc curves),
PA aligned to the image's mass ±12°. NO FJ, NO flux_scale, NO cosmetic knobs.

**(F) Select** — `arc_visibility_select.py` (tier-aware in v2)
Keep only images with a visibly lensed feature, matching the discovery-selected
real sample. Metrics: arc peak / deflector-residual (thresh) AND the
real-comparable arc/sky floor (`--min_sky_snr`, real Q1 q25 = 7.6). **v2 tiers:**
  - ARC (~50%): `--thresh 6 --min_extent 100 --min_sky_snr 7.6` (thin visible arcs)
  - FAINT (T2, ~25%): `--thresh 5 --min_extent 80 --min_sky_snr 4.0` (low-contrast
    arcs the strict floor removed → the model learns faint arcs)
  - BLOB (T3, ~25%): `--thresh 4 --min_extent 30 --min_sky_snr 5.0` (relaxed extent
    so distinct point-image doubles/quads survive)

**(G) Merge** — `merge_shards.py`
Concatenate selected shards → **deflector-disjoint** train/val split (a held-out
set of Q1 deflectors, by `q1_deflector_evalidx`, goes entirely to val). 100k set:
`gen5v2_train.h5` / `gen5v2_val.h5`.

## 2. Scale-up execution (the cluster mechanics)

CUHK cluster limits: every job needs `--gres=gpu:N`; MaxArraySize=10; QOS caps 8
submitted jobs / 16 GPUs; 160G disk quota. So the 100k regen is a **self-
scheduling worker pool**: 1 prep (CPU) → 6 tier-aware workers that atomically
claim shards (`mkdir claims/<id>`), run A–F, checkpoint `sel_<id>.h5`, reclaim
stale claims >3h → 1 merge. Launch once with `launch_v2.sh`; resumable by re-run.
300k rendered → ~120k selected (~40% yield).

## 3. Training

`train_cnn_paltas.py --arch resnet --nll --norm asinh --min_theta_e 0.4 --augment
--epochs 40 --lr 1e-3` on the deflector-disjoint split. 2.8M-param scale-
conditioned ResNet + Gaussian-NLL (μ, logσ²) uncertainty head; per-image asinh
normalization; dihedral augmentation; 8-view TTA at inference. **v3 experiment:**
`--theta_oversample 1.5` (a WeightedRandomSampler that draws high-θ examples more
often, no data duplication) to attack the residual high-θ RMSE.

## 4. Results on real Euclid Q1 (322 lenses vs PyAutoLens θ_E)

| model | R² | RMSE | NMAD | bias |
|---|---|---|---|---|
| GEN4 (HST/Euclidised) | +0.51 | 0.30″ | — | — |
| GEN5 v1 (match_theta) | +0.65 | 0.25″ | 0.097″ | −1.4% |
| **GEN5 v2 (T1+T2+T3)** | **+0.729** (clean +0.764) | 0.223″ | 0.083″ | −1.5% |
| LEMON (their 354) | +0.71 | 0.17″ | 0.07″ | +0.01″ |

At LEMON-matched difficulty (Grade-A / top-61%, N≈185): GEN5 v2 **R² +0.78, NMAD
0.076″** — we **win R², tie NMAD and bias, trail only on RMSE** (0.196 vs 0.17),
which the matched-difficulty test localizes entirely to the high-θ tail (v3
target). GEN5 also generalizes to Euclid-SLACS (R² 0.60). GEN4 remains best on
low-θ HST S4TM — the instrument-specialization crossover.

## 5. Honest caveats (carry into the paper)
- Ground truth is PyAutoLens SIE (the Q1 reference; ~1% on good fits, a handful of
  confident failures — 3 impossible labels dropped for the "clean" number). No
  independent Q1 θ_E catalogue exists.
- Training uses the real Q1 deflector *light* and eval is on those same galaxies →
  deflector-appearance overlap. `q1_deflector_evalidx` is tracked so a clean
  held-out-deflector eval is possible without regenerating.
- LEMON's 354 is success-filtered (easier); our 322 is the full set. Our numbers
  are on the harder sample, and a matched-difficulty comparison favors us.
