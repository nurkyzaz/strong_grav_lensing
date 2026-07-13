# Email drafts — updated 2026-07-13 (Nurkyz ruling: keep only what the paper
# needs → the LEMON email. Bergamini email RETIRED: we now use the official
# Q1 GRID-PSF-VIS product directly, which supersedes the HST2EUCLID code ask
# (and keeps our operator fully independent). TinyLensGPU and Brian emails
# RETIRED per the same ruling. Prior drafts live in git history.)

**VERIFIED ADDRESS (from the paper's footnote):**
- LEMON corresponding author: **valerio.busillo@inaf.it** (V. Busillo, INAF-Capodimonte)

---

## To the LEMON team (Euclid Collaboration: Busillo et al. 2026, A&A)

Subject: Shared SLACS sample and per-lens predictions — LEMON (Q1) comparison from a two-domain θ_E CNN with spectroscopic-lensing ground truth

Dear Dr. Busillo and the LEMON team,

I am a researcher working on CNN-based Einstein-radius estimation for real
galaxy-galaxy lenses. Our training simulations follow the same structural
principle as LEMON — the deflector's light and mass belong to one physical
object — but implemented with real observed ingredients: real HST images of
SDSS-spectroscopic early-type galaxies as deflectors (each galaxy's measured
σ_v sets its θ_E), real COSMOS sources, and the measured Euclid Q1 VIS PSF
(from the released MER GRID-PSF product) in the degradation operator. We
evaluate against the independent, uniform spectroscopic-lensing b_SIE values
of Bolton et al. (2008) for 62 SLACS and 40 S4TM lenses, in two domains from
one population model:

- Euclid-like domain (Q1-PSF-degraded real HST cutouts):
  bias −0.010″, RMSE 0.137″, NMAD 0.056″, R² = 0.71, catastrophic rate 15%;
- native HST domain: bias +0.005″, RMSE 0.152″, NMAD 0.048″, R² = 0.64
  (and RMSE 0.088″ / R² = 0.90 on the lower-mass S4TM sample).

Your Q1 LEMON paper is the closest published work to ours, and we would like
to compare with it as carefully and fairly as possible — in your conventions
and your evaluation domain. Two things would make the comparison exact rather
than distribution-level, and we would of course credit them explicitly:

1. The list of the 29 SLACS systems in your 60-lens Euclidised-HST validation
   set, so we can report a same-lens head-to-head table.
2. If possible, your per-lens θ_E predictions (and uncertainties) for those
   systems — aggregate metrics hide sample-composition effects, and a
   per-lens scatter plot of the two methods would be more informative for
   both papers.

We would gladly share our per-lens predictions on the same systems in return
(they are ready). We believe a careful cross-validation between a fully
synthetic Euclid-native pipeline and a real-ingredient HST-anchored one would
strengthen confidence in both ahead of DR1.

Thank you for the impressive work — the Q1 modeling papers are a real service
to the community.

Best regards,
Nurkyz Ydyrysova
[affiliation]

---

Notes for Nurkyz before sending:
- The per-lens numbers quoted are eval #19 (Euclid domain, G4-trained cnv2_3
  on the real-PSF benchmark) and eval #21 (native) — update if a later eval
  supersedes them before you send.
- Euclid Collaboration papers sometimes route through a collaboration
  contact — if the footnote address bounces, CC the first author's
  institutional address from the A&A page.
