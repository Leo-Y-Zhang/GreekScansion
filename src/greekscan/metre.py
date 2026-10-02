"""The metre as a grammar, and scansion as a search for certificates.

Dactylic hexameter is six feet. The first five are a dactyl (- u u) or a
spondee (- -). The sixth has two syllables, the first heavy and the second
anceps - either weight is legal there. That is the whole grammar, and there are
only 32 foot patterns in it.

From that follows the idea the project rests on. A scansion needs no published
scansion to be checked against, because the metre is the check: a candidate
either satisfies the grammar at every position or it does not. When exactly one
reading of a line fits, the line has scanned itself, and that reading is a
certificate - no authority required.

A reading is a syllabification *and* a foot pattern, because the spelling does
not always fix the syllable count: two adjacent vowels may be run together by
synizesis. So the search runs over every reading the spelling allows. The
payoff is that when only one survives, the metre has decided not just the feet
but whether synizesis applied - and `Result.synizesis` says where.
"""

from __future__ import annotations

from itertools import product

from .quantity import EITHER, HEAVY, LIGHT, weights_for
from .syllable import Syllable, capped_sites, variants

DACTYL = (HEAVY, LIGHT, LIGHT)
SPONDEE = (HEAVY, HEAVY)
#: The sixth foot: heavy, then anceps. EITHER expresses the anceps exactly - it
#: accepts a syllable of either weight.
FINAL_FOOT = (HEAVY, EITHER)

MIN_SYLLABLES = 5 * len(SPONDEE) + len(FINAL_FOOT)  # 12, every foot a spondee
MAX_SYLLABLES = 5 * len(DACTYL) + len(FINAL_FOOT)  # 17, every foot a dactyl

_PATTERNS: list[tuple[tuple[str, ...], ...]] | None = None


def foot_patterns() -> list[tuple[tuple[str, ...], ...]]:
    """All 32 legal foot sequences, each a tuple of six feet."""
    global _PATTERNS
    if _PATTERNS is None:
        _PATTERNS = [
            tuple(list(feet) + [FINAL_FOOT]) for feet in product((DACTYL, SPONDEE), repeat=5)
        ]
    return _PATTERNS


def _compatible(observed: str, required: str) -> bool:
    """Whether an observed weight can fill a required slot.

    EITHER observed is an undecided syllable and fills anything; EITHER
    required is the final anceps and anything fills it.
    """
    return observed == EITHER or required == EITHER or observed == required


def scansions(line_weights: list[str]) -> list[tuple[tuple[str, ...], ...]]:
    """Every foot pattern consistent with one sequence of syllable weights."""
    found = []
    for pattern in foot_patterns():
        flat = [slot for foot in pattern for slot in foot]
        if len(flat) != len(line_weights):
            continue
        if all(_compatible(o, r) for o, r in zip(line_weights, flat)):
            found.append(pattern)
    return found


class Reading:
    """One complete account of a line: how it divides, and how it scans."""

    __slots__ = ("syllables", "weights", "pattern")

    def __init__(self, syllables: list[Syllable], line_weights: list[str], pattern) -> None:
        self.syllables = syllables
        self.weights = line_weights
        self.pattern = pattern

    @property
    def feet(self) -> str:
        return "".join("D" if foot == DACTYL else "S" for foot in self.pattern[:5]) + "|"

    @property
    def synizesis(self) -> list[str]:
        """The syllables in this reading that exist by synizesis."""
        return [s.text for s in self.syllables if s.synizesis]


class Result:
    """What the scanner concluded about one line, and why."""

    __slots__ = ("line", "readings", "plain_weights", "sites")

    def __init__(self, line: str, readings: list[Reading], plain_weights: list[str], sites: int) -> None:
        self.line = line
        self.readings = readings
        self.plain_weights = plain_weights
        self.sites = sites

    @property
    def candidates(self) -> list:
        return self.readings

    @property
    def weights(self) -> list[str]:
        """The unique reading's weights, or the plain reading's if not unique."""
        return self.readings[0].weights if self.unique else self.plain_weights

    @property
    def syllable_count(self) -> int:
        return len(self.weights)

    @property
    def unique(self) -> bool:
        return len(self.readings) == 1

    @property
    def ambiguous(self) -> bool:
        return len(self.readings) > 1

    @property
    def unscannable(self) -> bool:
        return not self.readings

    @property
    def verdict(self) -> str:
        if self.unique:
            return "unique"
        return "ambiguous" if self.ambiguous else "unscannable"

    @property
    def synizesis(self) -> list[str]:
        return self.readings[0].synizesis if self.unique else []

    @property
    def reason(self) -> str:
        """Why an unscannable line failed, as far as can be told cheaply."""
        if not self.unscannable:
            return ""
        plain = len(self.plain_weights)
        if plain < MIN_SYLLABLES:
            return f"only {plain} syllables; the shortest hexameter has {MIN_SYLLABLES}"
        if plain > MAX_SYLLABLES and plain - self.sites > MAX_SYLLABLES:
            return (
                f"{plain} syllables and only {self.sites} place(s) where vowels could run "
                f"together; the longest hexameter has {MAX_SYLLABLES}"
            )
        return "syllable count is possible but no foot pattern fits the weights"

    def feet(self) -> str:
        """The certificate as D and S, or empty when the line is not unique."""
        return self.readings[0].feet if self.unique else ""


#: How freely synizesis may be invoked.
#:
#: "never"   - the spelling is taken at face value. Lines needing synizesis are
#:             reported unscannable, which is the honest answer about *this*
#:             scanner rather than about the text.
#: "minimal" - the default, and what an editor does: prefer the plain reading,
#:             and run vowels together only where the metre leaves no choice,
#:             using as few merges as will work.
#: "always"  - every reading at once. Raises how many lines scan at all, and
#:             lowers how many scan uniquely; the README reports both.
SYNIZESIS_MODES = ("never", "minimal", "always")


def scan(line: str, synizesis: str = "minimal") -> Result:
    """Scan one line over the readings the chosen synizesis policy allows."""
    if synizesis not in SYNIZESIS_MODES:
        raise ValueError(f"synizesis must be one of {SYNIZESIS_MODES}, not {synizesis!r}")

    readings_by_merges: dict[int, list[Reading]] = {}
    plain_weights: list[str] = []
    for index, syllables in enumerate(variants(line)):
        merges = sum(1 for s in syllables if s.synizesis)
        if index == 0:
            plain_weights = weights_for(syllables)
        if synizesis == "never" and merges:
            continue
        line_weights = weights_for(syllables)
        for pattern in scansions(line_weights):
            readings_by_merges.setdefault(merges, []).append(
                Reading(syllables, line_weights, pattern)
            )

    if synizesis == "minimal" and readings_by_merges:
        # Take only the cheapest repair that works, so a line that scans
        # without synizesis is never made ambiguous by offering it one.
        fewest = min(readings_by_merges)
        readings = readings_by_merges[fewest]
    else:
        readings = [r for _, group in sorted(readings_by_merges.items()) for r in group]

    return Result(line, readings, plain_weights, capped_sites(line))


def scan_all(lines: list[str], synizesis: str = "minimal") -> list[Result]:
    return [scan(line, synizesis) for line in lines if line.strip()]
