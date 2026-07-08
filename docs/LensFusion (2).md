# **CNN-Based Einstein Radius Prediction as an Auxiliary Constraint for LensFusion**

## **Overview**

Train a convolutional neural network (CNN) to predict the Einstein radius (θ\_E) directly from a lensed measurement image. This gives LensFusion an independent, global estimate of the lens mass scale. Feeding that estimate into the inference framework as a soft constraint helps suppress the under- and over-magnified reconstructions that LensFusion currently produces for some systems — especially compact sources, where the lensed arcs carry little information and the likelihood is weak.

This is the first of several possible "helper" CNNs discussed with Brian. The full menu is:

1. Separate the foreground lens-light profile from the measurement image (hardest).  
2. Segment the arc-light (deflected source) region into a mask — feeds directly into the gradient mask / regularization in the inference (medium difficulty).  
3. Predict the Einstein radius from the measurement image (easiest, well supported by literature).

Einstein-radius prediction (option 3\) is the agreed starting point. Team split: Edgar focuses on the denoising part, Nurkyz on the CNN part.

## **Background and motivation**

LensFusion reconstructs the unlensed source light and the lens convergence map from a single noisy lensed image, using learned diffusion priors plus a ray-tracing likelihood (DAPS for broad exploration, then PnP-DM for refinement). It recovers θ\_E to about 1% on most systems.

However, a subset of reconstructions fit the image well but settle on a wrong magnification — the inferred θ\_E (and enclosed mass) is too large or too small. The paper's own success criterion flags these when |Δθ\_E / θ\_E| \> 0.15. These failures cluster at small source sizes, because compact sources make short, weakly structured arcs that poorly constrain the mass scale.

A CNN that reads θ\_E straight from the image gives an independent anchor for the mass scale, which the sampler can be gently pulled toward.

Important: this targets the mis-magnification / weak-likelihood failure mode — NOT the mass-sheet degeneracy. The Einstein radius is invariant under the mass-sheet transformation, so it cannot resolve that particular degeneracy. (The paper treats those as two separate issues.)

Definition used throughout: θ\_E is set by the mean-convergence condition κ̄(\< θ\_E) \= 1, matching LensFusion's own evaluation code (the `einstein_radius_hard` function; Eq. 19 in the paper).

## **Goals**

1. Build a CNN regressor: input a lensed image, output θ\_E in arcseconds.  
2. Reach a small fractional error on simulated test data (target a few percent; exact bar to confirm — see open questions).  
3. Later (Phase 2, with Brian): feed θ\_E into the sampler as a soft constraint and measure whether it reduces mis-magnified failures.

## **Plan**

### **Phase 1 — the CNN (main near-term focus)**

**Data.**

* Start single-band, which is simplest. HST COSMOS F814W is the natural first choice, since LensFusion's source prior already comes from COSMOS. Euclid VIS is an alternative single-band option.  
* Then scale to the project's multi-band setup: the simulated lens light spans 7 bands (CLAUDS u, CFHT MegaCam r, and HSC g, r, i, z, y). The background source-galaxy data is sourced separately in comparable filters; a slight source/lens filter mismatch is acceptable and is common in the literature.  
* Ground-truth label: θ\_E computed from the convergence map κ used to generate each mock (κ̄(\< θ\_E) \= 1).  
* Split train / validation / test (e.g. 80 / 10 / 10). Augment with rotations, flips, and small translations. Train across the noise levels LensFusion uses (σ\_N ≈ 0.01–0.1) for robustness.

**Architecture.** Start from a standard CNN regressor (VGG- or ResNet-style backbone) → global average pooling → one or two dense layers → a single linear output (θ\_E in arcsec). Compare a small ResNet against the VGG baseline.

**Training.** MSE or Huber loss. Report MAE, fractional error (Δθ\_E / θ\_E), and R². Adam optimizer, early stopping.

### **Phase 2 — integration into LensFusion (later, with Brian)**

