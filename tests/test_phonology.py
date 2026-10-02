"""Phonology: what the spelling says, syllable by syllable.

These test the half of the project that reads Greek. Every case is a rule that
can be stated without reference to any particular poem, so none of them depends
on quoting a text correctly.
"""

from greekscan.orthography import is_diphthong, letters
from greekscan.quantity import EITHER, HEAVY, LIGHT, weight, weights
from greekscan.syllable import syllabify


class TestLetters:
    def test_accents_and_breathings_are_discarded(self):
        assert [l.char for l in letters("μῆνιν")] == ["μ", "η", "ν", "ι", "ν"]

    def test_final_sigma_folds_to_sigma(self):
        assert [l.char for l in letters("ος")] == ["ο", "σ"]

    def test_punctuation_and_spaces_are_not_sounds(self):
        assert [l.char for l in letters("ω, ε.")] == ["ω", "ε"]

    def test_word_boundaries_are_recorded(self):
        seq = letters("τω τε")
        assert seq[1].char == "ω" and seq[1].word_final
        assert seq[2].char == "τ" and seq[2].word_initial

    def test_written_elision_removes_the_vowel_entirely(self):
        # An apostrophe means the vowel is not there to be counted.
        assert [l.char for l in letters("ἄλγε' ἔθηκε")][:4] == ["α", "λ", "γ", "ε"]

    def test_iota_subscript_survives_as_a_length_mark(self):
        (vowel,) = [l for l in letters("ᾳ") if l.is_vowel]
        assert vowel.explicitly_long


class TestDiphthongs:
    def test_a_real_diphthong_is_one_nucleus(self):
        seq = letters("οι")
        assert is_diphthong(seq[0], seq[1])

    def test_a_diaeresis_breaks_the_pair(self):
        seq = letters("οϊ")
        assert not is_diphthong(seq[0], seq[1])

    def test_a_pair_that_is_not_a_diphthong_stays_apart(self):
        seq = letters("ωε")
        assert not is_diphthong(seq[0], seq[1])


class TestSyllabification:
    def test_open_syllables_split_on_the_single_consonant(self):
        syllables = syllabify("τωτετε")
        assert len(syllables) == 3
        assert not any(s.closed for s in syllables)

    def test_two_consonants_close_the_syllable_before_them(self):
        syllables = syllabify("εστι")
        assert len(syllables) == 2
        assert syllables[0].closed and [l.char for l in syllables[0].coda] == ["σ"]

    def test_a_double_consonant_closes_on_its_own(self):
        syllables = syllabify("εζω")
        assert syllables[0].closed, "zeta is worth two consonants"

    def test_stop_plus_liquid_is_left_undecided(self):
        syllables = syllabify("επρω")
        assert syllables[0].optionally_closed

    def test_a_long_vowel_before_a_vowel_is_open_to_correption(self):
        syllables = syllabify("τω ετε")
        assert syllables[0].correptable

    def test_trailing_consonants_close_the_last_syllable(self):
        assert syllabify("τωτον")[-1].closed

    def test_a_line_with_no_vowels_yields_nothing_rather_than_raising(self):
        assert syllabify("στ") == []


class TestWeight:
    def test_short_vowel_standing_open_is_light(self):
        assert weight(syllabify("τε")[0]) == LIGHT

    def test_long_vowel_is_heavy(self):
        assert weight(syllabify("τω")[0]) == HEAVY

    def test_a_closed_syllable_is_heavy_whatever_its_vowel(self):
        assert weight(syllabify("εστι")[0]) == HEAVY

    def test_a_dichronon_standing_open_is_undecided(self):
        assert weight(syllabify("τα")[0]) == EITHER

    def test_a_diphthong_is_heavy(self):
        assert weight(syllabify("ται")[0]) == HEAVY

    def test_stop_plus_liquid_after_a_short_vowel_is_undecided(self):
        assert weight(syllabify("επρω")[0]) == EITHER

    def test_stop_plus_liquid_after_a_long_vowel_is_still_heavy(self):
        # The vowel is long, so the cluster cannot change the weight.
        assert weight(syllabify("ωπρω")[0]) == HEAVY

    def test_correption_makes_a_long_final_vowel_undecided(self):
        assert weights("τω ετε")[0] == EITHER
