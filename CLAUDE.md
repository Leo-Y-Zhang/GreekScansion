# GreekScansion — notes for a coding session

Scans Classical Greek dactylic hexameter. The design rule that everything else
follows from: **report only what the metre settles.** Three verdicts — `unique`
(one legal reading, which is a certificate), `ambiguous` (several), and
`unscannable` (none, which is a finding, not a failure). Never resolve an
ambiguity by picking the first reading.

## Layout

```
src/greekscan/orthography.py   Greek as sound: what the spelling does and does not record
src/greekscan/syllable.py      syllabification, including every reading synizesis allows
src/greekscan/quantity.py      syllable weight: HEAVY, LIGHT, or EITHER
src/greekscan/metre.py         the 32-pattern grammar and the search over readings
src/greekscan/cli.py           CLI; ASCII output, because a Windows console is cp1252
verify_all.py                  the gate: re-derives the README's table
corpus/sample.txt              three epic openings
CREST_GOLD.md                  the research design this repository is the instrument for
```

## Running it

```bash
python -m pytest        # 120 tests, no dependencies beyond pytest
python verify_all.py    # the gate; --write rewrites the README table
PYTHONPATH=src python -m greekscan corpus/sample.txt
```

## Things that will bite

- **`EITHER` is load-bearing.** A dichronon standing open, a stop-plus-liquid
  cluster, and a correptable long final vowel are all genuinely undecidable
  from the spelling. Resolving one of them with a guess would make the
  certificates meaningless.
- **Synizesis changes the syllable *count*,** so a line has several
  syllabifications, not one. `variants()` returns them; `scan()` searches them
  under a policy (`never` / `minimal` / `always`). `minimal` must never spend a
  merge the metre does not force — that invariant has a test.
- **Read files with `encoding="utf-8"` explicitly.** The Windows default is
  cp1252 and will mangle or raise on Greek. Printing Greek is guarded in the
  CLI for the same reason.
- **Do not add a vowel-length lexicon.** It would collapse most of the
  ambiguity this project exists to measure. If one is ever wanted, it belongs
  behind a flag that is off by default, and the README must report both numbers.
- **`TestTheCheckerActuallyChecks` is the test that matters.** It corrupts a
  correct weight sequence one position at a time and insists the scanner then
  refuses it. Position 16 is asserted to *survive*, because the final syllable
  is anceps. If a change makes that class pass trivially, the change is wrong.
- **The README's table is gated.** Change the rules and `verify_all.py` fails
  until the table is rewritten — look at the diff before running `--write`,
  because the table moving is either a real improvement or a regression.
