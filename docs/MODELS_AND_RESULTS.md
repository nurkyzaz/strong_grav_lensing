| realistic | 2.58% | 0.87–0.88 | — |
 
**Publishable ellipticity number: R² ≈ 0.79** (arc-only clean model). The realistic model's higher
R² may include a lens-light↔mass correlation cue (IllustrisTNG mass–light coupling), so it needs a
controlled test before being claimed. Ellipticity does **not** yet transfer to real SLACS.
 
An augmentation bug (flips/rotations scrambling orientation-dependent e1/e2 while leaving θ_E
unaffected) was caught and corrected — orientation-aware augmentation must transform (e1, e2).
 
## Compact-source result (LensFusion Phase-2 deliverable)
 
m3 is more accurate on compact sources (r_half < 0.15″): median +2.1%, MAE 0.063″, 11% failure,
vs. normal sources +3.5%, MAE 0.087″, 19% failure. This is the established regime for Brian's
soft-θ_E regularizer.
 
## Next model (paltas-trained) — plan
 
- Train the same CNN architecture on `simct_paltas_train.h5` (SIE labels, flat θ_E prior).
- Point `train_cnn_m3.py` at the per-image `theta_E` key (no `kappa_index` join; no θ_E² reweighting).
- Keep `normalize_images` at train time; images are raw electrons.
- Evaluate through the **same** `metrics_real.py` on the **same** 62 SLACS + 40 S4TM.
- Success = R² crosses to positive, median within ±5%, failure rate ≲10% (matching/beating Cao 2025).