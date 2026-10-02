"""GreekScansion - scanning Classical Greek hexameter, with a certificate.

The public surface is deliberately small:

    from greekscan import scan, scan_all, weights, syllabify

`scan` returns a Result whose `verdict` is "unique", "ambiguous" or
"unscannable". "unique" means the metre admitted exactly one reading of the
line, which is the only sense in which this program claims anything.
"""

from .metre import (
    MAX_SYLLABLES,
    MIN_SYLLABLES,
    SYNIZESIS_MODES,
    Reading,
    Result,
    foot_patterns,
    scan,
    scan_all,
)
from .quantity import EITHER, HEAVY, LIGHT, render, weight, weights
from .syllable import Syllable, syllabify, variants

__all__ = [
    "EITHER",
    "HEAVY",
    "LIGHT",
    "MAX_SYLLABLES",
    "MIN_SYLLABLES",
    "SYNIZESIS_MODES",
    "Reading",
    "Result",
    "Syllable",
    "foot_patterns",
    "render",
    "scan",
    "scan_all",
    "syllabify",
    "variants",
    "weight",
    "weights",
]

__version__ = "0.1.0"
