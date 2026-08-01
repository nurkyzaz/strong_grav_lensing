# CLAUDE.md — Strong-lensing θ_E CNN (paltas pipeline; operated over SSH)

You (Claude Code) run LOCALLY on Nurkyz's Mac. Code, data, and compute live on a
remote cluster reachable via `ssh nurkyz@gpus`. Read this file fully before acting.
It is project memory. **`DECISIONS_LOG.md` in this folder is the single most
authoritative file — if anything here conflicts with it, DECISIONS_LOG.md wins,
and say so out loud rather than silently picking one.**

## CONTINUATION PROMPT (state as of 2026-08-02; delete this block when superseded)

REPO LOCATION: this repo now lives at **~/code/LensFusion** — MOVED off the
iCloud-synced ~/Desktop on 2026-08-01 because iCloud was corrupting .git
(duplicated `refs/heads/main` → `main 2`, broke the repo). Never put it back
under ~/Desktop or ~/Documents (both iCloud-synced). Big dirs `_local/` (archive),
`epsf_library/`, `roman_dc/`, `.venv_epsf/`, `data_local/` were NOT copied
(iCloud / regenerable / on cluster) — recreate `.venv_epsf` for local Python.
NOTE (2026-08-02): the LEMON line and the GEN5/Phase-0 line were developed on
separate branches and MERGED back to main on 2026-08-02 — main is now the single
source of truth again.

Read the top DECISIONS_LOG.md entries (2026-08-02 first), then COMMITMENTS.md
(reconcile every OPEN row at every ⛔), then MODELS_AND_RESULTS.md (eval count 25),
and docs/GENERATOR_AND_CODEBASE_REFERENCE.md (generator internals). Two galleries
live on the Mac (open in a browser): `g5_c21_pilot_review/` (GEN5 renders, 3-domain
× 3-stretch) and `q1_real_review/` (the 322 real Q1 eval lenses + official RGB +
Phase-0 metrics).

NAMING RULING (Nurkyz 2026-07-22): **GEN4 = the low-z native generation
(SLACS/S4TM); GEN5 = the high-z build (Euclid-Q1 + Roman) via z-migration.**
Chain files renamed g4b_* → g5_* (g5_make_manifest.py, config_lensfusion_acs_g5.py,
g5_c21_*.sbatch; pilot dir ~/paltas_g5_c21_pilot).

WHERE WE ARE (eval count 25): the GEN4 low-z self-consistent population is the
paper's CORE, MEASURED result (62 SLACS + 40 S4TM, Bolton b_SIE): native SLACS
R² +0.64 / 15%, S4TM r50 R² +0.90 / 8%, Euclid-domain R² +0.71 / RMSE 0.137″ —
matches/beats Cao 2025, leads LEMON on real-θ_E lenses.
- **LEMON head-to-head, domain A** (Euclidised HST, their EXACT lenses vs lit GT):
  WE LEAD SLACS (29, R²+0.57 vs −4.26) and EEL (12) decisively; COSMOS (5) small-N
  wash (we under-predict θ_E>2.3″ out-of-support); ACS (13) has NO θ_E GT — arc
  radius only. **NEW 2026-08-01: we scored OURSELVES on ACS-vs-Pawase-arc-radius
  for the first time** — our scatter is tighter than LEMON (NMAD 0.31 vs 0.36) but
  we carry the expected θ_E<arc-radius negative bias; ACS is reported SEPARATELY,
  kept OUT of the θ_E aggregate (unlike LEMON's Table 3). Package
  `lemon_comparison_package/`; `analysis/lemon_acs_arcradius.py`. Email REWRITTEN
  (EMAIL_DRAFTS_20260710.md: 2 asks — ACS GT + SLACS same-lens permission — not
  "we can't reproduce"). PAPER_DRAFT §4.6 has the same-lens paragraph.
- **ACTIVE workstream = GEN5** (C21 z-migration + AR3 isophote-anchored m=3,4
  multipoles on the 514-prune / 488-measured / 394-AR3-clean G1b library, 488
  STANDALONE). GEN5 v4 pilot passes every STAT gate (peak/sky 141∈[103,727],
  sky-RMS 0.955, FJ −0.48, AR0 4/4, Roman 1.03/1.02/1.05) BUT Nurkyz's eye-check +
  Phase 0 (DONE) found real visual gaps vs the 322 real Q1: **companions ~4× too
  many (FIRM fix); "arcs not visible" = dynamic-range/clutter, not faint arcs (GEN5
  arcs measure brighter than real); "too-elliptical arcs" UNCONFIRMED by the
  coverage metric — needs a smoothness metric.** FULL GENERATION IS HELD until
  Phase 1 + the blockers below close.
- evals #24/#25 (native REAL Euclid Q1, N=322, vs PyAutoLens GT): best in-support
  R²+0.61 / fail 32% / bias −8% — BELOW LEMON's own 0.71; OPEN frontier (= the
  domain-B / C34 target). ROMAN Data Challenge Rung-0 SUBMITTED (6-net G5a ens);
  2nd independent submission not yet done.

