# GENERATOR & CODEBASE REFERENCE

Authoritative, code-grounded description of how the LensFusion θ_E training-data
generator works, what every core script does, and the full photometry / units /
normalization chain. Written 2026-08-01 by reading the actual cluster code
(`~/cosmos_acs/tiles/`, `~/einstein_cnn/`), not the older plan docs. Where a
line cites a file, it was verified against that file. If code changes, update
this file. For the big-picture guide (GEN4/GEN5, the CNN, uncertainty, how to run)
see [HOW_IT_WORKS.md](HOW_IT_WORKS.md).

---

## 0. One-paragraph overview

We train a small CNN to regress a strong lens's Einstein radius θ_E from a single
HST ACS/WFC F814W image (or its Euclid / Roman rendering). The training images are
**hybrid**: real physics (paltas + lenstronomy ray-tracing) painted with real
ingredients (real COSMOS source galaxies, real HST deflector-galaxy cutouts, real
empty-sky backgrounds, real focus-diverse PSFs), calibrated to real photometric
units. The defining idea since GEN4 is **physical self-consistency**: each training
system is ONE real galaxy that provides both the lens *light* (its cutout) and the
lens *mass* (its measured SDSS velocity dispersion σ_v → θ_E), so the
luminosity→mass channel a human modeler uses is present in training.

---

## 1. The generator, end to end

The pipeline is a chain of scripts. One "population draw" → three instrument
renderings (native HST / Euclid / Roman). Data + compute live on the cluster.

```
 (A) MEASURE real galaxies      g1_measure_stamps.py / g1b_measure_stamps.py
        real HST early-type cutouts  →  per-stamp (σ_v, z_l, mag, Re, q, PA,
        + SDSS spectroscopy              isophote a3/b3/a4/b4, m3/m4)
                                         → tables/g1b_kinematics_v1.csv (488 stamps)
        real SLACS deflectors → aperture photometry → lens_light_empirical.csv
                                         (measure_real_deflector_mags.py)

 (B) BUILD THE MANIFEST         g2_make_manifest.py (GEN4) / g5_make_manifest.py (GEN5)
        one row per training image = one physically self-consistent system:
        pick a library galaxy → draw z_source → theta_E COMPUTED from σ_v (SIS);
        mass shape = measured light shape ⊕ scatter; GEN5 adds z-migration +
        isophote-anchored m=3,4 multipoles. Importance-sampling ("tempered"
        prior) keeps the effective θ_E distribution wide while every image stays
        physical.  → a manifest CSV (one row per render).

 (C) RENDER (paltas)            config_lensfusion_acs*.py  +  paltas/lenstronomy
        reads the manifest row → ray-traces the COSMOS source through the
        PEMD(+shear)(+multipole) mass → a NOISELESS lensed-source image in e-/s.

 (D) ASSEMBLE (hybrid image)    hybrid_combine.py
        noiseless source render (e-/s)
        + real deflector-galaxy stamp (e-/s, native amplitude)
        + real empty-sky HST cutout (e-/s, correlated real noise + field neighbors)
        + real field companions (e-/s)
        + Gaussian top-up so the image's sky-RMS matches real SLACS
        (+ optional AR1 Poisson shot noise on the arc)
        → the native-HST training image (still physical e-/s units).

 (E) INSTRUMENT OPERATOR        euclidise.py (Euclid)  /  Roman rendering (G5a)
        native-HST image → degrade to Euclid VIS or Roman WFI (flux ZP, PSF
        match, resample, survey-depth noise). Native-HST arm skips this.

 (F) TRAIN                      train_cnn_paltas.py
        per-image asinh + z-score normalization → scale-conditioned ResNet /
        InceptionNeXt with a (μ, log σ²) head → θ_E + uncertainty.

 (G) EVALUATE                   metrics_real.py + eval drivers
        frozen real benchmark (62 SLACS + 40 S4TM, Bolton b_SIE GT), logged
        with a running eval count. Model selection on sim-val ONLY.
```

---

## 2. Photometry, units & normalization  ← the research-meeting question

**Short answer to "what are the units, and do you normalize deflectors and
sources?":** the raw data and every generated component live in one physical
flux system — **electrons per second (e⁻/s), AB zeropoint 25.94 for F814W**. Each
light component (deflector, source, companions) is independently *flux-calibrated*
to a physical magnitude in that system, then all are **summed into one image**.
The CNN never sees those absolute fluxes: at training input the *combined* image
is compressed with `arcsinh` and **standardized per image** (subtract its mean,
divide by its std), which removes the absolute level entirely. So we normalize
**once, on the final image — not per component.** θ_E is a geometric quantity, so
this is deliberate.

