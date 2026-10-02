"""Cutting a line of verse into syllables - in every way the spelling allows.

The line is syllabified as one continuous string of sound, not word by word.
That is not a shortcut: Greek metre treats the verse as a phonological whole,
so a consonant ending one word closes the syllable before it exactly as a
word-internal consonant does.

Two things are genuinely undecidable from the spelling, and each is recorded
rather than resolved:

  * a stop followed by a liquid may be read as a cluster that closes the
    preceding syllable or as a single onset that leaves it open, and Homer does
    both. That syllable is marked `optionally_closed`.
  * two adjacent vowels inside a word that are not a diphthong may be run
    together into one long syllable - synizesis, as in Πηληϊάδεω, whose -εω is
    one syllable in Iliad 1.1. Since the spelling never marks it, the line is
    syllabified both ways and the metre is left to choose.

`syllabify` gives the plain reading; `variants` gives every reading. The second
is what the scanner uses, which is why it can report *where* synizesis happened
instead of being defeated by it.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from itertools import combinations

from .orthography import (
    DOUBLE_CONSONANTS,
    LIQUIDS,
    STOPS,
    Letter,
    is_diphthong,
    letters,
)

#: Beyond this many candidate sites, every subset is not enumerated; see
#: `variants`. Six sites is 64 readings, which is already generous for a line.
MAX_SYNIZESIS_SITES = 6


@dataclass
class Syllable:
    """One syllable: its vowel nucleus, and what closes it."""

    nucleus: list[Letter] = field(default_factory=list)
    onset: list[Letter] = field(default_factory=list)
    coda: list[Letter] = field(default_factory=list)
    optionally_closed: bool = False
    correptable: bool = False
    #: True when this syllable exists only because two vowels were run together.
    synizesis: bool = False

    @property
    def closed(self) -> bool:
        return bool(self.coda)

    @property
    def text(self) -> str:
        return "".join(l.char for l in self.onset + self.nucleus + self.coda)


def _consonant_weight(run: list[Letter]) -> int:
    """How many consonants a run is worth. ζ, ξ and ψ are each worth two."""
    return sum(2 if l.char in DOUBLE_CONSONANTS else 1 for l in run)


def _is_muta_cum_liquida(run: list[Letter]) -> bool:
    return (
        len(run) == 2
        and run[0].char in STOPS
        and run[1].char in LIQUIDS
        and run[0].char not in DOUBLE_CONSONANTS
    )


def _nuclei(seq: list[Letter]) -> list[tuple[int, int]]:
    """Vowel nuclei as half-open ranges, taking a diphthong as one nucleus."""
    found: list[tuple[int, int]] = []
    i = 0
    while i < len(seq):
        if seq[i].is_vowel:
            if i + 1 < len(seq) and seq[i + 1].is_vowel and is_diphthong(seq[i], seq[i + 1]):
                found.append((i, i + 2))
                i += 2
            else:
                found.append((i, i + 1))
                i += 1
        else:
            i += 1
    return found


def synizesis_sites(seq: list[Letter], nuclei: list[tuple[int, int]]) -> list[int]:
    """Indices k where nucleus k and k+1 could be run together.

    The pair must be adjacent with no consonant between them, inside one word,
    and not already a diphthong - which `_nuclei` would have joined already.
    """
    sites = []
    for k in range(len(nuclei) - 1):
        if nuclei[k][1] != nuclei[k + 1][0]:
            continue  # a consonant stands between them
        if seq[nuclei[k][1] - 1].word_final:
            continue  # across a word boundary this is crasis, not synizesis
        sites.append(k)
    return sites


def _build(seq: list[Letter], nuclei: list[tuple[int, int]], merged: frozenset[int]) -> list[Syllable]:
    """Assemble syllables from a chosen set of nuclei."""
    if not nuclei:
        return []

    syllables = [Syllable(nucleus=seq[a:b]) for a, b in nuclei]
    for index in merged:
        syllables[index].synizesis = True

    syllables[0].onset = seq[: nuclei[0][0]]

    for k in range(len(nuclei) - 1):
        run = seq[nuclei[k][1] : nuclei[k + 1][0]]
        weight = _consonant_weight(run)
        if weight == 0:
            if syllables[k].nucleus[-1].word_final:
                syllables[k].correptable = True
        elif weight == 1:
            syllables[k + 1].onset = list(run)
        elif _is_muta_cum_liquida(run):
            syllables[k].coda = [run[0]]
            syllables[k + 1].onset = [run[1]]
            syllables[k].optionally_closed = True
        else:
            syllables[k].coda = [run[0]]
            syllables[k + 1].onset = list(run[1:])

    syllables[-1].coda = seq[nuclei[-1][1] :]
    return syllables


def _merge(nuclei: list[tuple[int, int]], sites: tuple[int, ...]) -> tuple[list[tuple[int, int]], frozenset[int]]:
    """Run the chosen sites together, returning new nuclei and their indices."""
    if not sites:
        return list(nuclei), frozenset()
    drop = set(sites)
    out: list[tuple[int, int]] = []
    merged: set[int] = set()
    k = 0
    while k < len(nuclei):
        if k in drop and k + 1 < len(nuclei):
            out.append((nuclei[k][0], nuclei[k + 1][1]))
            merged.add(len(out) - 1)
            k += 2
        else:
            out.append(nuclei[k])
            k += 1
    return out, frozenset(merged)


def syllabify(line: str) -> list[Syllable]:
    """The plain reading: no synizesis applied."""
    seq = letters(line)
    return _build(seq, _nuclei(seq), frozenset())


def variants(line: str) -> list[list[Syllable]]:
    """Every reading of the line the spelling allows, plainest first.

    When there are more candidate synizesis sites than `MAX_SYNIZESIS_SITES`,
    only the plain reading and the single-site readings are produced. That is a
    deliberate cap, not an oversight: it is reported by `capped_sites`, and a
    line that needs more than six simultaneous synizeses is not a line this
    scanner should be claiming anything about.
    """
    seq = letters(line)
    base = _nuclei(seq)
    sites = synizesis_sites(seq, base)

    if len(sites) > MAX_SYNIZESIS_SITES:
        subsets: list[tuple[int, ...]] = [()] + [(s,) for s in sites]
    else:
        subsets = []
        for size in range(len(sites) + 1):
            subsets.extend(combinations(sites, size))

    readings = []
    seen: set[tuple] = set()
    for subset in subsets:
        # Overlapping sites cannot both apply: merging k consumes k+1.
        if any(b - a == 1 for a, b in zip(subset, subset[1:])):
            continue
        nuclei, merged = _merge(base, subset)
        key = tuple(nuclei)
        if key in seen:
            continue
        seen.add(key)
        readings.append(_build(seq, nuclei, merged))
    return readings


def capped_sites(line: str) -> int:
    """How many synizesis sites a line has, for reporting the cap honestly."""
    seq = letters(line)
    return len(synizesis_sites(seq, _nuclei(seq)))
