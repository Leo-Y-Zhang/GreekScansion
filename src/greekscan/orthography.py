"""Reading Greek text as sounds rather than as glyphs.

Scansion depends on the phonology, not on the editor's accents, so the first
job is to discard everything that cannot change syllable weight while keeping
the three diacritics that can: the iota subscript, which marks a long vowel; a
macron or breve, where an editor has supplied the length outright; and the
diaeresis, which states that two vowels are *not* a diphthong and so changes
the syllable count.

Everything here is deliberately conservative. Where a decision belongs to the
metre rather than to the spelling - whether a dichronon is long, whether a stop
plus liquid closes the syllable before it - this module records the ambiguity
instead of resolving it, and `quantity` carries it forward.

One pass builds the Letters, so there is no index arithmetic to keep aligned
between "which vowels had a diaeresis" and "which letters survived".
"""

from __future__ import annotations

import unicodedata

YPOGEGRAMMENI = "ͅ"
MACRON = "̄"
BREVE = "̆"
DIAERESIS = "̈"
KEPT_MARKS = frozenset({YPOGEGRAMMENI, MACRON, BREVE, DIAERESIS})

VOWELS = frozenset("αεηιουω")

#: ε and ο are short wherever they stand; η and ω are long wherever they stand.
ALWAYS_SHORT = frozenset("εο")
ALWAYS_LONG = frozenset("ηω")
#: The dichrona: length is not recoverable from the spelling alone.
DICHRONA = frozenset("αιυ")

#: Vowel pairs forming a single heavy nucleus. υι is included; ωυ is
#: vanishingly rare in hexameter and is omitted rather than guessed at.
DIPHTHONGS = frozenset({"αι", "αυ", "ει", "ευ", "ηυ", "οι", "ου", "υι"})

CONSONANTS = frozenset("βγδζθκλμνξπρστφχψ")
#: ζ, ξ and ψ each stand for two consonants, so they always close what precedes.
DOUBLE_CONSONANTS = frozenset("ζξψ")
STOPS = frozenset("βγδκπτθφχ")
LIQUIDS = frozenset("λρ")


class Letter:
    """One sound, carrying the length information its spelling actually gives."""

    __slots__ = ("char", "marks", "word_final", "word_initial")

    def __init__(self, char: str) -> None:
        self.char = char
        self.marks = ""
        self.word_final = False
        self.word_initial = False

    @property
    def is_vowel(self) -> bool:
        return self.char in VOWELS

    @property
    def is_consonant(self) -> bool:
        return self.char in CONSONANTS

    @property
    def explicitly_long(self) -> bool:
        return YPOGEGRAMMENI in self.marks or MACRON in self.marks

    @property
    def explicitly_short(self) -> bool:
        return BREVE in self.marks

    @property
    def blocks_diphthong(self) -> bool:
        """A diaeresis on the second vowel means the pair is two syllables."""
        return DIAERESIS in self.marks

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"Letter({self.char!r}, marks={self.marks.encode('unicode_escape')!r})"


def letters(text: str) -> list[Letter]:
    """Split a line into Letters: Greek sounds only, in order.

    Elision is honoured where the text marks it. An apostrophe means a vowel
    was written away, so it is simply not there to be counted - nothing special
    is needed beyond dropping the punctuation. *Unwritten* synizesis is not
    handled, and the README says so.
    """
    out: list[Letter] = []
    at_word_start = True
    for ch in unicodedata.normalize("NFD", text.lower()):
        if unicodedata.combining(ch):
            if out and ch in KEPT_MARKS:
                out[-1].marks += ch
            continue
        if ch == "ς":
            ch = "σ"
        if ch in VOWELS or ch in CONSONANTS:
            letter = Letter(ch)
            letter.word_initial = at_word_start
            out.append(letter)
            at_word_start = False
        else:
            # Whitespace and punctuation end a word; an apostrophe marks
            # elision and does not, on its own, start a new one.
            if out and not ch.isspace() and ch not in "'’᾽":
                out[-1].word_final = True
            if ch.isspace() or ch in ".,;:!?·":
                if out:
                    out[-1].word_final = True
                at_word_start = True
    if out:
        out[-1].word_final = True
    return out


def is_diphthong(first: Letter, second: Letter) -> bool:
    """Whether two adjacent vowels form one heavy nucleus.

    A diaeresis on the second vowel, or an explicit length mark on the first,
    says the editor read them apart.
    """
    if not (first.is_vowel and second.is_vowel):
        return False
    if second.blocks_diphthong or first.explicitly_long or first.explicitly_short:
        return False
    return (first.char + second.char) in DIPHTHONGS
