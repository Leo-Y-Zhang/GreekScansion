# GreekScansion

[![tests](https://github.com/Leo-Y-Zhang/GreekScansion/actions/workflows/ci.yml/badge.svg)](https://github.com/Leo-Y-Zhang/GreekScansion/actions/workflows/ci.yml)
[![python](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/downloads/)
[![dependencies](https://img.shields.io/badge/dependencies-none-brightgreen)](pyproject.toml)
[![licence](https://img.shields.io/badge/licence-proprietary%20source--available-lightgrey)](LICENSE)

Scans Classical Greek dactylic hexameter, and reports **only what the metre
itself settles**.

The idea the program rests on is that a scansion does not need an authority to
be checked against. Hexameter is a strict grammar — six feet; the first five a
dactyl (`- u u`) or a spondee (`- -`); the sixth two syllables, heavy then
anceps — so there are exactly 32 possible foot patterns. A candidate reading
either satisfies that grammar at every position or it does not. When exactly
one reading of a line fits, **the line has scanned itself**, and that reading
is a certificate: no published scansion is required to confirm it.

So the program has three answers, and the interesting ones are not the first:

| verdict | meaning |
| --- | --- |
| `unique` | one reading fits. The metre decided; this is a certificate. |
| `ambiguous` | several readings fit. The spelling genuinely does not say which. |
| `unscannable` | no reading fits. Either the text needs something this scanner does not do, or a rule here is wrong. Both are findings. |

An `unscannable` line is never quietly given a reading, and an `ambiguous` line
is never quietly given its first one.

## What it knows, and what it refuses to guess

Syllable weight follows from the phonology: a syllable is heavy if its vowel is
long or a diphthong, or if a consonant closes it; light if a short vowel stands
open. The line is syllabified as one continuous string of sound, not word by
word, because Greek metre treats the verse as a phonological whole.

Three things are genuinely undecidable from the spelling. Each is carried
forward as "either", for the metre to resolve:

- **the dichrona.** α, ι and υ are written the same long or short. `ε`/`ο` are
  always short and `η`/`ω` always long, so those are decided.
- **stop plus liquid** (*muta cum liquida*). The cluster may close the syllable
  before it or belong wholly to the next onset, and Homer does both.
- **epic correption.** A long vowel ending a word before another vowel may
  shorten.

A fourth case is worse, because it changes the *number* of syllables:
**synizesis**, two adjacent vowels inside a word run together into one long
syllable. `Πηληϊάδεω` in *Iliad* 1.1 is the standard example — its `-εω` is one
syllable, and nothing in the spelling says so. The scanner therefore
syllabifies the line every way the spelling allows and searches over all of
them, under one of three policies:

- `never` — take the spelling at face value.
- `minimal` (default) — what an editor does: prefer the plain reading, and run
  vowels together only where the metre leaves no choice, using as few merges as
  will work.
- `always` — every reading at once.

The point of `minimal` is that it never spends a merge it does not need, so a
line that already scans is not made ambiguous by being offered one.

## The measurement

Three openings of Greek epic, in `corpus/sample.txt`. Recomputed by
`verify_all.py`, which CI runs, so this table cannot drift from the code:

<!-- MEASURED:BEGIN -->
| synizesis | lines | unique | ambiguous | unscannable |
| --- | --- | --- | --- | --- |
| `never` | 3 | 2 | 0 | 1 |
| `minimal` | 3 | 2 | 1 | 0 |
| `always` | 3 | 1 | 2 | 0 |
<!-- MEASURED:END -->

Read the trade-off across the rows, because it is the project's first real
result. Taking the spelling at face value, two of the three lines scan
themselves and *Iliad* 1.1 cannot be scanned at all. Allowing synizesis only
where it is forced rescues 1.1 — to two readings, not one — and costs the other
two lines nothing. Allowing it everywhere makes every line scannable and loses
a certificate: *Iliad* 1.2 drops from one reading to two.

That is the honest shape of the problem. Coverage and determinacy pull against
each other, and `minimal` is a defensible point between them rather than the
right answer.

## Using it

```bash
python -m greekscan corpus/sample.txt              # default: minimal
python -m greekscan corpus/sample.txt --synizesis never
python -m greekscan corpus/sample.txt --only unscannable
python -m greekscan -  < your-text.txt
```

Input is UTF-8, one verse line per line; `#` starts a comment. Output is ASCII
(`-` heavy, `u` light, `?` undecided) because a Windows console is cp1252 and
raises on Greek; `--greek` adds the text when the console can take it.

Accents, breathings and the diaeresis are read for what they tell the metre and
then discarded. The iota subscript is kept — it marks a long vowel. A macron or
breve is honoured where an editor supplied one. Written elision (`μυρί'`) is
handled, because the vowel is simply not there to count.

## What is not verified

- **No claim about any published scansion.** The tests are rules and synthetic
  lines; where the output is compared to anything, it is compared to the metre,
  not to an edition. The three corpus lines are quoted from memory of standard
  texts and should be checked against an edition before being relied on.
- **Unwritten synizesis is a search, not knowledge.** `minimal` is a policy,
  not a linguistic result.
- **Only dactylic hexameter.** No elegiac couplet, no lyric metres, no iambics.
- **No crasis across word boundaries**, no unwritten elision, no digamma. Any
  of those could turn an `unscannable` line into a scannable one.
- **The dichrona are never resolved by lexicon.** A dictionary of vowel lengths
  would collapse much of the ambiguity reported here; this scanner deliberately
  has none, so that every certificate rests on the metre alone.

## Testing

```bash
python -m pytest        # the suite
python verify_all.py    # the gate CI runs: re-derives the table above
```

The suite's load-bearing part is `TestTheCheckerActuallyChecks`, which corrupts
a correct weight sequence one position at a time and insists the scanner then
refuses it. A checker that accepts everything certifies nothing, so that test
is the one that makes the rest mean something. Position 16 is the exception and
is asserted to survive — the final syllable is anceps, so both weights are
legal there by design.

AI coding assistance was used in this repository and is disclosed wherever a
venue asks.
