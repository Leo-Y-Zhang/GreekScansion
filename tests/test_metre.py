"""The metre as a grammar, and the claim that it certifies its own scansions.

The synthetic lines here are built from two syllables whose weight is not in
doubt - τω is heavy, τε is light - so a failure is a fault in the scanner and
never an argument about a text. The last class is the one that matters: it
corrupts a correct weight sequence and insists the scanner then refuses it,
because a checker that accepts everything certifies nothing.
"""

import random

import pytest

from greekscan.metre import (
    DACTYL,
    MAX_SYLLABLES,
    MIN_SYLLABLES,
    SPONDEE,
    foot_patterns,
    scan,
    scansions,
)
from greekscan.quantity import EITHER, HEAVY, LIGHT

HEAVY_SYLLABLE = "τω"
LIGHT_SYLLABLE = "τε"


def synthetic(dactyls, final_anceps_heavy=False):
    """A line of made-up Greek with exactly the requested foot pattern.

    Each foot becomes its own word, so no consonant cluster forms across a
    boundary and every syllable stays open - which keeps every weight decided.
    """
    words = [
        HEAVY_SYLLABLE + (LIGHT_SYLLABLE * 2 if is_dactyl else HEAVY_SYLLABLE)
        for is_dactyl in dactyls
    ]
    words.append(HEAVY_SYLLABLE + (HEAVY_SYLLABLE if final_anceps_heavy else LIGHT_SYLLABLE))
    return " ".join(words)


class TestGrammar:
    def test_there_are_exactly_thirty_two_foot_patterns(self):
        assert len(foot_patterns()) == 32

    def test_the_first_five_feet_are_dactyls_or_spondees(self):
        for pattern in foot_patterns():
            assert len(pattern) == 6
            assert all(foot in (DACTYL, SPONDEE) for foot in pattern[:5])

    def test_the_syllable_bounds_are_twelve_and_seventeen(self):
        assert (MIN_SYLLABLES, MAX_SYLLABLES) == (12, 17)

    def test_length_alone_fixes_how_many_feet_are_dactyls(self):
        # total = 3d + 2(5 - d) + 2 = d + 12, so the length forces the count.
        for pattern in foot_patterns():
            length = sum(len(foot) for foot in pattern)
            dactyl_count = sum(1 for foot in pattern[:5] if foot == DACTYL)
            assert length == dactyl_count + 12


class TestScanning:
    def test_five_dactyls_scan_uniquely(self):
        result = scan(synthetic([True] * 5))
        assert result.syllable_count == 17
        assert result.unique and result.feet() == "DDDDD|"

    def test_five_spondees_scan_uniquely(self):
        result = scan(synthetic([False] * 5, final_anceps_heavy=True))
        assert result.syllable_count == 12
        assert result.unique and result.feet() == "SSSSS|"

    def test_a_mixed_line_scans_uniquely(self):
        result = scan(synthetic([True, False, True, False, True]))
        assert result.unique and result.feet() == "DSDSD|"

    def test_the_final_syllable_is_anceps_so_either_weight_scans(self):
        for final_heavy in (True, False):
            result = scan(synthetic([True] * 5, final_anceps_heavy=final_heavy))
            assert result.unique, "the final syllable may be heavy or light"
            assert result.feet() == "DDDDD|"

    def test_too_short_a_line_is_unscannable_and_says_why(self):
        result = scan(LIGHT_SYLLABLE + HEAVY_SYLLABLE)
        assert result.unscannable
        assert "syllables" in result.reason

    def test_an_all_undecided_line_of_fifteen_is_ambiguous(self):
        # Length forces three dactyls, but not which three: C(5,3) = 10.
        assert len(scansions([EITHER] * 15)) == 10

    def test_an_all_undecided_line_of_seventeen_is_still_unique(self):
        # Only five dactyls reach 17 syllables, so the length alone decides it.
        assert len(scansions([EITHER] * 17)) == 1

    def test_a_length_no_hexameter_can_have_is_refused(self):
        assert scansions([HEAVY] * 18) == []


class TestRoundTrip:
    @pytest.mark.parametrize("seed", range(40))
    def test_every_pattern_is_recovered_from_its_own_line(self, seed):
        rng = random.Random(seed)
        dactyls = [rng.random() < 0.5 for _ in range(5)]
        final_heavy = rng.random() < 0.5
        result = scan(synthetic(dactyls, final_heavy))
        expected = "".join("D" if d else "S" for d in dactyls) + "|"
        assert result.unique, f"{expected} did not scan uniquely"
        assert result.feet() == expected


class TestTheCheckerActuallyChecks:
    """A checker that accepts a corrupted line is not a checker."""

    @staticmethod
    def correct():
        return [HEAVY, LIGHT, LIGHT] * 5 + [HEAVY, LIGHT]

    def test_the_uncorrupted_sequence_is_accepted(self):
        assert len(scansions(self.correct())) == 1

    @pytest.mark.parametrize("position", range(17))
    def test_flipping_any_single_weight_is_caught(self, position):
        mutated = self.correct()
        mutated[position] = LIGHT if mutated[position] == HEAVY else HEAVY
        found = scansions(mutated)
        if position == 16:
            # The last syllable is the anceps: both weights are legal there,
            # so this is the one mutation that is *meant* to survive.
            assert len(found) == 1
        else:
            assert found == [], f"position {position} was corrupted and still scanned"

    def test_dropping_a_syllable_is_caught(self):
        # Sixteen syllables is a legal length (four dactyls), so the length is
        # not what rejects this - the weights are.
        shortened = self.correct()[:-1]
        assert len(shortened) == 16
        assert scansions(shortened) == []

    def test_an_empty_line_scans_to_nothing(self):
        assert scansions([]) == []
