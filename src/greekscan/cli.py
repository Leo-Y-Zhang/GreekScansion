"""Command line: scan a file of verse and report what the metre settled.

Output is ASCII by default - heavy is `-`, light is `u`, undecided is `?` -
because a Windows console is cp1252 and will raise on Greek. Pass --greek to
print the text too, which works when the console is UTF-8.

The summary is the measurement the project reports: how many lines the metre
pinned to one reading, how many stayed ambiguous, and how many no legal
pattern fits. The last number is not hidden; it is the interesting one.
"""

from __future__ import annotations

import argparse
import sys

from .metre import SYNIZESIS_MODES, scan_all
from .quantity import render


def _read_lines(path: str) -> list[str]:
    if path == "-":
        data = sys.stdin.read()
    else:
        with open(path, encoding="utf-8") as handle:
            data = handle.read()
    return [l for l in (line.strip() for line in data.splitlines()) if l and not l.startswith("#")]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="greekscan",
        description="Scan Classical Greek dactylic hexameter and report what the metre settles.",
    )
    parser.add_argument("path", help="UTF-8 file of verse, one line per line; - for stdin")
    parser.add_argument("--greek", action="store_true", help="also print the Greek text")
    parser.add_argument("--only", choices=("unique", "ambiguous", "unscannable"),
                        help="print only lines with this verdict")
    parser.add_argument("--quiet", action="store_true", help="print the summary alone")
    parser.add_argument("--synizesis", choices=SYNIZESIS_MODES, default="minimal",
                        help="how freely two vowels may be run together (default: minimal)")
    args = parser.parse_args(argv)

    results = scan_all(_read_lines(args.path), args.synizesis)
    if not results:
        print("no verse found", file=sys.stderr)
        return 2

    counts = {"unique": 0, "ambiguous": 0, "unscannable": 0}
    for index, result in enumerate(results, start=1):
        counts[result.verdict] += 1
        if args.quiet or (args.only and result.verdict != args.only):
            continue
        detail = result.feet() if result.unique else result.reason or f"{len(result.candidates)} readings"
        if result.synizesis:
            detail += f"  [synizesis x{len(result.synizesis)}]"
        line = f"{index:>4}  {result.verdict:<11} {render(result.weights):<18} {detail}"
        if args.greek:
            line += "  " + result.line
        try:
            print(line)
        except UnicodeEncodeError:  # a cp1252 console met Greek
            print(line.encode("ascii", "replace").decode("ascii"))

    total = len(results)
    print(
        f"\n{total} lines: {counts['unique']} scanned uniquely, "
        f"{counts['ambiguous']} ambiguous, {counts['unscannable']} unscannable "
        f"({100.0 * counts['unique'] / total:.1f}% pinned by the metre alone, "
        f"synizesis={args.synizesis})"
    )
    # A non-zero exit would mean "this file is bad", which is not what an
    # ambiguous line means, so only an empty input is an error.
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