### 2.1 Units of the raw data
- HST ACS/WFC F814W drizzled `_drc` cutouts: pixels are in **electrons/second**.
- **AB zeropoint ZP_HST = 25.94** (F814W). Conversion:
  `mag_AB = 25.94 − 2.5·log₁₀(flux[e⁻/s])`  and  `flux = 10^(−0.4·(mag − 25.94))`.
- Grid: **128 px @ 0.05″/px = 6.4″** field of view (matches the SLACS benchmark).
- Every generated ingredient (paltas render, deflector stamp, empty-sky backdrop,
  companions) is produced in **e⁻/s on the same 0.05″ grid at ZP 25.94** — a
  single consistent flux system (`config_lensfusion_acs.py`, `hybrid_combine.py`).

### 2.2 Deflector (lens galaxy) magnitude — how we *measure* it
`measure_real_deflector_mags.py` on the 62 real SLACS cutouts:
1. sum pixels in a **r = 2″ circular aperture** (40 px);
2. subtract a **sigma-clipped sky** level (median of four 16×16 corner boxes);
3. `mag = 25.94 − 2.5·log₁₀(aperture_flux)`.
→ measured F814W deflector mags: **median ≈ 17.6, range [15.9, 19.3]**. (Printed
caveat: the aperture includes some arc light → deflector mags run slightly bright;
small for SLACS where the deflector dominates.) These feed the joint (mag, Re)
prior `lens_light_empirical.csv`.

How the deflector light enters the image:
- **Pre-GEN4** (`config_lensfusion_acs.py`): a **parametric Sérsic** (n=4 de
  Vaucouleurs) whose apparent magnitude is *drawn* from the empirical prior
  ([15.6, 19.7]), jointly with Re (`ApparentSersic` + `cross_object`).
- **GEN4+** (`hybrid_combine.py`, `--deflector_manifest`): the **real HST galaxy
  stamp** is pasted centered at its **NATIVE amplitude** — its own measured e⁻/s
  flux and morphology are both used, nothing is rescaled. (An earlier Path-B
  variant instead scaled each stamp's total flux to a drawn empirical magnitude
  with rank-matched Re; superseded by native-amplitude self-consistency.)

### 2.3 Source (the lensed background galaxy) magnitude
- The source is a **real COSMOS galaxy** (`paltas` `COSMOSCatalog`, the
  `COSMOS_23.5` GREAT3-vetted sample), physically ray-traced through the lens mass.
- Its flux amplitude is set by `mag_to_amplitude` at ZP 25.94. The magnitude is
  the COSMOS galaxy's own catalog photometry, then **renormalized to the
  Newton et al. measured SLACS *source* magnitudes** (`HighSBCOSMOSCatalog.
  normalize_to_mag`; mean ≈ **24.3** at z ≈ 0.65). So: **we do not re-measure the
  SLACS source ourselves — Newton et al. measured the SLACS source apparent
  magnitudes, and we renormalize the COSMOS stamp's flux to that distribution.**
- **GEN5** (`Gen5HighZSource` in `config_lensfusion_acs_g5.py`): after the Newton
  renormalization (calibrated at z≈0.65), the source is **dimmed** by
  `dm = 5·log₁₀(D_L(z_s)/D_L(0.65)) − 2.5·log₁₀((1+z_s)/(1+0.65))`
  (luminosity-distance + flat-fν K-correction) to the row's drawn higher z_source.
  This fixed a Nurkyz-caught bug where the low-z Newton apparent-mag prior was
  overwriting paltas's cosmological dimming (arcs weren't dimming with z).

### 2.4 Field companions
`build_source_stamps.py` cuts **real compact sources** from COSMOS ACS tiles
(e⁻/s, median-subtracted, edge-tapered) into a stamp library; `hybrid_combine.py`
injects ~Poisson(U[lo,hi]) of them per image (real lenses average ~10 field
neighbors/image; early sims had ~0).

