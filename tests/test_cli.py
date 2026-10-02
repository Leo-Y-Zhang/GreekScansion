"""The command line, including the part that has to survive a cp1252 console."""

import pytest

from greekscan.cli import main
from tests.test_metre import synthetic


def write(tmp_path, lines):
    path = tmp_path / "verse.txt"
    path.write_text("\n".join(lines), encoding="utf-8")
    return str(path)


class TestCli:
    def test_it_reports_the_summary(self, tmp_path, capsys):
        path = write(tmp_path, [synthetic([True] * 5), synthetic([False] * 5, True)])
        assert main([path]) == 0
        out = capsys.readouterr().out
        assert "2 lines: 2 scanned uniquely" in out
        assert "100.0% pinned by the metre alone" in out

    def test_it_counts_an_unscannable_line_without_failing(self, tmp_path, capsys):
        path = write(tmp_path, [synthetic([True] * 5), "τετω"])
        assert main([path]) == 0
        assert "1 unscannable" in capsys.readouterr().out

    def test_comments_and_blank_lines_are_skipped(self, tmp_path, capsys):
        path = write(tmp_path, ["# a note", "", synthetic([True] * 5)])
        assert main([path]) == 0
        assert "1 lines: 1 scanned uniquely" in capsys.readouterr().out

    def test_only_filters_the_listing_but_not_the_summary(self, tmp_path, capsys):
        path = write(tmp_path, [synthetic([True] * 5), "τετω"])
        assert main([path, "--only", "unscannable"]) == 0
        out = capsys.readouterr().out
        assert "unscannable" in out and "unique" not in out.split("\n\n")[0]

    def test_quiet_prints_the_summary_alone(self, tmp_path, capsys):
        path = write(tmp_path, [synthetic([True] * 5)])
        assert main([path, "--quiet"]) == 0
        out = capsys.readouterr().out.strip()
        assert out.startswith("1 lines:")

    def test_an_empty_file_is_an_error(self, tmp_path):
        path = write(tmp_path, ["# nothing but a comment"])
        assert main([path]) == 2

    def test_feet_are_shown_for_a_unique_line(self, tmp_path, capsys):
        path = write(tmp_path, [synthetic([True, False, True, False, True])])
        assert main([path]) == 0
        assert "DSDSD|" in capsys.readouterr().out

    def test_greek_output_does_not_raise_on_a_narrow_console(self, tmp_path, capsys):
        # The CLI replaces unencodable characters rather than dying; this at
        # least proves the --greek path runs end to end.
        path = write(tmp_path, [synthetic([True] * 5)])
        assert main([path, "--greek"]) == 0
        assert "unique" in capsys.readouterr().out


class TestModuleEntryPoint:
    """`python -m greekscan` is documented, so it is tested.

    CI caught its absence once: the package had no __main__.py, so the
    invocation in the README failed while every in-process test passed.
    """

    def test_running_the_module_scans_the_sample_corpus(self):
        import os
        import pathlib
        import subprocess
        import sys

        root = pathlib.Path(__file__).resolve().parent.parent
        env = dict(os.environ, PYTHONPATH=str(root / "src"), PYTHONIOENCODING="utf-8")
        done = subprocess.run(
            [sys.executable, "-m", "greekscan", str(root / "corpus" / "sample.txt")],
            capture_output=True,
            text=True,
            env=env,
            cwd=root,
        )
        assert done.returncode == 0, done.stderr
        assert "scanned uniquely" in done.stdout
