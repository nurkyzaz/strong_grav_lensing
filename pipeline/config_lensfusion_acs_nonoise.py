# config_lensfusion_acs_nonoise.py -- Stage-1.3 variant: identical to
# config_lensfusion_acs.py but with detector noise OFF. The hybrid pipeline
# (hybrid_combine.py) adds real empty-cutout backgrounds + calibrated topup
# noise instead; adding paltas noise on top would double-count it.
import os
import sys

sys.path.insert(0, os.path.expanduser('~/cosmos_acs/tiles'))
from config_lensfusion_acs import *   # noqa: F401,F403

no_noise = True