### 2.5 Assembly and noise (`hybrid_combine.py`)
```
image = paltas_noiseless_source_render   (e⁻/s)
      + real_deflector_stamp             (e⁻/s, native amplitude)
      + real_empty_HST_cutout            (e⁻/s, median-subtracted: real correlated noise + field galaxies)
      + real_field_companions            (e⁻/s)
      + Gaussian top-up   → each image's sky-RMS matched to the real SLACS sky-RMS distribution
      (+ AR1: optional Poisson shot noise on the arc render, --arc_poisson)
```
All summed in e⁻/s → one physical image. (Real backdrops were the single dominant
realism ingredient in the ablation — training on plain Gaussian noise made the net
read real correlated background as lensed flux and over-predict catastrophically.)

### 2.6 Euclid / Roman operators
`euclidise.py`: flux → Euclid VIS I_E (**ZP 23.9**), PSF-match ACS→VIS with the
real Q1 GRID-PSF matching kernel (`acs2vis_matching_kernel.npy`; Gaussian is an
ablation only), **2×2 sum → 100 mas/px**, Poisson(signal+sky) at the 2280 s EWS
depth (sky variance ×~2.2 for the real Q1 arm — Q1 measures noisier than the
nominal spec), then bilinear upsample **back to 128 px** so the same architecture
and normalization apply unchanged. Roman (G5a) is the analogous WFI rendering.

### 2.7 Normalization at the CNN input (`train_cnn_paltas.py::normalize_images`)
```python
x = np.arcsinh(images / asinh_a)          # asinh compression (a = 1.0)
x = (x − x.mean(per-image)) / (x.std(per-image) + 1e-8)   # per-image z-score
```
- Applied **identically** to the training sims and the real benchmark (the
  `RealBenchmark` loader calls the same function) — no train/test normalization
  mismatch.
- **This removes the absolute flux level / zeropoint at input.** The network reads
  morphology and geometry, not absolute brightness — correct, because θ_E is an
  angular quantity. `arcsinh` compresses the bright deflector core while keeping
  faint arc structure visible.
- The **pixel scale** (arcsec/px) is passed as a *separate* conditioning scalar
  (standardized by dataset mean/std), so the net knows the angular scale of each
  image — essential when mixing native-HST (0.05″) with degraded renderings.
- **Deflector vs source are NOT normalized separately.** They are flux-calibrated
  individually in physical e⁻/s during generation (§2.2–2.4), summed into one
  image (§2.5), and that single image is normalized once here.

---

## 3. Codebase by files (what each core script is for)

Cluster: generator in `~/cosmos_acs/tiles/`, training/eval in `~/einstein_cnn/`.
Repo mirrors: `pipeline/` ← tiles, `training/` ← einstein_cnn, `results/` ← eval
CSVs + logs, `tables/` ← measured catalogs, `analysis/` ← Mac-side analysis.

### Measurement / catalogs
- `g1_measure_stamps.py`, `g1b_measure_stamps.py` — measure each real deflector
  stamp: σ_v/z crossmatch + light shape (mag, Re, q, PA) + **isophote fit
  (a3/b3/a4/b4 → m3/m4)** for the multipole anchoring. Output
  `tables/g1b_kinematics_v1.csv` (**488 stamps**, GEN5 library).
- `measure_real_deflector_mags.py` — aperture photometry on the SLACS cutouts →
  `lens_light_empirical.csv` (joint (mag, Re) deflector-light prior).
- `build_source_stamps.py` — real compact-source stamp library for field
  companions.

### Manifest builders (the physics)
- `g2_make_manifest.py` — **GEN4** self-consistent population: θ_E = 4π(σ_v/c)²
  D_ls/D_s (SIS), σ_v from SDSS fiber velDisp; mass shape = light shape ⊕
  misalignment (ΔPA~N(0,10°), q_mass = q_light ⊕ 0.08); tempered importance
  sampling to keep the effective θ_E wide while preserving the FJ correlation.
- `g4b_make_manifest.py` — expanded-library variant of the above.
- `g5_make_manifest.py` — **GEN5**: adds z-migration (stamp → z_new, zoom+Tolman
  dimming) and **AR3 isophote-anchored m=3,4 multipoles** (mult_a = iso_m·θ_E,
  capped 0.10·θ_E; PA anchored to the light).

### paltas configs (the renderer)
- `config_lensfusion_acs.py` — base HST config: PEMD+shear mass, COSMOS source,
  `ApparentSersic` deflector light, real ePSF, detector (ZP 25.94, 675 s), the
  `mag_cut` anti-blob gate, and the joint (mag, Re) `cross_object` prior.
