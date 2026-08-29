# Draft v2 — Comments Tracker

Running status of every comment in the **LensCNN** Google Doc, as we turn draft v2
into the MNRAS submission (`paper/main.tex`).

- **Source doc:** [LensCNN](https://docs.google.com/document/d/18AST2znkXRgzOmFBY0NOpIXNm1L6E6gSs5AHSN64n2s/edit)
- **Pulled:** 2026-08-28 (31 comment threads: 17 from Prof. Chan, 14 self-notes; 30 open, 1 resolved)
- **Author key:** **[Chan]** = Prof. T. K. Chan (feedback to address) · **[self]** = Nurkyz's own working note

**Status legend:** ☐ open · ◐ in progress · ☑ addressed in LaTeX · ✅ resolved in Doc · ⏸ blocked (pending experiment / your decision)

> How to read a row: the *anchor* is the passage the comment sits on; *action* is what we do about it.

### Progress log
- **2026-08-29 — Section 1 (Introduction) — first pass done** (edits made directly in the Google Doc):
  - ☑ C10 + C11 — added a formalism paragraph in §1.1 (lens equation; defines lens light/lens mass/source light; Sérsic light, SIS mass; cites Meneghetti 2021 + Treu 2010).
  - Cleaned the "Need to cite:" placeholder block (removed redundant Meneghetti links now cited in-text).
  - Integrated the "P.S. Gen4/Gen5" note into a clean definition sentence at the end of §1.4.
  - Identified + cited the 3 "fundamental lens literature" links: springer+google = Meneghetti (2021); arxiv 2401.04165 = **Saha et al. (2024)** "Essentials of strong gravitational lensing" — all three now cited in §1.1; removed the floating arxiv link. refs.bib updated (Saha2024, Treu2010).
  - **Still flagged for you:** (1) your note "LEMON R²=-4 when applied to SLACS (can we mention this?)" left in §1.3 — your call. (2) C8/C9 are Discussion/Data items; C7 minor forward-pointer pending. (3) Optionally add fuller formalism (deflection angle, convergence, Fermat potential) if prof wants more than the lens equation.
- **2026-08-29 — Section 2 (Literature Review) — first pass done** (edits in the Google Doc):
  - ☑ C13 — cited **Swierc et al. (2024)** for "Domain-Adaptive NPE"; refs.bib updated.
  - ☑ C15 — added justification for why Bolton b_SIE GT > YattaLens pipeline GT (§2.1 Gawade paragraph).
  - ☑ C14 — confirmed: the DA works are already labelled "sim→sim" / "All three are sim-to-sim" in §2.2 (Chan's "both are simulated images" point is covered).
  - **Flagged for you:** C17 — Table 1 is an image; add an "Uncertainty quantification" row (Ours ✓, Cao ✓, others ✗) when you regenerate it. C12 — research direction, no edit. C22 — verify accuracy ranking during Results §5.
- **2026-08-29 — Section 3 (Data and Simulator) — first pass done** (edits in the Google Doc):
  - ☑ C19 — renamed "deflector library"→"lens-light library" (4 instances) + added "How the lens mass is constructed" paragraph (mass = model, SIS from σv).
  - ☑ C18 — reliability of σv→θ_E addressed (SLACS isothermality, Koopmans 2006 / Auger 2010, scatter as label-noise floor). refs.bib updated.
  - ☑ C9 — GEN5 multipoles framed as perturbations on isothermal base.
  - ☑ C7 — σv→θ_E relation now homed in §3.4.
  - **§3.1 TABLE — BLOCKED on data (needs you):** the placeholder "[Table of sample properties]" needs θ_E, z_l, z_s, deflector-mag for SLACS-62 + S4TM-40. Repo has real **SLACS θ_E** (Bolton b_SIE: 0.69/1.17/1.78) and library z_l/mag, but **no z_s (source redshift) and no S4TM θ_E table**. Won't fabricate — need you to point me to z_s + S4TM values (Bolton 2008 / Shu et al. S4TM) or approve a partial table.
  - **Self-notes flagged:** §3.1 "or maybe call it the Generator Pipeline section?" (naming decision — your call); C20 "may regenerate training set with expanded library" (pending).
- **2026-08-29 — Section 4 (CNN Architecture) — first pass done** (edits in the Google Doc):
  - ☑ C23 — gave the empty "Training and the cost of inference" heading real content.
  - ☑ C24–C29 — the technical §4 text already carries these plain-language points; removed the duplicate "Version without ML words" scaffold block (revert via history if you wanted the plain version kept).
  - **Flagged:** C3 ("I mean ablations") relates to §5.2 — handle in Results.

---

## Section 0 — Title, authors, abstract

| # | Who | Status | Comment | Anchor | Action |
|---|-----|--------|---------|--------|--------|
| C2 | [Chan] | ◐ | "I think we should submit to MNRAS. But basically the format is similar… except the abstract" | Abstract heading (A&A rules) | Use MNRAS single-paragraph abstract, drop A&A Context/Aims/Methods/Results headers. **Done in skeleton** — confirm wording. |
| C1 | [Chan] | ☐ | "Use real HST galaxy as lens light and SIS constrained with velocity dispersion as lens mass" | Abstract methods: "real HST galaxy as lens light … as deflectors" | Reframe deflector wording (light is real, mass is SIS-from-σv). Ties to **C19**. |
| C5 | [self] | ☐ | "I meant that the reasons for the sim-to-real gap are not very well understood" | Abstract: "whose physical origins remain poorly understood" | Keep phrasing; make sure Intro §1.3 backs it up. |

## Section 1 — Introduction

| # | Who | Status | Comment | Anchor | Action |
|---|-----|--------|---------|--------|--------|
| C10 | [Chan] | ☑ | "Every paper starts with this — need at least a short version. Mention the lens equation, define source light, lens mass and lens light. Cite some lensing review/textbook." | §1.1 heading | **DONE** — added formalism paragraph in §1.1: lens equation β=θ−α(θ), defines lens light / lens mass / source light, cites Meneghetti (2021) + Treu (2010). |
| C11 | [Chan] | ☑ | "sersic lens and source light, SIS mass profile" | (definitions) | **DONE** — same paragraph states Sérsic lens & source light, SIS lens mass. |
| C7 | [Chan] | ☐ | "This should be in data section? the Einstein radius and velocity dispersion relation" | §1.1 SIS equation θ_E(σv) | Relation stays in §1.1 as context; full treatment already in §3.4. **TODO (minor):** add a "(see Section 3)" forward-pointer. |
| C14 | [Chan] | ◐ | "from clean data to noisy target … But both are simulated images" | §1.3 sim-to-real gap (a cited DA work) | §1.3/§1.4 text already states the DA works are "sim-to-sim". **Flag:** confirm this fully answers Chan's point (exact anchor not located). |

## Section 2 — Related work / literature review

| # | Who | Status | Comment | Anchor | Action |
|---|-----|--------|---------|--------|--------|
| C13 | [Chan] | ☑ | "which paper is this?" | §2.2 "Domain-Adaptive NPE (2024)" | **DONE** — identified as **Swierc et al. (2024)** (arXiv:2410.16347); citation added in doc + refs.bib. |
| C15 | [Chan] | ☑ | "Gawade is using YATTALENS.. It is not clear why Bolton is better" | §2.1 Gawade et al. | **DONE** — added a sentence explaining YattaLens GT is a model estimate (shared biases → measures consistency, not accuracy), whereas Bolton b_SIE is spectroscopy+imaging independent of any CNN. |
| C16 | [Chan] | ✅ | "I think it is better to just compare with other machine learning papers…" | comparison framing | **Resolved in Doc.** Comparison table (Table 1) is ML-focused. |
| C17 | [Chan] | ⏸ | "The table looks good, but does our method quantify uncertainty?" | §2.3 **Table 1 (image)** | **Needs table regen (yours):** add an "Uncertainty quantification" row — Ours ✓ (NLL head, ρ=0.71), Cao ✓ (per C6), LEMON/Gawade/HOLISMOKES ✗. Text already notes our UQ (§2.3 point 5). Table is an image so I can't edit it. |
| C12 | [Chan] | ⏸ | "it is surprising. we could work on that" | §2.2 "DA does not improve over realism-calibrated simulations" | Chan's reaction, not a text change — a research direction. Flag; no edit. |
| C22 | [Chan] | ☐ | "check which networks are more accurate." | positioning / results comparison | Verify accuracy ranking vs LEMON / Cao / Gawade / HOLISMOKES is stated correctly (do during Results §5). |

## Section 3 — Data and simulator

| # | Who | Status | Comment | Anchor | Action |
|---|-----|--------|---------|--------|--------|
| C19 | [Chan] | ☑ **KEY** | "The lens light can be real, but the underlying mass profiles cannot… no observation." → "better to say **lens light library**" → "add a section on **how the lens mass is constructed**." | §3.3 "Deflector library" | **DONE** — (a) renamed "deflector library"→"lens-light library" (4 instances, all tabs); (b) added "How the lens mass is constructed" paragraph at top of §3.4: mass is a *model* (SIS from σv), not observed. |
| C18 | [Chan] | ☑ | "how reliable is the relation?" | σv → θ_E (SIS) relation | **DONE** — mass paragraph notes SLACS profiles ≈isothermal on average (Koopmans 2006; Auger 2010); galaxy-to-galaxy scatter → label-noise floor. |
| C9 | [Chan] | ☑ | "but still SIS lens mass?" | §3.4 mass shape / GEN5 multipoles | **DONE** — mass paragraph states GEN5 multipoles are perturbations on an isothermal base; "remains fundamentally isothermal." |
| C7 | [Chan] | ☑ | (see §1) σv→θ_E relation belongs in Data | §3.4 | **DONE** — new mass paragraph homes the relation in §3.4, referencing §1.1. |
| C8 | [Chan] | ☐ | "This is a hard problem. It seems our code is not solving this too?" | (find anchor — likely faint-arc / large-θ tail) | Address honestly as a limitation. |
| C20 | [self] | ⏸ | "but I may try to regenerate the training set with expanded library" | §3.3 library size (139 stamps) | Pending: numbers may update if library expands. |
| C21 | [self] | ⏸ | "this might change" | §3.x a specific number | Flag as provisional. |

## Section 4 — CNN architecture and training

| # | Who | Status | Comment | Anchor | Action |
|---|-----|--------|---------|--------|--------|
| C23 | [Chan] | ☑ | "new sections" | §4 "Training and the cost of inference" (empty heading) | **DONE** — gave the heading real content: a training/inference-cost paragraph (40 epochs, ms/lens inference, amortised speed vs Cao). |
| C29 | [self] | ☑ | "A standard ResNet told the pixel scale (0.05″/px)…" | §4 architecture | **Covered** — technical §4 text already describes the scale-conditioned CNN. Removed the duplicate "Version without ML words" plain-English scaffold block. |
| C28 | [self] | ☑ | "or four layers" | §4 architecture detail | **Covered** — text says "four residual stages". |
| C27 | [self] | ☑ | "Network outputs (1) predicted θ_E and (2) uncertainty." | §4 output head | **Covered** — text describes the (μ, log σ²) NLL head. |
| C26 | [self] | ☑ | "The uncertainty due to noise in the image itself" | §4 aleatoric uncertainty | **Covered** — text describes per-image aleatoric uncertainty. |
| C25 | [self] | ☑ | "At evaluation, flip/rotate each real image 8× (TTA)…" | §4 evaluation | **Covered** — text describes 8× dihedral TTA. |
| C24 | [self] | ☑ | "Total uncertainty = mean per-view uncertainty + spread across 8 views." | §4 uncertainty | **Covered** — text describes total variance = mean aleatoric + epistemic (view spread). |
| C3 | [self] | ☐ | "I mean ablations" | (self-clarification) | Minor — relates to §5.2 ablations; ensure labelled clearly when we do Results. |

## Section 5 — Results

| # | Who | Status | Comment | Anchor | Action |
|---|-----|--------|---------|--------|--------|
| C6 | [Chan] | ☐ | "Cao is not too expensive, especially they give uncertainty quantification. Maybe some CPU codes?" | §5.4 Cao comparison / speed claim | Soften the "10⁶× speed" framing; acknowledge Cao provides UQ; consider a CPU-timing comparison. |
| C30 | [Chan] | ☐ | "How to transfer?" | §5.6 transfer to Euclid/Roman | Describe the transfer/retraining procedure explicitly. |
| C4 | [self] | ⏸ | "to be added … result from our second model trained for euclid/roman high-z" | Abstract/§5 Euclid Q1 result | Pending experiment (Euclid Q1, N=322). |
| C12 | [Chan] | ☐ | "it is surprising. we could work on that" | (a surprising result) | Low action — note for discussion. |

## Cross-cutting / structural

| # | Who | Status | Comment | Anchor | Action |
|---|-----|--------|---------|--------|--------|
| C23 | [Chan] | ☐ | "new sections" | ~§5.6 / end | Add Discussion + any new sections Chan flags. |
| C31 | [self] | ✅ | "Do we have to mention we participate in the Roman challenge?" → Chan: "Not necessarily" | §2.4 / §5.6 Roman | **Decided:** optional — likely omit the challenge mention. |

---

### Open questions to raise with Prof. Chan
- Co-authors: confirm "Brian? Sam? Prof. Otto?" for the author list.
- C7: is the σv→θ_E relation's primary home Intro or Data (or both, short+full)?
- C8/C12: which specific results does he mean — needs anchor confirmation from the Doc.
