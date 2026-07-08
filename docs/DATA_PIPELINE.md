
## Retired approach: bespoke composite generator (for the record)
 
Painted a synthetic/real arc + lens light onto real cutouts, hand-tuning brightness ratios.
Superseded because it required unphysical flux tuning and could not source SLACS-sized real lens
light from a single COSMOS tile. Full failure chain (v0→v3) in `DECISIONS_LOG.md`. Diagnostic
`diagnose_simct.py` (arc geometry, PSF FWHM, lens peak/sky, arc thickness) is still useful for
sanity-checking any generator.
 
## Grids and conventions
 
- Composites and real cutouts: **128 px @ 0.05″/px = 6.4″** (matches SLACS cutouts, HSTempty, paltas).
- Native IllustrisTNG κ maps: 0.06047″/px (= 7.68/127) — relevant only to the legacy κ pipeline.
- z_lens = 0.5, z_source = 1.5; θ_E range 0.5–2.5″ (typical observed 0.7–1.7″).
## Real-lens benchmark data (test set — keep separate from training)
 
- `real_slacs_images.h5` (62), `real_s4tm_images.h5` (40): images, names, `theta_E_pub` (b_SIE),
  optional per-pixel noise (`--with-noise`). Built by `build_real_lens_labels.py` (VizieR) +
  `fetch_real_lens_images.py` (MAST → ACS/WFC F814W drizzled `_drc` → 6.4″ → 128×128).
- These are the evaluation set only; never mix into training.