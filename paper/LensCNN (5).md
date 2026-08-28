## **4\. CNN Architecture and Training**

We train a scale-conditioned CNN (ResNet or InceptionNeXt) with 4 residual stages, global average pooling, scale-scalar concatenation, and an MLP head. Input normalization: arcsinh compression (a=1.0) followed by per-image z-score standardization. The loss is Gaussian-NLL (μ, log σ²) for uncertainty quantification. Training: 40 epochs, batch size 64, Adam optimizer, cosine LR schedule, flip/rotation augmentation. Model selection is on sim-val only (deflector-disjoint, PSF-disjoint, seed-disjoint). Test-time augmentation: 8× dihedral TTA, with total σ \= aleatoric variance (mean over views) \+ epistemic view-spread variance.

