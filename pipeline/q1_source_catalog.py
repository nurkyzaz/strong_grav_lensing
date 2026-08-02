"""GEN5 C37 — paltas source class that draws REAL delensed Euclid Q1 source-plane
reconstructions (from q1_sources_*.h5, built by analysis/build_q1_sources.py) as
the lensed-source population, replacing the low-z COSMOS stamps that produced
faint/diffuse arcs.

Key design choice: these are ALREADY real high-z Euclid sources at Euclid VIS
brightness. So we set the stamp's metadata z EQUAL to the drawn z_source -> the
base GalaxyCatalog applies NO angular-size rescale and NO k-correction, and we
set ab_zeropoint = output_ab_zeropoint -> NO zeropoint rescale. The native
delensed AMPLITUDE is preserved, so surface brightness is conserved through the
re-lensing and the arc lands at real Euclid surface brightness automatically.
The one free knob is q1_source_pixscale (source-plane arcsec/px) = arc thickness,
calibrated against the real Q1 arc width.
"""
import h5py
import numpy as np
from paltas.Sources.galaxy_catalog import GalaxyCatalog


class Q1SourceCatalog(GalaxyCatalog):
    # native amplitude preserved: set at init to output_ab_zeropoint (factor 1)
    ab_zeropoint = 25.94
    required_parameters = ("random_rotation", "output_ab_zeropoint", "z_source",
                           "center_x", "center_y", "q1_source_file",
                           "q1_source_pixscale")

    def __init__(self, cosmology_parameters, source_parameters):
        # keep the input zeropoint equal to the output -> no ZP rescale
        Q1SourceCatalog.ab_zeropoint = float(
            source_parameters["output_ab_zeropoint"])
        super().__init__(cosmology_parameters, source_parameters)
        with h5py.File(source_parameters["q1_source_file"], "r") as f:
            self.images = np.array(f["sources"][:], dtype=np.float64)
        self.pixscale = float(source_parameters["q1_source_pixscale"])
        print("Q1 SOURCE LIBRARY ACTIVE: %d real delensed Q1 sources, "
              "pixscale %.4f\"/px (arc-thickness knob)"
              % (len(self.images), self.pixscale))

    def __len__(self):
        return len(self.images)

    def image_and_metadata(self, catalog_i):
        img = self.images[catalog_i].copy()
        # z == drawn z_source  ->  z_scale_factor = 1, k-correction = 0
        z = float(self.source_parameters["z_source"])
        metadata = {"pixel_width": self.pixscale, "z": z}
        return img, metadata