* During sampling, each candidate convergence map κ has its own θ\_E^sample. Add a soft penalty that pulls the sampled mass scale toward the CNN value θ\_E^CNN(y).  
* Practical note: the current `einstein_radius_hard` is not differentiable (it uses argmax / interpolation), so Phase 2 will need a differentiable ("soft") θ\_E estimator to put the penalty inside the gradient-based update. Also, κ is sampled in a transformed (asinh) space, so the penalty acts through that mapping.

## **Evaluation**

* **CNN alone:** MAE, fractional error, and scatter (16–84 percentile) on the test set. Compare to Hezaveh+17 and the ground-based CNN papers.  
* **With integration (Phase 2):** run LensFusion with and without the θ\_E constraint on a fixed set of test mocks, and check: (a) reduced θ\_E fractional error, (b) fewer mis-magnified / fragmented failures, (c) no worse image-space χ².

## **Deliverables**

1. Trained θ\_E CNN (weights \+ code) — single-band first, then multi-band.  
2. Documentation: data generation, architecture, training, and performance metrics.  
3. (Phase 2\) Integration code, plus a short validation report on whether the constraint reduces failures.

## **Key references**

* **Hezaveh, Perreault Levasseur & Marshall (2017), Nature** — showed CNNs can estimate lens-model parameters, including the Einstein radius, directly from images, far faster than traditional modeling. The foundational reference for this project.

Hezaveh, Perreault Levasseur & Marshall (2017), *Fast Automated Analysis of Strong Gravitational Lenses with Convolutional Neural Networks*, Nature 548, 555–557.