GEN5 FROZEN v4 RECIPE (for full gen WHEN AUTHORIZED): g5_make_manifest --evo_q 1.2
[PENDING NURKYZ/BRIAN CONFIRM] → config_lensfusion_acs_g5 (Gen5HighZSource
banner-gated) → hybrid_combine (migration + companion dim) → euclidise
LF_EUC_SKY_SCALE=2.2 + arc_visibility_select 0.8/150 → romanise LF_ROM_FLUX=0.11.
BLOCKING full gen: C30 Phase-1 visual fixes (companion cut + deflector-dominance +
smoothness metric); C31 evo_q confirm; C2 q_mass–q_light fit (Zenodo 6104823, still
ad-hoc); Nurkyz >1k-scale ruling.

PENDING DECISIONS / TO-DOs (Nurkyz):
1. **GEN5 Phase 1** (companion cut + deflector-dominance check + smoothness metric
   + re-pilot + re-show) — the immediate GEN5 next step, pending go.
2. **Real-eval-set audit** (C32): auto-flagger RULED unreliable; Nurkyz adjudicates
   the 322 via the upgraded q1_real_review gallery (only 2 tiny-θ failed-PyAutoLens
   models, incl #161, are defensible auto-flags). Decide flag-only vs cleaned subset.
3. **Paper-1 scope**: freeze at two-domain HST + Euclidised-HST + LEMON head-to-head
   + ablations + uncertainty + DA-negative; defer GEN5 / Roman / multipoles /
   native-Q1 to Paper 2. Then WRITE (PAPER_DRAFT.md still a skeleton).
4. Send the LEMON email (draft ready; set the provenance line).
5. Roman 2nd submission (GEN5-Roman-trained), the independent-methodology entry (C34).
6. Brian/advisor on authorship + scope; recreate .venv_epsf; confirmation-set eval.

STANDING OPERATIONAL PATTERN: cluster compute via `ssh nurkyz@gpus` (csh login →
wrap in `bash -lc`); chain stages with sbatch --wait driver scripts (≤8 jobs,
gate-check between hops, bank results before deletion, jobs survive Nurkyz's
logout); benchmark evals counted + reported immediately; one config change → one
pilot → gates; push to git at every milestone. After any autonomous cluster
campaign, RECONCILE the cluster work back to the Mac + git (a 3-week desync
happened once — evals #22–#25 + GEN5 + Roman ran unlogged; consolidated 2026-08-01).

## Superseded document warning

A document titled "Project Instructions for Claude" describing CNN training data
generated via LensFusion's own `forward_operator` + IllustrisTNG κ maps (κ̄=1 labels,
Gaussian PSF/noise) may exist in this folder or be pasted again later. **Its
data-generation approach is SUPERSEDED** (see DECISIONS_LOG.md, 2026-07-02 pivot and
2026-07-05 ruling) — the actual project uses **paltas**, real ACS PSF, HST-calibrated
noise, and **SIE θ_E labels** (not κ̄=1). That document's terminology section (source
vs. lens vs. lens light vs. convergence) and its Phase-2 non-differentiability
caution are still valid background. If you see it, treat data-generation claims in
it as historical, not current.

