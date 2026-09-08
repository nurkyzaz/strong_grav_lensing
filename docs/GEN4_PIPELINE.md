# GEN4 — how the HST pipeline works

GEN4 is the **native-HST** training-data generator: real HST early-type galaxies as
deflectors, each with its mass set self-consistently from its own measured velocity
dispersion. It is the base pipeline; GEN5 ([`GEN5_PIPELINE.md`](GEN5_PIPELINE.md)) applies
the same idea to the Euclid instrument. Big picture: [`HOW_IT_WORKS.md`](HOW_IT_WORKS.md);
generator internals + units: [`GENERATOR_AND_CODEBASE_REFERENCE.md`](GENERATOR_AND_CODEBASE_REFERENCE.md).

## 0. The one idea

**Physical self-consistency: one real galaxy provides both the lens light and the lens
mass.** The deflector is a real HST cutout pasted at its **native amplitude** (its own
measured e⁻/s flux and morphology, nothing rescaled), and its mass — hence θ_E — comes
from that same galaxy's SDSS velocity dispersion. So the luminosity→mass relation a human
modeler uses is built into the training data, not faked.

Everything lives in one physical flux system: **electrons/second, F814W AB zeropoint
25.94, on a 128 px @ 0.05″/px = 6.4″ grid** (matching the SLACS benchmark cutouts).

## 1. Pipeline stages (per training image)

**(A) Measure real galaxies** — `g1b_measure_stamps.py`, `measure_real_deflector_mags.py`
Each real HST early-type cutout is crossmatched to SDSS (σ_v, z) and measured for light
shape (mag, Re, axis ratio q, PA) and **isophote parameters (a3/b3/a4/b4 → m3/m4)** for
multipole anchoring → `tables/g1b_kinematics_v1.csv`. Aperture photometry on the SLACS
cutouts → `lens_light_empirical.csv` (the joint (mag, Re) deflector-light prior; measured
deflector mags median ≈ 17.6).

**(B) Population manifest** — `g2_make_manifest.py` (and `g4b_make_manifest.py`)
One row per training image = one self-consistent system:
- **θ_E from σ_v** via the singular isothermal sphere relation
  `θ_E = 4π (σ_v/c)² · D_ls/D_s`, with σ_v from the SDSS fibre velocity dispersion
  (fibre→SIE correction f_SIS = 0.948, plus ~7% intrinsic scatter in θ_E).
- **Mass shape = measured light shape ⊕ scatter** (ellipticity from the galaxy's own q/PA).
- Importance-sampling ("tempered" prior) keeps the effective θ_E distribution wide while
  every image stays physical.
- The `g4b` variant upgrades the deflector to `PEMDShearFourMultipole` with the manifest's
  **isophote-anchored m=3,4 multipoles** and per-row migrated z_lens.

**(C) Arc render** — `run_paltas_pilot.py` + `config_lensfusion_acs_g4b.py`
Reads the manifest row and ray-traces (paltas + lenstronomy) a **real COSMOS source
galaxy** (`COSMOSCatalog` / `HighSBCOSMOSCatalog`, GREAT3-vetted `COSMOS_23.5`) through the
PEMD + shear (+ multipole) mass → a **noiseless** lensed-source image in e⁻/s. The source
flux is renormalized to the Newton et al. measured SLACS **source** magnitudes (mean ≈ 24.3
at z ≈ 0.65). PSF = real HST focus-diverse ePSF.

**(D) Assemble the hybrid image** — `hybrid_combine.py` (`--deflector_manifest` /
`--deflector_stamps`)
```
image = paltas noiseless source render        (e⁻/s)
      + real HST deflector stamp              (e⁻/s, NATIVE amplitude)   ← the GEN4 core
      + real empty-sky HST cutout             (e⁻/s: real correlated noise + field galaxies)
      + real field companions                 (e⁻/s, ~Poisson(U[lo,hi]) per image)
      + Gaussian top-up → each image's sky-RMS matched to the real SLACS distribution
      (+ optional Poisson shot noise on the arc, --arc_poisson)
```
All summed in e⁻/s → one physical native-HST image. (The **real empty-sky backdrops** were
the single dominant realism ingredient in ablation — training on plain Gaussian noise made
the net read real correlated background as lensed flux and over-predict.)

**(E) Instrument operator (optional)** — `euclidise.py`
The native-HST arm stops at (D). For the **Euclidised-HST** variant (used to compare in
Euclid's domain), `euclidise.py` degrades the image to Euclid VIS: PSF-match ACS→VIS with
the real matching kernel, 2×2 bin to 100 mas/px, add survey-depth Poisson noise, then
upsample back to 128 px so the same CNN applies unchanged.

**(F) Train / evaluate** — `train_cnn_paltas.py`, `predict_real_lenses_paltas.py`
Same model and commands as GEN5 (see `HOW_IT_WORKS.md` §How to run). Frozen benchmark:
62 SLACS + 40 S4TM lenses, Bolton et al. 2008 SIE b_SIE ground truth.

## 2. Results (real benchmark, Bolton b_SIE)

| domain | bias | RMSE | R² |
|---|---|---|---|
| native HST | ≈ +0.005″ | ≈ 0.152″ | ≈ 0.64 (and ≈ 0.90 / RMSE 0.088″ on the lower-mass S4TM sample) |
| Euclidised HST | ≈ −0.010″ | ≈ 0.137″ | ≈ 0.71 |

GEN4 is strongest on the HST domain (especially low-θ / S4TM); GEN5 is strongest on native
Euclid — the intended instrument-specialization crossover.

## 3. GEN4 vs GEN5 at a glance

| | GEN4 | GEN5 |
|---|---|---|
| Target instrument | native HST (ACS/WFC F814W) | native Euclid VIS (Q1) |
| Deflector light | real **HST** galaxy cutout, native amplitude | real **Euclid Q1** deflector (fitted VIS Sérsic), calibrated to the eval cutout |
| Where the deflector is added | in `hybrid_combine.py` (before any degradation) | **after** `euclidise.py`, via `inject_q1_deflector.py` |
| Manifest builder | `g2_make_manifest.py` / `g4b_make_manifest.py` | `g5_make_manifest.py` (z-migrated, multipoles) |
| Instrument step | none (or optional `euclidise.py` for Euclidised-HST) | `euclidise.py` is a core stage |
| Shared | same self-consistent σ_v→θ_E idea, real COSMOS sources, paltas rendering, and the same CNN | ← same |
