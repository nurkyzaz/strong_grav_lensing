# How it works — GEN4, GEN5, the CNN, and uncertainty

The one-stop guide: what the two training-data generators are, how the CNN works and
what it's trained on, how uncertainty is produced, and **exactly what to run**. For deeper
detail: [`GENERATOR_AND_CODEBASE_REFERENCE.md`](GENERATOR_AND_CODEBASE_REFERENCE.md)
(generator internals, units) and [`GEN5_PIPELINE.md`](GEN5_PIPELINE.md) (the GEN5 recipe).

---

## What this project is

A convolutional neural network that reads **one** lensed-galaxy image and predicts the
**Einstein radius θ_E** (a single number, in arcsec). It's trained on physically realistic
simulations and validated on real lenses with known θ_E. "GEN4" and "GEN5" are two
generations of *training data*, aimed at two instruments (HST and Euclid).

## The core idea shared by GEN4 and GEN5

**Physical self-consistency.** Each simulated system is built from *one real galaxy* that
supplies both:
- the lens **light** — its real image (a real cutout, or its fitted light profile), and
- the lens **mass** — from its measured SDSS velocity dispersion σ_v → θ_E (via the
  singular isothermal sphere relation).

So the light→mass channel a human modeler relies on is present in the training data. The
lensed arc is a **real COSMOS source galaxy** ray-traced (paltas + lenstronomy) through
that mass model, and the final image is assembled from real ingredients (real deflector
light, real empty-sky background, real instrument PSF) calibrated to real flux units
(electrons/second). The CNN then learns θ_E straight from the pixels.

## GEN4 — native HST

- **What it is:** training images in the native **HST ACS/WFC F814W** domain.
- **How it works:** the deflector is a **real HST early-type galaxy cutout** at its native
  brightness; its mass comes from its own SDSS σ_v. Real arc + real deflector + real sky,
  no instrument degradation step.
- **Best at:** HST lenses (SLACS / S4TM), especially the lower-θ range.
- **Pipeline:** `g1b_measure_stamps.py` (measure galaxies) → `g2_make_manifest.py`
  (one self-consistent system per row) → `run_paltas_pilot.py` + a `config_lensfusion_acs*`
  config (render the arc) → `hybrid_combine.py` (add real deflector + sky + companions +
  noise). Full detail: `GENERATOR_AND_CODEBASE_REFERENCE.md`.

## GEN5 — native Euclid Q1

- **What it is:** training images in the **Euclid VIS (Q1)** domain.
- **The key move:** inject the **real Euclid Q1 deflector light** — each Q1 lens's own
  fitted VIS Sérsic profile — calibrated into the eval-cutout flux system. This is GEN4's
  "real light, native amplitude, tied to mass" principle applied to the Euclid instrument
  (earlier synthetic-deflector attempts produced unrealistic "dots").
- **Pipeline (stages A–G):** `g5_make_manifest.py` (population, z-migrated, with
  isophote-anchored m=3,4 multipoles) → render arc → `hybrid_combine.py` **(deflector
  off)** → `euclidise.py` (Euclid VIS PSF + matched noise) → `inject_q1_deflector.py`
  (the real deflector light) → `arc_visibility_select.py` (keep visibly-lensed images) →
  `merge_shards.py` (**deflector-disjoint** train/val split). Full detail:
  `GEN5_PIPELINE.md`.

## GEN4 vs GEN5 in one line

Same population model and same self-consistency idea, **rendered for different
instruments** (HST vs Euclid). Each model is strongest in its own domain — this
"instrument specialization" is expected and intentional.

---

## The CNN — how it works, and on what

Code: [`training/train_cnn_paltas.py`](../training/train_cnn_paltas.py), class
`EinsteinCNNScale`.

- **Input:** one grayscale image, normalized **per image** with `arcsinh` compression
  (tames the bright lens centre) then standardized (subtract mean, divide by std). This
  removes the absolute flux level on purpose — θ_E is a geometric quantity.
- **Backbone (default `--arch resnet`, ~2.8M params):** a compact ResNet — a 7×7 stride-2
  stem, then four residual stages with 32 → 64 → 128 → 256 channels, then global average
  pooling. Other choices: `inceptionnext`, `convnextv2`, `resnet50`, `logpolar`.
- **Scale conditioning (why it generalizes across instruments):** the image's angular
  pixel scale is fed in as a **scalar** alongside the pooled image features, so a single
  model handles different fields-of-view / pixel scales (HST, Euclid, Roman) with no
  accuracy loss.
- **Output head:** either a point estimate of θ_E, or — with `--nll` — a Gaussian
  `(μ, log σ²)`, i.e. θ_E **and** a per-lens error bar (see Uncertainty below).
- **Label:** θ_E in arcsec, in the **SIE b_SIE convention** (matches the Bolton et al.
  2008 ground truth directly).
- **Training:** Adam optimizer; Huber loss (point) or Gaussian-NLL (`--nll`); dihedral
  (flip/90°-rotation) augmentation.

---

## Uncertainty — how it's produced

Two independent sources, combined into one predictive error bar:

1. **Aleatoric (irreducible data noise)** — the `--nll` head predicts `log σ²` for each
   image, trained by the Gaussian-NLL loss `0.5·(logσ² + (y−μ)²/σ²)`
   (`gaussian_nll()` in the training script). σ_aleatoric = exp(½·logσ²).
2. **Epistemic (model uncertainty)** — train a **deep ensemble** (several models with
   different `--seed`); the spread of their predictions is σ_epistemic. (This is the
   ensemble method recommended for the paper.)
3. **Total predictive σ = √(σ_aleatoric² + σ_epistemic²).**
4. **Test-time augmentation (TTA):** at inference, average 8 dihedral (D4) views of each
   image for a more robust point estimate (`--tta`).
5. **Calibration:** raw σ tends to be a bit under-confident; `training/recalibrate_sigma.py`
   rescales it so the stated coverage matches reality. The rescaled σ correlates with the
   true error (it's informative, not a flat number).

---

## How to run

**Setup** (once): `pip install -r requirements.txt` (Python 3.8; see the README for the
galsim/torch notes). Large data + model weights live on the cluster, not in the repo.

**1. Generate training data**
- GEN4 (HST): the manifest → render → `hybrid_combine.py` chain in
  `GENERATOR_AND_CODEBASE_REFERENCE.md` §1.
- GEN5 (Euclid): the A–G stages in `GEN5_PIPELINE.md`. At scale on the cluster this runs
  as a self-scheduling worker pool (`launch_v2.sh`).

**2. Train the CNN**
```
python training/train_cnn_paltas.py \
  --train_file <train.h5> --val_file <val.h5> \
  --arch resnet --nll --norm asinh \
  --min_theta_e 0.4 --augment --epochs 40 --lr 1e-3 \
  --out_ckpt einstein_cnn.pt
```
For a **deep ensemble**, run this several times with different `--seed` → one checkpoint
per member. (`--help` lists every flag, including the optional domain-adaptation options.)

**3. Predict / evaluate on real lenses**
```
python training/predict_real_lenses_paltas.py \
  --ckpt einstein_cnn.pt --real real_slacs_images.h5 --tta --out theta_E_pred.csv

python training/metrics_real.py theta_E_pred.csv          # bias / RMSE / R² + scatter plot
```
Combine ensemble members' CSVs for the epistemic spread; run `recalibrate_sigma.py` on the
sim-validation split to set the σ scale.

> **Rule:** never train or tune on the benchmark files (`real_slacs_images.h5`,
> `real_s4tm_images.h5`). They are held out for evaluation only; model selection is done on
> the simulated validation split.