## Code repository

GitHub (private): **https://github.com/nurkyzaz/strong_grav_lensing** — this Mac folder is
the working tree (`main`). Layout convention (set by the initial curation, keep it):
the FLAT root files are the live working copies and stay UNTRACKED; the repo tracks
curated mirrors — `docs/` (the .md/.tex docs), `pipeline/` (~/cosmos_acs/tiles scripts),
`training/` (~/einstein_cnn scripts), `analysis/` (Mac-side scripts), `results/`
(per-lens prediction CSVs + forensics), `tables/`, `paper_figures/`. To publish: copy
root docs into `docs/`, pull current cluster scripts into `pipeline/`+`training/`,
add new eval CSVs to `results/`, commit, push. **Push policy (Nurkyz ruling
2026-07-10): push whenever meaningful changes accumulate** — a logged eval, a new
plan/stage, a new script generation, or a DECISIONS_LOG milestone; don't wait to be
asked, and don't push mid-experiment noise. Data/binaries never enter git
(*.h5, *.pt, *.npy, PDFs, epsf_library/ — cluster or Zenodo).

## Cluster operational facts (validated by a prior orientation pass — do not re-derive)

- Login shell is **csh**. Every remote command needs `bash -lc '...'` wrapping:
  `ssh nurkyz@gpus "bash -lc 'cd ~/cosmos_acs/tiles && python foo.py 2>&1'"`
  Bare `cmd 2>&1` over plain ssh fails with "Ambiguous output redirect".
- **No tmux/screen on the login node.** It's a SLURM head node (`sbatch`/`squeue`
  present; `nvidia-smi` fails on the head node itself — GPUs are on compute nodes,
  presumably a1–a6). Long jobs (pilot generation past a few minutes, training, full
  dataset generation) go through **SLURM batch scripts**, not tmux. Write an
  `.sbatch` file, `sbatch` it, poll with `squeue -u nurkyz`, read logs from the
  SLURM output file — do not block a foreground ssh session on a long job.
- **Quota 104/150 GB, limit 160** (raised 2026-07-13; as of last check — re-verify with `quota -s` or the cluster's
  equivalent before any large generation run). A ~3 GB pilot fits; delete superseded
  datasets/checkpoints before generating a new full (50–100k image) set.
- conda env `Stronglensing`, Python 3.8 → no backslashes inside f-strings.
- Working dirs: `~/einstein_cnn/` (models, benchmark, metrics, diagnostics),
  `~/cosmos_acs/tiles/` (paltas config, PSF file, generation/fix toolchain).
- **Monitors report, the session submits** (rule adopted after the 2026-07-10 merge
  collision): completion-monitors and watcher loops must never carry submission
  side-effects that can race a manual action. Only an explicit submit script (the
  `sbatch --wait` wave pattern, e.g. `submit_pathb.sh`/`submit_l1.sh`) or the live
  session may submit jobs.
- ssh prints a quota banner on STDOUT — never pipe binary data (tar) through a plain
  ssh channel; write to a cluster file and `scp` it instead.

## Environment pins (violating these breaks things — see DECISIONS_LOG.md for why)

- paltas **0.2.0**, installed with `--no-deps` (its numpy pin must never be
  resolved). Do **not** downgrade to 0.1.1 (calls `ProfileListBase._import_class`,
  removed from our lenstronomy → crash). Do **not** upgrade lenstronomy past the
  current ~1.12–1.13 band (≥1.14 renames `DataAPI` numpix→num_pix and breaks paltas
  0.2.0; ≤1.11 breaks on modern numba).
- Config `config_lensfusion_acs.py` defines an `ApparentSersic` subclass for lens
  light (paltas 0.2.0 treats `magnitude` as absolute; this restores the apparent
  convention) and `mag_cut` (anti-blob gate). Do not remove either.

## Established diagnoses — paid for, do not re-litigate without new evidence

