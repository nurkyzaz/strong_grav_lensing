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
| [`docs/HOW_IT_WORKS.md`](docs/HOW_IT_WORKS.md) | **Start here.** What GEN4/GEN5 are and how they work, the CNN, uncertainty, and exactly how to run generation/training/eval. |
| [`docs/GENERATOR_AND_CODEBASE_REFERENCE.md`](docs/GENERATOR_AND_CODEBASE_REFERENCE.md) | Generator internals — photometry, units, normalization, file-by-file map, GEN lineage. |
| [`docs/GEN5_PIPELINE.md`](docs/GEN5_PIPELINE.md) | The Euclid ("GEN5") simulation recipe, stage by stage. |
| [`docs/PROJECT_OVERVIEW.md`](docs/PROJECT_OVERVIEW.md) | Background/motivation (some legacy framing; see HOW_IT_WORKS for the current pipeline). |
| [`docs/CODEBASE_MAP.md`](docs/CODEBASE_MAP.md) | Map of the older Phase-2 (diffusion) tree. |
| [`docs/LensFusion_cluster_runbook.md`](docs/LensFusion_cluster_runbook.md) | How to log in and run jobs on the CUHK cluster (SLURM). |

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

## Setup

```
conda create -n lensfusion python=3.8 && conda activate lensfusion
pip install -r requirements.txt
```

The pipeline is built on **[paltas](https://github.com/swagnercarena/paltas)**
(Wagner-Carena et al.), pinned to **0.2.0** in `requirements.txt`. paltas is used
**unmodified** — the multipole deflector class `PEMDShearFourMultipole` that the GEN5
configs use is part of stock paltas 0.2.0. Our contribution is the per-galaxy,
isophote-anchored multipole *priors* passed to it in `pipeline/config_lensfusion_acs*.py`
(see `docs/GEN5_PIPELINE.md`), not a fork of paltas.

`galsim` is the one dependency that can be awkward to pip-install (it needs FFTW/Eigen);
if it fails, `conda install -c conda-forge galsim=2.5.3`. For GPU training, install the
`torch` build matching your CUDA (the cluster used cu121).

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
