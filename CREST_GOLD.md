# CREST Gold project design

**The question.** *Where does the ambiguity in Greek hexameter actually lie —
and how much of a line can the metre decide on its own, with no lexicon and no
published scansion to consult?*

That is a real question with a measurable answer, and the answer is not known
in advance. It is also the kind of question a computer settles better than a
reader: a human scanning a line resolves the dichrona from knowing the words,
which is exactly the knowledge that has to be withheld to find out what the
metre alone can do.

## Why it is worth asking

Scansion is normally taught as something you do *to* a line with a dictionary
beside you. But hexameter is a strict grammar, and a grammar constrains. Strip
out every piece of lexical knowledge, feed in only what the spelling records,
and some lines still collapse to exactly one legal reading — those lines have
scanned themselves. Others do not. Which lines fall into which class, and
*why*, is the result.

The practical payoff is the inverse reading. When one reading survives, the
metre has decided every undecided syllable in the line: it has told you the
length of each dichronon, whether a stop-plus-liquid cluster closed its
syllable, and whether two vowels ran together. The scanner becomes a way of
*extracting* phonological facts from the metre rather than feeding them in.

## Method

The instrument is this repository, and it already works: 120 tests, a gate that
re-derives the README's figures, no dependencies. The project is the study, not
the plumbing — which is what keeps 70 hours going into findings.

1. **Assemble a corpus** of hexameter from public-domain editions, large enough
   to say something (target: several thousand lines across Homer, Hesiod and
   the Homeric Hymns), with its provenance recorded line by line.
2. **Pre-register** the hypotheses and thresholds below, before running on the
   full corpus. Writing down what would count as a disappointing result is what
   stops the analysis being tuned until it looks good.
3. **Measure** the three-way split — unique, ambiguous, unscannable — under
   each synizesis policy.
4. **Explain the tail.** Every unscannable line is a bug report against either
   the rules or the text. Classify them: digamma, unwritten elision, crasis,
   proper nouns, corrupt lines, or a genuine error here. The classification is
   a finding in its own right.
5. **Invert it.** For the uniquely-scanning lines, extract what the metre
   decided about each dichronon, and check the extracted lengths against each
   other. A vowel the metre calls long in one line and short in another is
   either a real quantity alternation or an error — both worth reporting.
6. **Write it up** with every number re-derived by the gate rather than typed.

### Pre-registered expectations

Recorded now so the result cannot be fitted to them afterwards.

| Prediction | Threshold that would count as confirmed |
| --- | --- |
| Most lines do **not** self-certify | fewer than 50% `unique` under `minimal` |
| `minimal` beats `never` on coverage | `unscannable` at least halved |
| `always` costs certificates | `unique` strictly lower than under `minimal` |
| The unscannable tail has few causes | 80% of failures fall into ≤5 classes |
| Metre-extracted vowel lengths are self-consistent | under 5% of dichrona get contradictory verdicts |

A result that contradicts any row is more interesting than one that confirms
it, and will be reported as it stands.

## How the work divides between two students

CREST assesses each student's own contribution, so the split has to be real,
not a label on shared work. These two halves meet at one interface — the
sequence of syllable weights — and each can be judged alone.

**Student A — the phonology and the engine.**
Owns `orthography.py`, `syllable.py`, `quantity.py`: reading Greek as sound,
syllabifying the line, deciding weight and, more importantly, deciding what
*cannot* be decided. Owns the synizesis search and the policies. Their case is
made by the rule-level tests and by the classification of the unscannable tail
— every class of failure is a question about the phonology.

**Student B — the metre, the measurement and the analysis.**
Owns `metre.py`, the corpus and its provenance, the pre-registration, the
statistics and the inversion step. Their case is made by the grammar tests, by
`TestTheCheckerActuallyChecks` (which deliberately corrupts correct input to
prove the checker discriminates), by `verify_all.py`, and by the write-up.

Both students keep their own log of hypotheses, dead ends and decisions. The
dead ends matter: CREST Gold asks for evidence of a *process*, and a project
with no abandoned approach in it does not look like research.

## Rough shape of 70 hours each

| | A | B |
| --- | --- | --- |
| Reading round the problem; metre and phonology from the grammars | 10 | 8 |
| Corpus assembly and provenance | 4 | 12 |
| Engine work: rules, synizesis, edge cases | 22 | 4 |
| Tests, including the adversarial ones | 10 | 10 |
| Pre-registration and statistics | 3 | 14 |
| Classifying the unscannable tail | 12 | 6 |
| Write-up, figures, peer review | 9 | 16 |

## What has to happen before any of it counts

- **A mentor.** Gold expects a professional or academic supervisor, and that is
  the critical path: get a written yes early. A classicist and a computer
  scientist are both plausible, and a classicist is the harder ask.
- **Pay before assessment.** CREST has no submission deadline — it is rolling —
  but the fee must have cleared before assessment begins, and assessment then
  takes 2–6 weeks. As of 2 October 2026 the UK Gold fee is £30 + VAT, about £36
  per student.
- **Disclose the AI assistance.** It is disclosed in the README and must be
  disclosed in the entry. CREST wants student-led work, and "we built the
  instrument and then designed and ran the study" is exactly that — but the
  claim has to be true, so the log of decisions is what backs it.

## Destination

A public repository and a short write-up reporting, for a few thousand lines of
hexameter, how much of the metre decides itself — with the unscannable tail
classified rather than discarded.

That one sentence is the test of whether the project is worth the hours. If the
write-up cannot be stated in it, the scope is wrong.
