# Strong-lensing θ_E CNN (paltas pipeline)

A convolutional neural network that predicts the **Einstein radius θ_E** from a single
lensed-galaxy image, trained on physically realistic simulations built with
[**paltas**](https://github.com/swagnercarena/paltas) (real COSMOS sources + real
instrument PSFs + real empty-field backdrops + calibrated noise), and validated on a
frozen real-lens benchmark (62 SLACS + 40 S4TM lenses, Bolton et al. 2008 SIE b_SIE
ground truth).

Two instrument domains share one population model: native **HST** (ACS/WFC F814W) and
**Euclid** Q1 (VIS). See `docs/GEN5_PIPELINE.md` for the Euclid pipeline.

> **This repo holds CODE + DOCS only.** Large data and model weights (`*.h5`, `*.fits`,
> `*.npy`, `*.pt`) are gitignored and live on the compute cluster
> (`~/cosmos_acs/tiles/`, `~/einstein_cnn/`).

## Where to start (docs)

| Doc | What it covers |
|-----|----------------|
| [`docs/PROJECT_OVERVIEW.md`](docs/PROJECT_OVERVIEW.md) | One-page overview of the problem and approach |
| [`docs/GENERATOR_AND_CODEBASE_REFERENCE.md`](docs/GENERATOR_AND_CODEBASE_REFERENCE.md) | **How the training-data generator works** — photometry, units, normalization, file-by-file map, GEN0→GEN5 lineage. Read this first for the code. |
| [`docs/GEN5_PIPELINE.md`](docs/GEN5_PIPELINE.md) | The Euclid ("GEN5") simulation recipe, stage by stage |
| [`docs/CODEBASE_MAP.md`](docs/CODEBASE_MAP.md) | Map of the older Phase-2 (diffusion) tree |
| [`docs/LensFusion_cluster_runbook.md`](docs/LensFusion_cluster_runbook.md) | How to log in and run jobs on the CUHK cluster (SLURM) |

## Repository layout

- `pipeline/` — paltas configs, data generation, realism gates, diagnostics, deflector/
  companion/ePSF builders, and the SLURM `.sbatch` + submit scripts. Runs on the cluster
  under `~/cosmos_acs/tiles/`.
- `training/` — `train_cnn_paltas.py` (ResNet / InceptionNeXt backbones, Gaussian-NLL
  uncertainty head, scale conditioning), `predict_real_lenses_paltas.py`, `metrics_real.py`.
  Runs on the cluster under `~/einstein_cnn/`.
- `analysis/` — local diagnostic/analysis scripts (arc/deflector morphology, PSF, photometry,
  Faber–Jackson calibration).
- `tables/` — small prior/label tables (lens-light priors, benchmark labels, ePSF manifests).
- `results/` — per-lens prediction CSVs from benchmark evaluations.
- `paper_figures/` — figures.

## Dependencies

The pipeline is built on **paltas** (Wagner-Carena et al.). Install paltas and its
dependencies (`lenstronomy`, `astropy`, `galsim`, `numpy`, `scipy`), plus `torch` +
`timm` for training. The configs use a multipole-extended deflector class
(`PEMDShearFourMultipole`); make sure your paltas build provides it (see
`docs/GEN5_PIPELINE.md`).

> ⚠️ **Note for the maintainers:** confirm which paltas build/commit the configs require
> and pin it here before handing the repo to new users, so `import paltas` resolves the
> multipole deflector class.

## Key entry points

- **Generate a dataset:** the `pipeline/*_pilot.sbatch` / `pipeline/generate_*.sbatch`
  jobs (SLURM), driven by a `config_lensfusion_acs*.py` config.
- **Train:** `training/train_cnn_paltas.py --arch {resnet,inceptionnext} --nll`
- **Evaluate on the frozen benchmark:** `training/predict_real_lenses_paltas.py --tta`
  then `training/metrics_real.py`

## Working rules (kept for reproducibility)

- **Never** train or tune on the benchmark files (`real_slacs_images.h5`,
  `real_s4tm_images.h5`). They are for evaluation only.
- Don't run a large generation (> ~200 images) until a small pilot passes the realism
  gates (`gate_stage0.py`, `side_by_side_real_sim.py`) — this catches unrealistic
  ("blobby") arcs early.
