"""Synizesis: the one place the syllable count itself is in doubt.

Two adjacent vowels inside a word that are not a diphthong may be run together
into one long syllable. The spelling never marks it, so the scanner tries both
and lets the metre decide - and the policy for how freely it may do so is the
project's main experimental variable.
"""

from time import perf_counter

import pytest

from greekscan.metre import SYNIZESIS_MODES, scan
from greekscan.syllable import MAX_SYNIZESIS_SITES, capped_sites, syllabify, variants

# "δεω" is the classic case: Πηληϊάδεω scans with -εω as one syllable.
EPSILON_OMEGA = "δεω"


class TestSites:
    def test_a_non_diphthong_vowel_pair_inside_a_word_is_a_site(self):
        assert capped_sites(EPSILON_OMEGA) == 1

    def test_a_diphthong_is_not_a_site_because_it_is_already_one_nucleus(self):
        assert capped_sites("δει") == 0

    def test_a_consonant_between_the_vowels_rules_it_out(self):
        assert capped_sites("δετω") == 0

    def test_a_word_boundary_rules_it_out(self):
        # Across words this is crasis, which is a different phenomenon.
        assert capped_sites("δε ω") == 0


class TestVariants:
    def test_the_plain_reading_comes_first_and_merges_nothing(self):
        readings = variants(EPSILON_OMEGA)
        assert not any(s.synizesis for s in readings[0])

    def test_one_site_gives_exactly_two_readings(self):
        readings = variants(EPSILON_OMEGA)
        assert len(readings) == 2
        assert sum(1 for s in readings[1] if s.synizesis) == 1

    def test_a_merged_syllable_is_heavy(self):
        from greekscan.quantity import HEAVY, weight

        merged = [s for s in variants(EPSILON_OMEGA)[1] if s.synizesis][0]
        assert weight(merged) == HEAVY

    def test_merging_reduces_the_syllable_count_by_one(self):
        plain, merged = variants(EPSILON_OMEGA)
        assert len(merged) == len(plain) - 1

    def test_overlapping_sites_are_never_applied_together(self):
        # Three vowels in a row offer two sites, but merging the first
        # consumes the second, so no reading may claim both.
        for reading in variants("δεωα"):
            merged_positions = [i for i, s in enumerate(reading) if s.synizesis]
            assert all(b - a > 1 for a, b in zip(merged_positions, merged_positions[1:]))

    def test_the_plain_syllabification_matches_the_first_variant(self):
        assert [s.text for s in syllabify(EPSILON_OMEGA)] == [
            s.text for s in variants(EPSILON_OMEGA)[0]
        ]

    def test_more_than_six_sites_still_enumerates_every_subset(self):
        line = "τεωτεωτωωτωωτωωτωωτωω"
        assert capped_sites(line) == 7
        assert len(variants(line)) == 2 ** 7

    def test_the_sixteen_site_limit_is_inclusive(self):
        assert MAX_SYNIZESIS_SITES == 16
        line = "ω" * 17
        assert capped_sites(line) == 16
        # Non-overlapping subsets of 16 consecutive sites: Fibonacci(18).
        assert len(variants(line)) == 2584

    @pytest.mark.parametrize("sites", (17, 40))
    def test_above_the_limit_never_enumerates_subsets(self, sites, monkeypatch):
        def unexpected_enumeration(*args):
            pytest.fail("over-limit lines must not enumerate subsets")

        monkeypatch.setattr("greekscan.syllable.combinations", unexpected_enumeration)
        with pytest.raises(ValueError, match="too many synizesis sites"):
            variants("τεω" * sites)


class TestPolicy:
    @pytest.mark.parametrize("mode", SYNIZESIS_MODES)
    @pytest.mark.parametrize("sites", (17, 40))
    def test_above_the_limit_returns_incomplete_quickly(self, mode, sites, monkeypatch):
        def unexpected_enumeration(*args):
            pytest.fail("over-limit lines must not request variants")

        monkeypatch.setattr("greekscan.metre.variants", unexpected_enumeration)
        started = perf_counter()
        result = scan("τεω" * sites, mode)
        assert perf_counter() - started < 1.0
        assert result.sites == sites
        assert result.search_incomplete and result.verdict == "search incomplete"
        assert not result.unique and not result.ambiguous and not result.unscannable
        assert result.readings == [] and result.synizesis == [] and result.feet() == ""
        assert f"too many synizesis sites ({sites}; limit 16)" in result.reason

    @pytest.mark.parametrize("mode", ("minimal", "always"))
    def test_more_than_six_sites_can_scan_with_two_merges(self, mode):
        result = scan("τεωτεωτωωτωωτωωτωωτωω", mode)
        assert result.unique and result.feet() == "SSSSS|"
        assert result.synizesis == ["τεω", "τεω"]

    def test_an_unknown_mode_is_refused(self):
        with pytest.raises(ValueError):
            scan("τωτετε", synizesis="sometimes")

    def test_every_documented_mode_runs(self):
        for mode in SYNIZESIS_MODES:
            assert scan("τωτετε τωτετε τωτετε τωτετε τωτετε τωτε", mode).unique

    def test_minimal_does_not_make_a_clean_line_ambiguous(self):
        """The point of minimal: never spend a merge that is not needed."""
        line = "τωετε τωτετε τωτετε τωτετε τωτετε τωτε"
        plain = scan(line, "never")
        minimal = scan(line, "minimal")
        assert plain.unique
        assert minimal.unique and minimal.feet() == plain.feet()

    def test_always_offers_at_least_as_many_readings_as_minimal(self):
        line = "τωτεωτε τωτετε τωτετε τωτετε τωτετε τωτε"
        assert len(scan(line, "always").readings) >= len(scan(line, "minimal").readings)

    def test_never_offers_no_more_readings_than_minimal(self):
        line = "τωτεωτε τωτετε τωτετε τωτετε τωτετε τωτε"
        assert len(scan(line, "never").readings) <= len(scan(line, "minimal").readings)

    def test_synizesis_is_only_reported_for_a_unique_reading(self):
        result = scan("τωτετε τωτετε τωτετε τωτετε τωτετε τωτε", "minimal")
        assert result.unique and result.synizesis == []
