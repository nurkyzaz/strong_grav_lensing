# Strong-lensing θ_E CNN (paltas pipeline)

A CNN that predicts the Einstein radius θ_E from a single HST ACS/WFC F814W lensed image,
trained on physically realistic simulations (paltas + real COSMOS sources + real STScI
focus-diverse ePSFs + real empty-field backdrops + calibrated noise), and validated on a
frozen real-lens benchmark (62 SLACS + 40 S4TM, Bolton 2008 b_SIE ground truth).

**This repo holds CODE + DOCS only.** Large data/models (`*.h5`, `*.fits`, `*.npy`, `*.pt`)
live on the CUHK cluster (`~/cosmos_acs/tiles/`, `~/einstein_cnn/`) and are gitignored.

## Layout

- `docs/` — project memory and plans. **`DECISIONS_LOG.md` is the authoritative record**
  (dated decisions, dead ends, every benchmark evaluation with a running count).
  `CLAUDE.md`, `MASTER_PLAN.md`, `PAPER_PLAN.md`, `PAPER_DRAFT.{md,tex,pdf}`, `LITERATURE.md`.
- `pipeline/` — cluster `~/cosmos_acs/tiles/`: paltas configs, data generation, realism gates,
  diagnostics, deflector/companion/ePSF builders, SLURM `.sbatch` + wave-submit scripts.
- `training/` — cluster `~/einstein_cnn/`: `train_cnn_paltas.py` (ResNet + InceptionNeXt
  backbones, NLL uncertainty head, scale conditioning), prediction, `metrics_real.py`.
- `analysis/` — local diagnostic/analysis scripts (ePSF retrieval, PSF bank, pool/field audits).
- `tables/` — small prior/label tables (lens-light joint prior, benchmark labels, ePSF manifests).
- `results/` — per-lens prediction CSVs from benchmark evaluations.
- `paper_figures/` — figures for the draft.

## Key entry points

- Generate a dataset: `pipeline/generate_*.sbatch` + `pipeline/submit_*.sh` (SLURM waves).
- Train: `training/train_cnn_paltas.py --arch {resnet,inceptionnext} --nll`.
- Evaluate on the frozen benchmark: `training/predict_real_lenses_paltas.py --tta` + `metrics_real.py`.

## Hard rules (see docs/CLAUDE.md)

Never train/tune on `real_slacs_images.h5` / `real_s4tm_images.h5`; every benchmark evaluation
is logged in `DECISIONS_LOG.md` with a running count. Anti-blob discipline: no generation > 200
images until a pilot passes `gate_stage0.py` + `side_by_side_real_sim.py`.
