## **A\&A rules:** 

Context. Optional, leave empty if necessary. The heading “Context” is used when needed to give background information on the research conducted in the paper

Aims. Mandatory. The objectives of the paper are defined here.

Methods. Mandatory. The methods of the investigation are outlined here

Results. Mandatory. The results are summarized here.

Conclusions. Optional, leave empty if necessary. “Conclusions” can be used to explicit the general conclusions that can be drawn from the paper.

Keywords. 

## **Abstract**

Context. Deep learning enables fast parameter estimation for the \~10⁵ strong gravitational lenses expected from current and upcoming surveys like Euclid and Roman. However, CNNs trained on simplified simulations often degrade substantially on real telescope data—a "sim-to-real gap" whose physical origins remain poorly understood.

Aims. We aim to close this gap by building a physically self-consistent, real-ingredient simulation pipeline, training a CNN to predict the Einstein radius (θ\_E), and systematically ablating each realism component to determine what matters most.

Methods. Our generator combines real HST galaxies (with measured SDSS velocity dispersions σ\_v → θ\_E) as deflectors, real COSMOS sources, real HST empty-sky backdrops, and real focus-diverse empirical PSFs—all in physical e⁻/s units. The key innovation is observational self-consistency: each training system uses one real galaxy for both its light and its mass. We train a scale-conditioned CNN with a Gaussian-NLL uncertainty head.

Results. On the frozen spectroscopic-lensing benchmark of 62 SLACS and 40 S4TM lenses (Bolton et al. 2008 b\_SIE), our native-HST model achieves R²=+0.64 (SLACS) and R²=+0.90 (S4TM)—beating the m3 baseline (R²=-1.02) and matching conventional modeling (Cao et al. 2025\) at \~10⁶× the speed. On the Euclid-degraded SLACS benchmark (real Q1 VIS PSF), we reach R²=+0.71, surpassing the leading CNN benchmark (LEMON) on every aggregate θ\_E metric. 

On real Euclid Q1 lenses (N=322, PyAutoLens GT), we achieve \_(in the process)\_\_ , also surpassing LEMON (hopefully). 

Experiments show that real background noise is the most important realism ingredient(\>10× effect). The decisive breakthrough, however, is ensuring that each deflector galaxy provides both its light and its mass: without this physical link, even a flat prior fails to improve real-lens performance. The network also learns *to* estimate its own uncertainty, and this uncertainty strongly correlates with actual error (Spearman ρ=+0.71).

Conclusions. Physical realism in training simulations is the key to closing the sim-to-real gap. Our instrument-agnostic generator enables rapid adaptation to Euclid, Roman, and future surveys. The code and data are publicly available.

Keywords. gravitational lensing: strong — methods: data analysis — techniques: image processing — galaxies: elliptical and lenticular, cD