1. **Prior-pull**: `einstein_cnn_m3.pt` fails on real lenses because its training
   θ_E prior was narrow/skewed → predictions collapse to ~0.95–1.0″. Fix = paltas's
   flat θ_E prior. Failure was distributional, not architectural — keep the m3
   architecture unless a gate proves otherwise.
2. **paltas 0.2.0 magnitude convention**: `SingleSersicSource.magnitude` is
   ABSOLUTE. `ApparentSersic` fixes lens light. If a Sersic SOURCE is ever added,
   its convention must be decided explicitly (COSMOSCatalog, the current source,
   is unaffected — it uses its own photometry).
3. **Central square artifact = truncated PSF kernel support, CONFIRMED** (27×27 px
   kernel → 26 px square; discontinuity ratio 107.6; absent under Gaussian PSF).
   The COSMOS-stamp-footprint hypothesis was tested and RETRACTED (stamp noise
   subdominant, ratio 0.38) — don't re-propose it.
4. **The PSF kernel itself is a known weak link**: edge_median/peak = 0 with
   edge_max/peak = 1.6e-2 → empirical stamp, noise floor ~0.5% of peak, negatives
   clipped to zero. `fix_psf_kernel.py`'s wing-extension has hardening for exactly
   this (adaptive r0, alpha cap, >10% flux abort guard) — always run
   `inspect_psf_kernel.py` first and choose `--r0`/`--alpha` from its output, don't
   trust naive extension on a noise-dominated stamp. Standing parallel ask: request
   a larger/cleaner ACS PSF from Sam (TinyTim or star stack, ≥51 px).
5. **mag_cut = 3.0** rejects unlensed-blob geometries on purpose. Log acceptance
   rate every run; exactly 1.0 with no mag_cut = bug.
6. **κ̄=1 vs SIE offset**: paltas SIE labels match the SLACS b_SIE benchmark
   directly — no conversion needed for evaluation. (Only matters again if Phase 2
   ever compares against a sampler-side κ̄=1 θ_E — flag, don't solve, until then.)
7. **The original empirical `acs_psf.npy` is RETIRED** (2026-07-05): only ~15% of
   its flux was in the core, ~70% in a noise plateau — it, not just its truncation,
   was why old previews looked strange. Real STScI focus-diverse ePSFs replaced it.
8. **Independent-marginal priors are an anti-pattern for lens light**: data-driven
   mag and Re priors sampled independently produced faint+huge deflectors nature
   doesn't make (peak/sky collapsed). Sample JOINT empirical (mag, Re) pairs.
9. **Aperture vs total magnitude**: paltas `magnitude` is the Sérsic TOTAL; an
   r=2″ aperture on an Re≈2″ n=4 galaxy holds only ~50% of the light. Any
   photometric prior derived from cutouts needs the incomplete-gamma
   aperture-to-total correction (`build_lens_light_prior.py` does this).
10. **Docs may promise scripts that don't exist** (`inspect_psf_kernel.py` and the
    hardened `fix_psf_kernel.py` flags were specified but never shipped). Verify a
    tool exists and read its actual `--help` before building a plan around it.
11. **Every SLURM partition here (normal/a/b/c) requires `--gres=gpu:N`**, even for
    pure-CPU jobs (paltas generation uses no GPU) — omit it and `sbatch` rejects
    the job outright. Request the minimum (`gpu:1`).
12. **QOS "normal" caps `MaxJobs`/`MaxSubmit` at 8.** Any array/job set bigger than
    8 must be split into sequential waves (`sbatch --wait` per wave), not submitted
    at once — `--array=0-21` or even three concurrent 8-task arrays both fail.

## Hard rules

- **FROZEN BENCHMARK, disclosed integrity gap**: `real_slacs_images.h5` (62) and
  `real_s4tm_images.h5` (40) are test data. DECISIONS_LOG.md 2026-07-05 records that
  they were already evaluated an unrecorded number of times in prior sessions
  (pre-dating logging discipline) — that's done and can't be undone, but from now
  on: never train or tune on them, evaluate only at explicit human checkpoints, and
  log every single evaluation here with a running count. Model selection uses ONLY
  a held-out simulation validation split.
