"""Turning syllables into weights, and refusing to guess where it cannot know.

A syllable is heavy if its vowel is long or a diphthong, or if a consonant
closes it. It is light if a short vowel stands open. Three situations are
genuinely undecidable from the spelling, and each yields EITHER rather than a
coin flip:

  * a dichronon (α, ι, υ) standing open - the spelling does not record length;
  * a stop plus liquid, which may or may not close the syllable before it;
  * a long vowel ending a word before another vowel, which epic correption may
    shorten.

EITHER is the whole point of the design. The metre, not this module, resolves
it - and a line whose weights leave more than one legal reading is reported as
ambiguous rather than silently given one.
"""

from __future__ import annotations

from .orthography import ALWAYS_LONG, ALWAYS_SHORT
from .syllable import Syllable, syllabify

HEAVY = "H"
LIGHT = "L"
EITHER = "E"


def _nucleus_is_long(syllable: Syllable) -> bool:
    # Any multi-letter nucleus is long: a diphthong, or two vowels run together
    # by synizesis.
    if len(syllable.nucleus) >= 2:
        return True
    vowel = syllable.nucleus[0]
    return vowel.char in ALWAYS_LONG or vowel.explicitly_long


def _nucleus_is_short(syllable: Syllable) -> bool:
    if len(syllable.nucleus) >= 2:
        return False
    vowel = syllable.nucleus[0]
    return vowel.char in ALWAYS_SHORT or vowel.explicitly_short


def weight(syllable: Syllable) -> str:
    """The weight of one syllable: HEAVY, LIGHT, or EITHER."""
    long_nucleus = _nucleus_is_long(syllable)

    if syllable.optionally_closed:
        # A long vowel is heavy whether or not the cluster closes the syllable,
        # so only a short or unknown vowel is left undecided.
        return HEAVY if long_nucleus else EITHER

    if syllable.closed:
        return HEAVY

    if long_nucleus:
        return EITHER if syllable.correptable else HEAVY

    if _nucleus_is_short(syllable):
        return LIGHT

    return EITHER  # a dichronon standing open


def weights_for(syllables: list[Syllable]) -> list[str]:
    return [weight(s) for s in syllables]


def weights(line: str) -> list[str]:
    """The weight of every syllable in the plain reading of a line."""
    return weights_for(syllabify(line))


def render(seq: list[str]) -> str:
    """Weights as marks, in ASCII so a cp1252 console can print them."""
    return "".join({HEAVY: "-", LIGHT: "u", EITHER: "?"}[w] for w in seq)
