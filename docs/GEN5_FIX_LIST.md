# GEN5 Fix List — physical consistency, ordered so fixes don't break each other

**Reset (Nurkyz 2026-08-03/12):** the gallery (fj13) still fails by eye. My
measurements were unreliable (pixel-scale + contamination errors); the EYE is the
ground truth. Cards 207/157/132 confirm: thick near-full rings dominating a tiny
faint deflector dot. This doc trusts the visual and fixes the PHYSICS.

## The one root problem (the inversion)
Real Euclid lens = a BIG bright foreground elliptical (the deflector) that
DOMINATES, with a THIN, FAINTER arc partially wrapped around it.
Our sim = a TINY faint deflector dot with a THICK bright ring dominating. Inverted.
Most comments (tiny deflectors, no big deflectors, arcs too thick/circular,
deflector invisible) are this one inversion.

## Dependency rule (how to not break one fix with another)
Two independent axes, never confuse them:
- **BRIGHTNESS / photometry** (magnitudes, Faber-Jackson, arc↔deflector ratio,
  magnification coupling) — these are ALREADY MATCHED on paper. Do NOT touch them
  when fixing shape.
- **SIZE / SHAPE / EXTENT** (deflector envelope, arc thickness, arc completeness)
  — these are WRONG by eye. Fix these WITHOUT changing total magnitudes.
Every fix below states which axis it touches and what must stay frozen.

## Priority-ordered fixes

### 0. DEFLECTOR peak-over-noise is 8x too LOW  (the real root cause, found 2026-08-12)
- ROBUST metric (unit-safe): deflector peak / sky-RMS. Real Euclid **248**, ours **33**.
- Decomposed: sky-RMS matches real (0.0056 vs 0.0059, 1.1x) — the NOISE IS FINE.
  The deflector PEAK is 8x too faint (0.18 vs 1.49, same units). So "background too
  noisy" is really "**deflector too faint**": it barely clears the (correct) noise,
  so only the bright core shows = a dot; the rest of the galaxy is under the noise.
- This is WHY the de Vauc envelope (#1 below) barely helped in the deflector-only
  test: adding faint wings to a too-faint core still sits under the noise.
- CAUTION: total deflector MAG appears to "match" real (21.4) on paper, yet the
  PEAK is 8x low — my mag/size/noise measurements have been unreliable (units +
  contamination). TRUST the peak/sky metric + the eye.
- CANDIDATE CAUSES (decide with the eye, not my numbers): (a) euclidise PSF over-
  smoothing the deflector -> low peak; (b) real deflectors genuinely brighter than
  the mag we assigned; (c) the over-concentrated-then-spread stamp profile. Cleanest
  route that SIDESTEPS all the unreliable stamp measurements: use the REAL Euclid
  deflector light (sersic_lens_light models) which have the right peak/sky by
  construction.
- **RESOLVED 2026-08-12: FJ mag0 21.39 -> 19.2** (peak/sky 38 -> 277 = real 248). The
  catalog VIS mag (21.4) is a DIFFERENT flux system than the eval cutouts the CNN/eye
  see; matching it made deflectors 2.5 mag too faint. LESSON: the eval cutouts are the
  ground truth for brightness, NOT the PyAutoLens catalog mag. fj18 side-by-side LOOKED better on 8 cards, but **Nurkyz eyeball on the full gallery: STILL DOTS + background still visibly noisy.** So peak/sky is necessary but NOT sufficient — the deflector appearance is UNRESOLVED. STATUS: ❌ STILL OPEN. See GEN5_HANDOFF.md.

### 1. DEFLECTOR must render as a BIG extended elliptical, not a dot  (was TOP; now second to #0)
- Real: extended de Vaucouleurs galaxy, visible light filling much of the frame
  (wings to ~2-3″), dominates the arc.
- Now: tiny faint core; the faint outer envelope is missing/below noise → "dot".
- Axis: SIZE/EXTENT. FREEZE: total deflector magnitude (FJ mag0 21.39 ∝ θ_E) and
  the arc↔deflector ratio.
- Candidate causes to test (eyeball each): (a) mig_scale z-migration over-shrinks
  the galaxy; (b) the deflector-stamp cleaning/edge-smooth trimmed the wings;
  (c) FJ concentrates the fixed flux into the core. Likely (a)+(b).
- Candidate fix: render deflectors LARGER / less-shrunk (or use real Euclid Q1
  deflector light profiles), so the same total mag is spread into a real galaxy.
- STATUS: ❌ OPEN — the #1 fix.

### 2. ARC must be THIN and partial, fainter than the deflector
- Real: thin arc, 25-50% of a ring, clearly fainter than the deflector.
- Now: thick ring, sometimes near-full, dominating.
- Axis: SIZE/SHAPE. FREEZE: arc magnitude and arc∝magnification∝θ_E coupling.
- Note: once #1 makes the deflector big+dominant, the arc will look far thinner
  and subordinate automatically — so DO #1 FIRST, then re-judge arc thickness.
- Candidate fix (if still thick after #1): more compact source (thinner arc).
- STATUS: ❌ OPEN (re-judge after #1).

### 3. ARC completeness — partial, off-axis (already ~right, keep)
- Real: partial arcs, at the poles, never full rings. Source off-axis.
- Now: mostly partial (some still near-full like #207) via absolute source offset.
- Axis: SHAPE. Keep the absolute offset; re-check the near-full ones after #1.
- STATUS: ⚠️ mostly OK, re-verify.

### 4. NOISE — re-verify by eye (you say too noisy)
- My measurement said sky RMS matches real; you see too noisy (e.g. #132).
- Axis: NOISE. Re-examine honestly — is it genuinely high, or do the FAINT
  deflectors (#5) just leave noise uncovered? Adjust only if your eye confirms.
- STATUS: ⚠️ RE-OPEN, eyeball.

### 5. FAINT / invisible deflectors on some cards
- Some deflectors too faint (e.g. #132 mag 23.3).
- Axis: BRIGHTNESS tail. The FJ faint tail was truncated to real's range, but by
  eye some are still too faint — likely BECAUSE they're tiny dots (#1). Re-judge
  after #1; the envelope fix should make even faint deflectors visible.
- STATUS: ⚠️ likely resolved by #1; re-verify.

### Already matched by eye + number (keep frozen, do not disturb)
- θ_E range (real ≤ ~2.9), companions (sparse ~1/img), arc↔deflector brightness
  ratio (deflector brighter), magnification coupling (big lens → bright arc).

## Workflow (Nurkyz eyeballs)
Fix #1 → render a small pilot → serve gallery → Nurkyz rates by eye (card numbers
+ issue, like today) → iterate. Only ONE size/shape knob changes per pilot; all
frozen brightness knobs carried unchanged (the complete recipe in
GEN5_REALISM_PLAN.md). Re-judge #2-#5 only AFTER #1, since #1 changes the whole look.
