# LensCNN — Changelog (v1 → v2 → v3)

Records exactly what changed at each revision and where each professor comment is
addressed. Comment IDs (C#) match `docs/COMMENTS_TRACKER.md`; reviewer-concern IDs
(R#) and experiment IDs (E#) match `docs/V3_REVIEW_AND_PLAN.md`.

- **v1** = the original "LensCNN" Google Doc as received (with Prof. Chan's comments).
- **v2** = the same Google Doc, edited in place to address the comments.
- **v3** = a from-scratch rewrite: `paper/main.tex` (authoritative LaTeX) + the new
  "LensCNN v3 (Draft)" Google Doc + this changelog.

---

## v1 → v2 (edits in the original Google Doc)

| Section | Change | Comment(s) |
|---|---|---|
| §1.1 | Added a formalism paragraph: lens equation β=θ−α(θ); defines lens light (Sérsic), lens mass (SIS via σ_v), source light; cites Meneghetti (2021), Saha et al. (2024), Treu (2010). | C10, C11 |
| §1.1 | Removed the "Need to cite:" placeholder block; the 3 links resolved to Meneghetti (×2, same textbook) + Saha et al. (2024). | (cleanup) |
| §1.4 | Integrated the "P.S. Gen4/Gen5" note into a clean definition sentence. | (self-note) |
| §2.2 | Cited **Swierc et al. (2024)** (arXiv:2410.16347) for "Domain-Adaptive NPE". | C13 |
| §2.1 | Added justification for why Bolton spectroscopic GT beats a YattaLens pipeline GT. | C15 |
| §2.2 | Confirmed the DA works are labelled "sim→sim". | C14 |
| §3.3 | Renamed "deflector library" → "lens-light library" (4 instances, all tabs). | C19 |
| §3.4 | Added "How the lens mass is constructed" paragraph: mass is a *model* (SIS from σ_v), reliability of σ_v→θ_E (Koopmans 2006; Auger 2010), multipoles as perturbations on an isothermal base. | C19, C18, C9, C7 |
| §4 | Gave "Training and the cost of inference" real content. | C23 |
| §4 | Removed the duplicate "Version without ML words" scaffold (technical text already carries the points). | C24–C29 |

**Left for you in v2 (flagged):** §3.1 "Generator Pipeline" naming; the "LEMON R²=−4 (can we mention this?)" note; C20 library-regeneration note; C17 (Table 1 image needs a UQ row — done in v3); C1/C2/C6/C8/C22/C30 (all done in v3).

---

## v2 → v3 (from-scratch rewrite, `paper/main.tex` + new Google Doc)

### All remaining professor comments closed
| Comment | Where addressed in v3 |
|---|---|
| C1 (abstract deflector wording) | Abstract reworded: "real HST galaxies provide the lens light… mass modelled as SIS via σ_v". |
| C2 (MNRAS abstract) | Single unstructured paragraph, ≤250 words. |
| C6 (Cao not too expensive / CPU / UQ) | §5.5 fair-comparison paragraph; §4 speed caveat; E7 CPU/GPU timing flagged. |
| C8 (our code not solving hard problem) | §6 Discussion: "Hard cases stay hard". |
| C17 (does our method quantify uncertainty?) | Table 1 gains an **Uncertainty (UQ)** row. |
| C22 (which networks more accurate) | §5.6 states the ranking with independent GT, carefully. |
| C30 (how to transfer?) | §5.7 describes the operator-render + retrain procedure. |

### Reviewer concerns pre-empted (see V3 Review & Plan)
| ID | Concern | v3 response |
|---|---|---|
| R1 | SIS labels vs SIE ground truth (label noise) | §3.4 label-noise paragraph; E1 experiment planned. |
| R2 | Train/benchmark leakage via lens-light library | §3.1/§3.3 explicit no-leakage statement; E2 audit (run — see below). |
| R3 | θ_E support / ceiling | §5.2 domain-of-validity. |
| R4 | LEMON numbers not reproducible | §5.6 caveat foregrounded, re-scoring reported separately. |
| R5 | Ablation on v2 recipe not headline | §5.3 ladder clarified; E8 optional re-run. |
| R6 | No confidence intervals | Bootstrap CIs flagged throughout; E3 (run — see below). |
| R7 | Uncertainty calibration, not just correlation | §5.4 recalibration + trade-off curve; E4. |
| R8 | Incomplete results (Euclid Q1 GEN5, DA) | Marked TODO E5/E6 (blockers before submission). |
| R9 | Roman "retrain succeeds" is circular | §5.7 framed as sim→sim, real validation post-launch. |
| R10 | Cao comparison fairness | §5.5 (see C6). |
| R11 | Single-band, θ_E-only scope | §1.3 + §6 scope statements. |
| R12 | Reproducibility | Data Availability + Appendix A. |

### Structural
- New **Discussion (§6)**; real LaTeX tables (caption above); figure with caption; benchmark-properties **Table 2**; consistent notation; BibTeX seeded (all `% VERIFY`).

### Experiments run during the v3 build (real results, in-repo data)
Folded into `paper/main.tex`; full write-up in `docs/V3_REVIEW_AND_PLAN.md` §7.
- **E3 bootstrap CIs** (`analysis/bootstrap_metrics.py`): SLACS R²=0.64 [0.45,0.82], S4TM R²=0.90 [0.86,0.93]; caught the S4TM member-vs-ensemble issue (0.90 is r50\_3; ensemble 0.81). → §5.1 + caption.
- **E2 leakage audit** (`analysis/leakage_audit.py`): 0 library galaxies within 5″ of any benchmark lens (nearest 2798″), 0 name overlap → §3.1 hardened.
- **E4 calibration + gating** (`analysis/calibration_gating.py`): raw σ over-confident (SLACS 1σ-coverage 40%, S4TM 60%; recalibration k≈2.0/1.4); full gating trade-off table → §5.4.
- **New figure** (`analysis/make_gating_figure.py` → `paper/figures/gating_tradeoff.png`): confidence-gating trade-off, added as Fig. in §5.4.
- **E9 Table 2**: θ_E ranges from real GT (SLACS 0.69–1.78; S4TM 0.54–1.62); z_l/z_s from Bolton 2008 / Auger 2009 / Shu 2017 (cited). Deflector-mag still TODO.
- **Number validation:** GEN4 SLACS 0.641, S4TM r50\_3 0.897, m3 S4TM −0.53 (all match); m3 SLACS −1.22 (draft −1.02, reconcile).
- **Still needs external data / heavy runs:** E1 (label noise — needs benchmark σ_v+z_s), E5/E6 (Euclid Q1 GEN5, DA), E7 (Cao CPU timing), E10/R4 (LEMON reproducibility).

### Additional v3 polish (this session)
- **Ablation figure** (`analysis/make_ablation_figure.py` → `paper/figures/ablation.png`): horizontal bar chart of per-ingredient SLACS R² → Fig. in §5.3 (real backdrops removal off-scale at −5.10).
- **Bibliography** (`paper/refs.bib`): replaced guesses with canonical details for the well-established references, and web-verified the key recent ones — **Busillo et al. 2026** (LEMON, A&A, arXiv:2503.15329) and **Cao et al. 2025** (TinyLensGPU, MNRAS 540, 3121, arXiv:2503.08586). `% VERIFY` now remains only on entries I could not confirm (Gawade, Ćiprijanović, Agarwal, Wedig, Shu vol/page, Schuldt vol, Wagner-Carena vol, Newton vol, Mandelbaum, Pawase) — replace those with ADS exports.
- Paper now carries **three figures** (predicted-vs-true, confidence-gating, ablation) and compiles to 6 pp with no undefined citations.

**Note on the Google Doc:** the "LensCNN v3 (Draft)" Google Doc is the readable v3 snapshot; `paper/main.tex` (and the compiled PDF) is authoritative and now slightly ahead (contains the E2/E4 numbers, the gating figure, and the finalised Table 2).
