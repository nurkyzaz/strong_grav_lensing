# Referee-response template — LensCNN (MNRAS)

Pre-drafted responses to the concerns a referee is most likely to raise, keyed to
`docs/V3_REVIEW_AND_PLAN.md` (R#) and the current `paper/main.tex`. When the
report arrives, paste the referee's points, match them to these, and fill the
`>>` action lines. "Addressed in" gives the section/figure to point the referee to.

> Standard opening: *"We thank the referee for a careful and constructive report.
> We have revised the manuscript to address each point; changes are marked in
> boldface in the resubmission. Below we respond point by point."*

---

### R1 — SIS(σ_v) training labels vs SIE (b_SIE) ground truth (label noise)
**Likely question:** How much of your residual is self-inflicted label noise from
the σ_v→θ_E model rather than network error?
**Response:** We agree this is fundamental and now state it explicitly (§3.4,
"Reliability of the σ_v→θ_E label", and §6). The SIS mapping is justified by the
near-isothermal average profile of SLACS early-types (Koopmans et al. 2006; Auger
et al. 2010), but carries intrinsic scatter that sets a floor on the attainable
R². **Addressed in:** §3.4, §6.
`>> ACTION (E1): run analysis to quote the SIS(σ_v)-vs-b_SIE bias/scatter on the`
`   benchmark once SDSS σ_v + source redshifts are joined to the 62 J-names;`
`   add one line + optionally a panel. This directly bounds R² and turns the`
`   weakness into a rigor point.`

### R2 — Train/benchmark leakage via the lens-light library
**Likely question:** Do any benchmark galaxies' light stamps appear in training?
**Response:** No. The library is drawn from non-lens parents, and a sky-position
cross-match finds zero library galaxies within 5″ of any benchmark lens (nearest
2798″) with no name overlap. **Addressed in:** §3.1; `analysis/leakage_audit.py`.
`>> ACTION: add coordinates to g1b_kinematics_v1.csv so the audit covers all 488`
`   stamps (currently 109 with coords); expected to stay clean.`

### R3 — θ_E support / out-of-support lenses
**Response:** The training support is [0.45, 2.30]″; we report a domain-of-validity
(§5.2) and disclose under-prediction of above-ceiling lenses (e.g. 2/5 COSMOS,
§5.6). **Addressed in:** §5.2, §5.6.
`>> ACTION: quote the out-of-support fraction for SLACS-62/S4TM-40/Euclid Q1.`

### R4 — LEMON comparison not reproducible
**Likely question:** Your headline comparison rests on numbers you cannot
reconcile with LEMON's published values.
**Response:** We report our transparent re-scoring of LEMON's public predictions
against the independent literature θ_E separately from LEMON's own reported
aggregate, and flag the discrepancy openly (§5.6). **Addressed in:** §5.6.
`>> ACTION (R4/E10): resolve with the LEMON authors before resubmission; state`
`   the resolution. This is the highest-risk external item.`

### R5 — Ablations on the pre-self-consistency recipe
**Response:** The ablations isolate single ingredients on the real-unit hybrid
recipe (R²=+0.27); physical self-consistency is a separate, larger step
(+0.27→+0.64), presented as a coherent ladder (§5.3, §5.5).
**Addressed in:** §5.3 (Table 4, Fig.), §5.5.
`>> ACTION (E8, optional): re-run the two dominant ablations on the GEN4 recipe`
`   to show the ladder is monotonic on the final model.`

### R6 — No confidence intervals on small samples
**Response:** Every headline metric now carries 68% bootstrap CIs (10⁴ resamples;
§5.1, Appendix A). We report these rather than point estimates alone.
**Addressed in:** §5.1; `analysis/bootstrap_metrics.py`. DONE.

### R7 — Uncertainty calibration, not just correlation
**Response:** We show the raw σ is over-confident (reliability diagram, Fig.
`fig:calib`; 1σ coverage 40%/60% vs 68%) and apply a global recalibration
(×2.0/×1.4); we present the full confidence-gating trade-off (Fig. `fig:gating`,
Table 5) rather than a single operating point. **Addressed in:** §5.4. DONE.

### R8 — Incomplete results (Euclid Q1 GEN5, post-DA)
**Response:** [To complete before submission.]
`>> ACTION (E5, E6): run the Euclid Q1 GEN5 evaluation (N=322) and the DA`
`   experiment; fill Table/§5.1, §5.5, §5.7. BLOCKER.`

### R9 — Roman "retrain succeeds" is circular
**Response:** We frame Roman explicitly as a simulation-to-simulation demonstration
of instrument-agnostic retraining (no real Roman lenses exist pre-launch), with
real validation deferred to post-launch. **Addressed in:** §5.7, §6.

### R10 — Cao comparison fairness (also Prof. Chan C6)
**Response:** We now note conventional modelling (TinyLensGPU) also returns
per-lens uncertainties and full posteriors and is not prohibitively expensive;
our advantage is amortized inference throughput, not a categorical capability gap.
**Addressed in:** §5.5, §4.
`>> ACTION (E7, optional): add a CPU/GPU wall-clock comparison.`

### R11 — Single-band, θ_E-only scope
**Response:** We state the scope explicitly and argue θ_E is the right first,
most-robust target; ellipticity/shear/source and multi-band inputs are natural
extensions. **Addressed in:** §1.3, §6.

### R12 — Reproducibility
**Response:** Code, configs, the kinematic library, and per-lens predictions are
available (Data Availability; Appendix A). **Addressed in:** Data Availability.
`>> ACTION: finalise the repository/DOI and seed/config list.`

---

## Pre-submission blockers (do these first)
1. **E5/E6** — Euclid Q1 GEN5 + post-DA results (R8).
2. **R4/E10** — LEMON reproducibility resolution.
3. **E1** — SIS-vs-SIE label-noise number (R1).
4. Replace remaining `% VERIFY` BibTeX entries with ADS exports.
5. Fill the `\todo{}` items in `paper/main.tex` (deflector mags, Cao table, email, funding, DOI).