* arXiv (free PDF): [https://arxiv.org/abs/1708.08842](https://arxiv.org/abs/1708.08842)

**Their code: [https://github.com/yasharhezaveh/Ensai/](https://github.com/yasharhezaveh/Ensai/tree/master/docs)**

**Changed version of their code: [https://github.com/Unique-Divine/Neural-Networks-for-Gravitational-Lens-Modeling/tree/master/images](https://github.com/Unique-Divine/Neural-Networks-for-Gravitational-Lens-Modeling/tree/master/images)** 

**The papers that match YOUR data regime (ground-based, multi-band) — most useful for you specifically:**

* *Neural network prediction of model parameters for strong lensing samples from Hyper Suprime-Cam Survey* (MNRAS 2025). This is the closest match — HSC bands like yours, trained on HSC-like sims, tested on real SuGOHI lenses, predicting Einstein radius among other parameters.  
  * [https://arxiv.org/abs/2404.18897](https://arxiv.org/abs/2404.18897) (PDF: [https://arxiv.org/pdf/2404.18897](https://arxiv.org/pdf/2404.18897))  
  * Journal: [https://academic.oup.com/mnras/article/540/4/3384/8159882](https://academic.oup.com/mnras/article/540/4/3384/8159882)  
* *Deep Learning in Wide-field Surveys: Fast Analysis of Strong Lenses in Ground-based Cosmic Experiments* — the gri-band study where they predict the Einstein radius to within about 10–15% using only ground-based images: [https://arxiv.org/abs/1911.06341](https://arxiv.org/abs/1911.06341) [arxiv](https://arxiv.org/pdf/1911.06341)  
* *Enhancing Gravitational Lens Study with Deep Learning (dropout regularization)* — recent (2026), builds a CNN on CSST-catalog sims to predict SIE parameters including θ\_E: [https://arxiv.org/html/2603.06339](https://arxiv.org/html/2603.06339)

* **Perreault Levasseur, Hezaveh & Wechsler (2017), ApJL** — adds uncertainty estimates (Bayesian / dropout) to the same approach; relevant if we want error bars on θ\_E^CNN.  
* **Ground-based CNN parameter-prediction work (HSC / SuGOHI-type studies)** — most relevant to our data regime, since these train on HSC-like simulations and test on real lenses using ground-based bands like ours.  
* **AgileLens (Euclid Q1)** — the VGG16-style architecture and Euclid-like preprocessing pipeline we can adapt for regression.

## **Open questions for Brian**

1. Single-band (HST F814W) first, then multi-band — is that the right order?  
2. Confirmed θ\_E range? (Literature uses roughly 0.5″–2.5″, which matches LensFusion's mocks.)  
3. Do we already have a pipeline that outputs θ\_E labels for the mocks, or do I build it?  
4. What θ\_E accuracy is actually "good enough" to help the sampler? (Even \~10% may be plenty, since the failures we target are already \> 15% off.)  
5. Should validation include real lenses? If so, note our data is ground-based (HSC / CFHT / CLAUDS), while SLACS is HST / F814W — a different regime.

Meeting 26 May 

**CNN**   
HST working on 1 or 2 bands   
Euclid works with 4 bands   
Usual Einstein radius ranges from 0.7 to 1.7 arcseconds  
    
**Do we already have a pipeline that outputs** θ**\_E labels for the mocks, or do I build it?**  
we don’t have it   
**how we should prep the lens data:**   
**existing dataset**   
**on the github he uploaded the dataset , so I can download it**   
**only source light and smth else**   
**I may first use the CNN from that Nature 2017 paper**   
**Gotta be careful with the data for training**   
**first follow their approach**   
**use data from Adams group: [https://iopscience.iop.org/article/10.3847/1538-4357/accf84](https://iopscience.iop.org/article/10.3847/1538-4357/accf84)**  
   
**use simulated data**   
**test 1 \- untrained data mock lens mass**   
**test 2 important \- real observation images**  
**abd then compare output of the model with the reported value from the literature**   
   
**lenstronomy \- should be good for parametric models**   
**or smth else**  
**to create the image of einstein radius** 

---

## **First, the big picture in simple words**

Here's what you're doing in plain English. You want to train a neural network that looks at a picture of a gravitational lens and guesses a single number — the Einstein radius (how wide the ring/arc is, in arcseconds). You'll train it on fake/simulated images where you already know the answer, then test it on real telescope images and check whether your answer matches what astronomers published.

The tool you'll use to simulate lenses is called **lenstronomy**. It's a Python package, well-documented, and it can both simulate lensed images *and* compute the Einstein radius from a mass map — which is exactly the two things you need.

---

## **Your 5-week plan, step by step**

### **Week 1 — Read, install, and understand your data**

**What to do:**

First, read the Hezaveh+17 paper (https://arxiv.org/abs/1708.08842) carefully — not just the abstract. Focus on: what images they fed in, what their CNN looked like, and what numbers they reported. You'll be copying their approach, so you need to actually understand it.

Second, go to the **LensFusion GitHub** and download the dataset Brian mentioned. Look inside it and figure out what's there. Brian said it has "source light and something else" — that something else is likely **convergence maps** (the κ maps that describe the mass distribution). If so, you can compute θ\_E labels from those directly. Check by opening a sample file and printing its contents.

Third, go to the **Adams group paper** (https://iopscience.iop.org/article/10.3847/1538-4357/accf84) and understand what images and data they provide. This will be your main training data.

Fourth, install your tools:

pip install lenstronomy

pip install torch torchvision

**What you should know by end of week 1:** What data you have, what's missing, and whether you need to simulate more images yourself with lenstronomy or can use existing ones directly.

---

### **Week 2 — Build the θ\_E label pipeline and prepare your training data**

This is the most important week practically, because without correct labels your CNN learns nothing.

**What to do:**

You need a pipeline that takes a lensed image and produces one number: the Einstein radius. Since you're using simulated data, you have two ways to get labels:

**Option A — parametric simulation (simplest).** Use lenstronomy to simulate images where you *choose* the Einstein radius yourself. You draw a random θ\_E (say, uniformly between 0.7 and 1.7 arcseconds as Brian confirmed), simulate the lensed image, and the label is just the number you chose. No computation needed — you already know the answer. lenstronomy's `SimulationAPI` does this:

from lenstronomy.SimulationAPI.sim\_api import SimAPI

**Option B — from convergence maps.** If the LensFusion dataset has κ maps, you compute θ\_E by finding the radius where the average κ inside equals 1\. lenstronomy has an exact function for this: `effective_einstein_radius_grid()` in the Analysis package computes exactly this — the radius with mean convergence \= 1 on a grid, which is the same definition LensFusion uses. This is the better label to use if you want your CNN to match what LensFusion measures.

In practice: **do Option A first** (faster to get running), then switch to Option B once you know your pipeline works.

For the image itself — use HST-like settings (single band, 1–2 channels), pixel scale around 0.05–0.1 arcsec/pixel, add realistic noise. lenstronomy has HST camera presets built in so you don't have to guess noise levels.

Split your dataset: 80% train, 10% validation, 10% test. Aim for at least 10,000–20,000 simulated images if you're generating them — the Hezaveh+17 paper used tens of thousands. For augmentation: random rotations and flips are enough.

---

### **Week 3 — Build and train the CNN**

**What to do:**

Follow the Hezaveh+17 approach as Brian said. Their network was a fairly standard CNN:

Input image → several Conv layers → Flatten → Dense layer → output: 1 number (θ\_E)

In PyTorch, the simplest starting point is a pretrained **ResNet-18** with the final layer replaced to output one number instead of 1000 classes:

import torchvision.models as models

model \= models.resnet18(pretrained=True)

model.fc \= torch.nn.Linear(512, 1\)  \# replace final layer

Use **MSE loss** (mean squared error) or **Huber loss** (more stable if some labels are very wrong). Use **Adam optimizer**, learning rate around `1e-4`. Train with early stopping — stop when validation loss stops improving for \~10 epochs.

Track these three numbers on your validation set:

* **MAE**: average absolute error in arcseconds  
* **Fractional error**: |predicted − true| / true — target below 10%  
* **R²**: how well your predictions correlate with truth (target \> 0.95)

**What you should have by end of week 3:** A trained model that makes reasonable predictions on your validation set. Even rough results (15–20% fractional error) are fine at this stage — the point is the pipeline works.

---

### **Week 4 — Run your two tests**

This is what Brian specifically asked for.

**Test 1 — Mock data not used in training.** Take the LensFusion test mocks (download from GitHub) and run your CNN on them. These have different mass profiles than what you trained on (IllustrisTNG profiles instead of simple SIE). Report your fractional error. This tells you whether your CNN generalizes beyond the training distribution. The HSC paper found that a network trained on simulated data reproduces Einstein radii with an accuracy of about 10–20%, a bias less than 5%, and an outlier fraction of the order of 10% — use this as your benchmark to compare against.

**Test 2 — Real observations.** You need real lens images with published Einstein radii to compare against. The best dataset for this is **SLACS** (Bolton et al. 2008\) — it's HST/F814W images of real galaxy-galaxy lenses with measured θ\_E values from the literature. Download the images from the HST archive (MAST: https://mast.stsci.edu), run your CNN, and compare your predicted θ\_E to the published values. Aim for \~10–20 systems to start.

This is the most impressive part of the project scientifically because it's real data, not simulations.

---

### **Week 5 — Write up, document, and discuss integration**

**What to do:**

Make clean plots:

* Scatter plot: predicted θ\_E vs true θ\_E (should be along the diagonal)  
* Histogram of fractional errors  
* A few example images with the predicted and true θ\_E labeled

Write brief documentation: how to generate data, what the model architecture is, how to run inference on a new image.

Have a conversation with Brian about Phase 2 — where the CNN output plugs into the LensFusion sampler. You don't need to implement it this week, just be ready to discuss where in the code it would go.

---

## **The links you need**

| What | Link |
| ----- | ----- |
| Hezaveh+17 paper (your main reference) | https://arxiv.org/abs/1708.08842 |
| Adams group paper (your training data) | https://iopscience.iop.org/article/10.3847/1538-4357/accf84 |
| lenstronomy docs | https://lenstronomy.readthedocs.io |
| lenstronomy GitHub | https://github.com/lenstronomy/lenstronomy |
| deeplenstronomy (wrapper for easy dataset generation) | https://arxiv.org/abs/2102.02830 |
| HSC CNN paper (matches your data regime, good benchmark) | https://arxiv.org/abs/2404.18897 |
| MAST archive (real HST images for Test 2\) | https://mast.stsci.edu |

One honest note: I couldn't fetch the Adams group paper directly because the journal blocks automated access. Before you go further, **download that paper and confirm what data they actually provide** — specifically whether it's images you can download or whether you need to simulate your own using their described setup. That answer changes how much time Week 2 takes. If you're unsure after reading it, bring it to Brian.

