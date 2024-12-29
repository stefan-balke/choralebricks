"""ChoraleBricks
"""

# import modules as sub-namespaces (e.g. `tdsp.generators.SinusoidalOsc`)
from . import constants
from . import dataset
from . import generators
from . import utils

# import specific function/class into global namespace
from .chord import Chord, ChordSequence