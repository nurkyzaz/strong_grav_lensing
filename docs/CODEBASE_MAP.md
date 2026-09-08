> **For the θ_E training generator (how it works, photometry/units/normalization,
> by-files map, GEN0→GEN5 lineage) see [GENERATOR_AND_CODEBASE_REFERENCE.md](GENERATOR_AND_CODEBASE_REFERENCE.md).**
> This file covers the older Phase-2 (LensFusion diffusion) tree only.

  bare arc. **No `kappa_interp_mode` kwarg** in this installed version.
- `forward_operator/regularizers.py` — regularizer catalog (Phase 2). `eval.py`,
  `utils/utils.py` — `einstein_radius_hard(kappa_bhw, pixel_scale)` (expects a batch dim, non-diff).
- `sampler.py`, `cores/`, `posterior_sample*.py` — DAPS/PnP-DM sampler (Phase 2).
## `~/lensfusion_data/`
- `kappa_ema_*.pt`, `galaxies_ema_*.pt` **[DATA]** — diffusion checkpoints (κ prior, source prior).
- `kappa_testset.h5`, `test_galaxies.h5` **[DATA]** — held-out κ maps and source galaxies.
Main κ+lens_light training data (not under home): `/home/user/ckwan1/ml_project/
strong_lensing_dataset/kappa_light/train_camera_complete.h5` (keys `kappa`, `lens_light`),
`.../source/galaxies_testset.h5` (key `galaxies`).
 
---
 
## The short version for a new contributor
 
Train with **paltas** (`~/cosmos_acs/tiles/config_lensfusion_acs.py` → `paltas_to_train.py`),
evaluate with **`~/einstein_cnn/metrics_real.py`** on `real_slacs_images.h5` + `real_s4tm_images.h5`.
The baseline is `einstein_cnn_m3.pt`. Everything labeled SUPERSEDED (the bespoke SIMCT composite
generator, HSTempty, harvested ellipticals) is a dead end. The one
open task is `diagnose_paltas_lens_light.py`.