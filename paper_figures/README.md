# Paper figures

- `figure1_real_vs_sim.png` — **Figure 1**. Real SLACS cutouts (top 2 rows) vs. hybrid v2
  training images (bottom 2 rows), identical asinh(img/sky_rms) stretch. Random draw; rerun
  `side_by_side_real_sim.py` for a different sample.
- `figure2_pred_vs_true.png` — **Figure 2**. Predicted vs. true θ_E: m3 baseline (grey) vs.
  hybrid v2 (orange/red), circles = SLACS, triangles = S4TM. The green band is Cao et al.
  2025's *claimed* ≲5% deviation threshold drawn for reference — **not** their actual
  per-lens data (that matched comparison is still a pending ablation, see paper §4.5).
- `supplementary_dataset_gate.png` — dataset realism gate (sim vs. real: normalized pixel
  histogram, radial profile, peak/sky distribution) underlying Table 1. Not currently cited
  as a numbered figure in the draft; included as backup evidence if your professor asks how
  the simulation was validated.

Regeneration commands (run on the cluster):
```
# Figure 1
python side_by_side_real_sim.py --real ~/einstein_cnn/real_slacs_images.h5 \
    --sim ~/einstein_cnn/train_hybrid_100k_v2.h5 --n 8 --seed <any> --out fig1.png

# Figure 2 (needs make_figure2.py, copied to ~/einstein_cnn/)
python make_figure2.py --out figure2_pred_vs_true.png
```
