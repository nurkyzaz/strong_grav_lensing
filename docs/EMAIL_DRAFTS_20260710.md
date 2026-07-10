# Email drafts — 2026-07-10 (L0 item 4; Nurkyz to review, personalize, and send)

All three are the long-lead-time items that block the exact head-to-head comparisons.
Send order: LEMON first (blocks the shared-29 table), Cao second, Brian whenever.

---

## 1. To the LEMON team (Euclid Collaboration: Busillo et al. 2026, A&A — corresponding author per the paper)

Subject: Shared SLACS sample and per-lens predictions — LEMON (Q1) comparison from an HST-trained θ_E CNN

Dear Dr. Busillo and the LEMON team,

I am a researcher working on CNN-based Einstein-radius estimation for real
galaxy-galaxy lenses, trained on simulations with HST-native realism (real COSMOS
sources, empirical focus-diverse ACS ePSFs, real empty-sky backdrops) and evaluated
against the uniform spectroscopic-survey b_SIE values of Bolton et al. (2008) for
62 SLACS and 40 S4TM lenses.

Your Q1 LEMON paper is the closest published work to ours, and we would like to
compare against it as carefully and fairly as possible — in your conventions and in
your evaluation domain. We have reimplemented the HST2EUCLID-style degradation from
the published description and evaluate in a LEMON-convention table (bias, RMSE,
NMAD, R²), but three things would make the comparison exact rather than
distribution-level, and we would of course make clear in the paper that they came
from you:

1. The list of the 29 SLACS systems in your 60-lens Euclidised HST validation set,
   so we can report a same-lens head-to-head table.
2. If possible, your per-lens θ_E predictions (and σ) for the 60 Euclidised HST
   lenses — aggregate metrics hide sample-composition effects, and a per-lens
   scatter plot of the two methods would be far more informative for both papers.
3. A pointer to the HST2EUCLID code (Bergamini et al. 2025), if it is available to
   collaborators — we want to replace our disclosed reimplementation with the
   original operator.

We would be happy to share our per-lens predictions on the same systems in return.
Our current results are competitive with yours on typical-lens accuracy, and we
believe a careful cross-validation between an HST-native and a Euclid-native
pipeline would strengthen confidence in both ahead of DR1.

Thank you for the impressive work — the Q1 modeling papers are a real service to
the community.

Best regards,
Nurkyz Ydyrysova
[affiliation]

---

## 2. To Xiaoyue Cao (Cao et al. 2025, MNRAS, TinyLensGpu on 63 SLACS)

Subject: Per-lens θ_E results for the 63 SLACS lenses — comparison with an amortized CNN

Dear Dr. Cao,

I am working on a CNN-based Einstein-radius estimator trained on physically
calibrated simulations and evaluated on the SLACS sample against the Bolton et al.
(2008) b_SIE values — the same lenses and ground truth as your TinyLensGpu paper,
which we use as our primary conventional-modeling comparison (and whose suggestion
that failures "can be mitigated by incorporating prior knowledge from machine
learning techniques" is a direct motivation for our work).

Would you be willing to share your per-lens θ_E results (point estimates and
uncertainties) for the 63 SLACS systems? The repository contains the code but not
the per-lens outputs, as far as we could find. A per-lens comparison would let us
report where the two method classes agree and disagree on identical data — much
more informative than comparing summary statistics. We are particularly interested
in the systems where both approaches struggle (e.g. SDSSJ0841+3824 appears
problematic for both pipelines), since those are informative about the lenses
rather than the methods.

We would gladly share our per-lens predictions in return, and will of course cite
the data as a private communication or as you prefer.

Best regards,
Nurkyz Ydyrysova
[affiliation]

---

## 3. To Brian (authorship + status; personalize freely — this is just a skeleton)

Subject: θ_E CNN paper — status and authorship

Hi Brian,

Quick status on the Einstein-radius CNN work: the realism program paid off. On the
frozen real-lens benchmark (62 SLACS + 40 S4TM, Bolton b_SIE) the current models
reach positive full-sample R² with no filtering, and in the Euclidised domain we
now beat the LEMON Q1 paper (Euclid Collaboration, A&A 2026) on typical-lens
accuracy (NMAD 0.084″ vs their 0.11″), with the remaining gap isolated to a
catastrophic tail we know how to attack (it is a small-θ_E training-distribution
effect, not an arc-visibility one — we have the forensics). The causal ablations
(which simulation-realism ingredient matters) are the novelty spine; nobody in the
literature isolates them.

Two things I'd like to settle with you:
1. Authorship and manuscript placement for this paper — we had flagged early on
   that this should be discussed before results exist; they now do.
2. I'm emailing Cao (TinyLensGpu) for their per-lens SLACS results — if you know
   the group, an introduction would help.

Happy to walk you through the result tables whenever suits.

Nurkyz

---

Notes for Nurkyz before sending:
- LEMON: check the corresponding-author email on the A&A page (Busillo et al. 2026,
  aa54538-25); the Euclid Collaboration papers sometimes route through a
  collaboration contact — if so, CC the first author's institutional address.
- If Brian knows anyone in the Euclid strong-lensing SWG, a CC there may speed up
  the HST2EUCLID code request (Bergamini et al. 2025 is an Euclid Collaboration
  paper too).
- Do NOT state specific unpublished numbers beyond what you are comfortable
  sharing; the LEMON draft above mentions NMAD-level competitiveness only
  implicitly ("competitive on typical-lens accuracy") — adjust to taste.
