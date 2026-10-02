"""The gate: re-derive every number the README quotes, and fail if it drifted.

The README carries a measured table. Numbers in prose go stale silently, so
this script recomputes them from the corpus and the code and compares. CI runs
it, which means a README that disagrees with the scanner is a build failure
rather than something a reader has to notice.

    python verify_all.py          # check
    python verify_all.py --write  # recompute and rewrite the table

Run --write only after looking at what changed: the table moving is either a
real improvement or a regression, and the diff is the evidence either way.
"""

from __future__ import annotations

import argparse
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent / "src"))

from greekscan import MAX_SYLLABLES, MIN_SYLLABLES, foot_patterns  # noqa: E402
from greekscan.metre import SYNIZESIS_MODES, scan_all  # noqa: E402

ROOT = pathlib.Path(__file__).parent
CORPUS = ROOT / "corpus" / "sample.txt"
README = ROOT / "README.md"
BEGIN = "<!-- MEASURED:BEGIN -->"
END = "<!-- MEASURED:END -->"


def corpus_lines() -> list[str]:
    text = CORPUS.read_text(encoding="utf-8")
    return [l for l in (line.strip() for line in text.splitlines()) if l and not l.startswith("#")]


def measure() -> list[tuple[str, int, int, int, int]]:
    lines = corpus_lines()
    rows = []
    for mode in SYNIZESIS_MODES:
        results = scan_all(lines, mode)
        rows.append(
            (
                mode,
                len(results),
                sum(1 for r in results if r.unique),
                sum(1 for r in results if r.ambiguous),
                sum(1 for r in results if r.unscannable),
            )
        )
    return rows


def table(rows) -> str:
    out = [
        "| synizesis | lines | unique | ambiguous | unscannable |",
        "| --- | --- | --- | --- | --- |",
    ]
    for mode, total, unique, ambiguous, unscannable in rows:
        out.append(f"| `{mode}` | {total} | {unique} | {ambiguous} | {unscannable} |")
    return "\n".join(out)


def parse_table(text: str) -> list[tuple[str, int, int, int, int]]:
    block = text.split(BEGIN)[1].split(END)[0]
    rows = []
    for line in block.splitlines():
        match = re.match(r"\|\s*`(\w+)`\s*\|\s*(\d+)\s*\|\s*(\d+)\s*\|\s*(\d+)\s*\|\s*(\d+)\s*\|", line.strip())
        if match:
            rows.append((match.group(1), *(int(match.group(i)) for i in range(2, 6))))
    return rows


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true", help="rewrite the README table")
    args = parser.parse_args()

    failures = []

    if len(foot_patterns()) != 32:
        failures.append(f"the grammar has {len(foot_patterns())} foot patterns, not 32")
    if (MIN_SYLLABLES, MAX_SYLLABLES) != (12, 17):
        failures.append(f"syllable bounds are {(MIN_SYLLABLES, MAX_SYLLABLES)}, not (12, 17)")

    measured = measure()
    text = README.read_text(encoding="utf-8")

    if args.write:
        head, rest = text.split(BEGIN)
        _, tail = rest.split(END)
        README.write_text(f"{head}{BEGIN}\n{table(measured)}\n{END}{tail}", encoding="utf-8")
        print("README table rewritten:")
        print(table(measured))
        return 0

    if BEGIN not in text or END not in text:
        failures.append("README has no MEASURED block to check against")
    else:
        documented = parse_table(text)
        if documented != measured:
            failures.append(
                "README table disagrees with the scanner.\n  README:   "
                + "; ".join(map(str, documented))
                + "\n  measured: "
                + "; ".join(map(str, measured))
            )

    for row in measured:
        if row[1] == 0:
            failures.append(f"mode {row[0]}: the corpus produced no results at all")

    if failures:
        print("VERIFY FAILED")
        for failure in failures:
            print("  - " + failure)
        return 1

    print("VERIFY OK")
    print(f"  {len(foot_patterns())} foot patterns, {MIN_SYLLABLES}-{MAX_SYLLABLES} syllables")
    for mode, total, unique, ambiguous, unscannable in measured:
        print(f"  {mode:<8} {total} lines -> {unique} unique, {ambiguous} ambiguous, {unscannable} unscannable")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