- `config_lensfusion_acs_g2.py` — manifest-driven (reads θ_E/e1,e2/z_s per row).
- `config_lensfusion_acs_g4b.py` — expanded-library config.
- `config_lensfusion_acs_g5.py` — **GEN5**: `PEMDShearFourMultipole` deflector
  with per-row isophote multipoles + migrated z_lens; `Gen5HighZSource` dimming.
- `config_lensfusion_acs_pathb_euclid.py` — defines `HighSBCOSMOSCatalog`
  (Newton-mag source renormalization).
- `config_lensfusion_acs_nonoise.py` — noiseless wrapper for hybrid assembly.

### Assembly / conversion
- `hybrid_combine.py` — **the image assembler** (§2.5): sum render + deflector
  stamp + real backdrop + companions + matched noise. `--arc_poisson` = AR1.
- `patch_combine_arc_poisson.py` — the AR1 patch.
- `merge_hybrid_shards.py`, `paltas_npy_to_train.py`, `paltas_to_train.py` —
  shard → training-h5 packaging.
- `euclidise.py` / `euclidise_arcs.py` — Euclid VIS operator (§2.6).

### PSF tooling
- `make_acs_psf.py`, `inspect_psf_kernel.py`, `fix_psf_kernel.py`,
  `diagnose_psf_square.py` — build/inspect/repair the empirical ePSF kernel
  (the truncated-kernel "central square" artifact was traced and fixed here).

### Training / evaluation
- `train_cnn_paltas.py` — **the trainer**: `normalize_images` (§2.7), the
  scale-conditioned `EinsteinCNNScale` / `InceptionNeXtScale`, Gaussian-NLL
  (μ, log σ²) head, MMD hooks (the domain-adaptation experiments), TTA.
- `metrics_real.py` — benchmark metrics (bias/RMSE/NMAD/R²/fail, bootstrap CIs).
- `gate_stage0.py`, `ar0_arc_gate.py` — the pilot gates (sky-RMS, peak/sky, arc
  realism) that every dataset version must pass before scale-up.

### Analysis (Mac)
- `analysis/lemon_headtohead_recompute.py` — LEMON vs Bolton head-to-head on the
  exact 29 SLACS (→ `results/lemon_vs_ours_slacs29.csv`).

---

## 4. Generation lineage (GEN0 → GEN5), one line each

- **m3 (pre-project baseline)** — CNN trained on the old forward-operator sims;
  fails on real lenses (R² −1.02): **prior-pull** (predictions collapse to the
  training mean). The problem this project set out to fix.
- **Hybrid v1/v2 (GEN1–2 era)** — paltas + real COSMOS sources + real ePSF + real
  backdrops + calibrated noise + flat wide θ_E prior. R² crosses to positive
  (+0.27); the ablation shows real backdrops dominate.
- **GEN3** — real Euclid Q1 VIS PSF replaces the Gaussian in the Euclid operator;
  faithful Euclid-domain benchmark.
- **GEN4** — **physical self-consistency**: real galaxy = light AND mass, σ_v→θ_E,
  FJ channel. The decisive step: native SLACS R² +0.64, S4TM R² +0.90, Euclid
  R² +0.71. This is the paper's core result.
- **GEN4.5 (AR ladder)** — arc realism: AR1 arc Poisson shot noise + AR2 ΔPA↔shear
  coupling (eval #22) = correctness refinements, flat on the benchmark; AR3
  multipoles designed here, implemented in GEN5.
- **GEN5** — z-migrated high-z population for **Euclid + Roman**: expanded 488-stamp
  library, z-migration (zoom + Tolman dimming), **AR3 isophote-anchored m=3,4
  multipoles**, high-z source dimming. Roman Data Challenge entry (G5a, 6-net
  ensemble). Native real Euclid Q1 still a frontier (R²~0.6, below LEMON's 0.71).

---

## 5. Key data products & labels

- **Frozen benchmark**: `real_slacs_images.h5` (62), `real_s4tm_images.h5` (40);
  GT = Bolton et al. 2008 SIE b_SIE. Never trained on; evals logged with a count.
- **Label**: θ_E in arcsec (SIE b_SIE convention — matches Bolton directly).
- **Deflector library**: `tables/g1b_kinematics_v1.csv` (488 stamps, with σ_v, z,
  light shape, isophote multipoles).
- **Light priors**: `lens_light_empirical.csv` (joint mag–Re).
- **LEMON comparison**: `tables/lemon_predictions/` (their per-lens preds),
  `results/lemon_vs_ours_slacs29.csv` (head-to-head).
