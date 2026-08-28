# Paper figures

Built by `make_figures.py` (run `python3 paper/figures/make_figures.py` from the
repo root). All inputs are local and verified 2026-08-03; numbers reproduce the
manuscript exactly. Each figure is written as both `.png` (preview) and `.pdf`
(vector, for LaTeX `\includegraphics`).

| file | what it shows | verified numbers | source data |
|---|---|---|---|
| `fig_realism_real_vs_sim.png` | Real Euclid Q1 lenses (top 2 rows) vs. our GEN5 simulated lenses (bottom 2 rows), identical asinh(img/sky-RMS) stretch. The realism "these are simulations" reveal. | — (qualitative) | real: `_local/reviews/q1_real_review/raw/q1_slde_eval_f2p85_zoom.h5` (real Euclid Q1, PyAutoLens θ_E); sim: `_local/reviews/g5cosmos_fj8_review/raw/euclid_sel.h5` (GEN5, frozen fj8 recipe) |
| `fig_cao_comparison.png` | Our **GEN4 native-HST** CNN vs. TinyLensGPU (Cao et al. 2025) on the 63 SLACS with Bolton 2008 b_SIE GT. Left: predicted-vs-true with ±1σ (ours) / 99.73% CI (Cao). Right: error CDF. | ours **R²=+0.64**, median 3.0%; Cao R²=−2.35, median 6.2% | `results/preds_l21_ens_real_slacs_images.csv`, `cao_joint_table.csv` |
| `fig_lemon_comparison.png` | Our **Euclid-arm** CNN vs. LEMON (Busillo et al. 2026) on the 29 shared Euclidised SLACS, Bolton GT. Left: predicted-vs-true with ±1σ both. Right: error CDF. | ours **R²=+0.57**, median 2.3%; LEMON R²=−4.26, median 20.7% | `lemon_comparison_package/combined_comparison.csv`, `lemon_predictions.csv`, `results/preds_l17_ens_euclid_slacs_images.csv` |
| `fig_benchmark_gallery.png` | Frozen real benchmark gallery: native HST/ACS F814W SLACS (top) + S4TM (bottom), θ_E-labeled, sorted by θ_E. The "what the model is tested on" gallery. | — (qualitative) | `real_slacs_images.h5`, `_local/reviews/audit/real_s4tm_images.h5` |
| `fig_realism_real_vs_sim_nativeHST.png` | **Native-HST GEN4** real SLACS (top 2 rows) vs. GEN4 simulated training images (bottom 2 rows), identical stretch. Sims show real field companions + correlated backdrop noise. | — (qualitative) | `_local/reviews/g4_merge_review/real_vs_train_G4.png` (title `train_g4_100k.h5`, 2026-07-11, the true GEN4 native render). **NOTE:** do NOT use `real_vs_train100k.png` (2026-07-06) — that is the pre-GEN4 hybrid without companions. |

## Notes / choices
- **Domains are kept honest.** Cao compares in the **native-HST** domain (both
  native). LEMON compares in the **Euclidised** domain (both Euclidised) — this is
  LEMON's own turf; using our native arm here would be apples-to-oranges.
- **`fig_realism_real_vs_sim` is the Euclid/GEN5 domain** because that is the only
  domain with BOTH real and matched simulated images available locally (the GEN4
  native-HST training h5 lives on the cluster). To make the native-HST version,
  re-run `make_figures.py` on the cluster pointing the real/sim paths at
  `real_slacs_images.h5` and the GEN4 native training h5. A pre-existing native
  panel (hybrid-100k recipe) is at `_local/previews/previews_stage2/real_vs_train100k.png`.
- Seeds are fixed (`np.random.default_rng`) so panels are reproducible; change the
  seed in `make_figures.py` for a different random draw.

## Suggested manuscript figure numbering
- **Fig. 1** = `fig_realism_real_vs_sim` (in §3, the generator)
- **Fig. 2** = `fig_benchmark_gallery` (in §3.1, the benchmark) — optional
- **Fig. 3** = `fig_cao_comparison` (in §5, conventional-modeling comparison)
- **Fig. 4** = `fig_lemon_comparison` (in §5, CNN-benchmark comparison)