- **Anti-blob discipline**: never generate more than 200 images until the previous
  pilot passes `gate_stage0.py`; never launch the full dataset until a 200-image
  pilot passes every gate. Every preview uses `preview_three_stretch.py` (linear /
  percentile / asinh) — a "blob" under one stretch is often a lens under another.
- **Diagnose before fixing**: reproduce/measure an artifact before changing config
  or code (pattern: `diagnose_components.py`, `diagnose_psf_square.py`,
  `inspect_psf_kernel.py`). One change at a time; re-smoke-test after each.
- **Log like a scientist**: dated entries in `DECISIONS_LOG.md` for every decision,
  fix, retraction, and benchmark evaluation. RETRACTED, not silently edited, when a
  hypothesis is disproven.
- **Commitments ledger (`COMMITMENTS.md`)**: any decision that defers work ("later",
  "at stage X", "flagged for verification") gets a ledger row AT DECISION TIME.
  Before any full generation and at every ⛔: reconcile every OPEN row — implement,
  re-defer with a reason, or retire with a reason. (Adopted 2026-07-12 after the
  G0-anchored ΔPA↔γ_ext coupling was found unimplemented at eval #19.)
- Evolve `config_lensfusion_acs.py` with backups (the `.bak`/`.bak2` pattern already
  in use), don't rewrite it from scratch. Don't touch anything under `~/einstein_cnn/`
  starting with `real_`.

## Toolchain already present in ~/cosmos_acs/tiles/ (use, don't reinvent)

`run_paltas_pilot.py`, `preview_three_stretch.py`, `paltas_npy_to_train.py`,
`gate_stage0.py`, `diagnose_components.py`, `diagnose_psf_square.py`,
`inspect_psf_kernel.py`, `fix_psf_kernel.py`, `patch_config_apparent_sersic.py`,
`patch_config_clean_cosmos.py`, `measure_real_deflector_mags.py`,
`hybrid_combine.py` (the default image assembler), `side_by_side_real_sim.py`
(real-vs-sim gallery, run on every dataset version),
`config_lensfusion_acs_nonoise.py` (no_noise wrapper for hybrid generation),
`lens_light_empirical.csv` (joint mag–Re prior table). Read each script's own
docstring/`--help` before use; confirm it exists before planning around it.

On the Mac (this folder): `epsf_retrieve.py` + `.venv_epsf/` retrieve STScI
focus-diverse ePSFs into `epsf_library/{benchmark,broad}/` (169 + 52 cubes
retrieved 2026-07-05, manifests alongside).

## The plan

**docs/MASTER_PLAN.md is the SINGLE live plan** (consolidated 2026-07-13: the
priority ladder, the Q program vs LEMON, the AR ladder, and every open item
inherited from the archived plans). Superseded plan documents live in
`docs/archive/` with banners — read them only for history. Deferred-work rows
live in COMMITMENTS.md (reconcile at every ⛔). If MASTER_PLAN conflicts with a
newer DECISIONS_LOG entry, the log wins; update the plan when that happens.

## Benchmark / literature context

Primary comparison: **Cao et al. 2025** (arXiv:2503.08586) — automated conventional
modeling pipeline (not a CNN), same 63 grade-A SLACS, same b_SIE ground truth, ≲5%
deviation / ~10% failure. Bar: match or beat on the same lenses. Secondary
CNN-to-CNN reference: **Gawade et al. 2025** (arXiv:2404.18897, ground-based HSC,
~10–20% error) and **Hezaveh et al. 2017** (Nature, foundational SIE-CNN). See
`LITERATURE.md` for what's confirmed vs. unverified from each.

## Style

Exact copy-paste commands in reports; plain-language explanation next to technical
results; flag uncertain physics explicitly ("confirm with Brian") rather than
asserting; before/after comparisons for every change. Ask before: any generation run
>1k images, any training run >30 min, any SLURM job you haven't shown the script
for first, deleting/rewriting (rather than patching) existing scripts/configs,
installing/upgrading packages, and any use of the real-lens files.
