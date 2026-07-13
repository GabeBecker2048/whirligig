"""Tests for the whirligig CLI: argument parsing, label sources, and exit codes."""

import io
import sys

import pytest

from whirligig import cli
from whirligig.cli import PRESETS, main


class FakeTtyStdin(io.StringIO):
    def isatty(self):
        return True


def run_ok(capsys, argv):
    """Run main(), assert success, and return the label printed to stdout."""
    assert main(argv) == 0
    return capsys.readouterr().out.strip()

def run_error(capsys, argv):
    """Run main(), assert a usage error (exit 2), and return the stderr text."""
    with pytest.raises(SystemExit) as e:
        main(argv)
    assert e.value.code == 2
    return capsys.readouterr().err


# --- label sources ---

def test_positional_labels(capsys):
    assert run_ok(capsys, ["-d", "0", "heads", "tails"]) in ("heads", "tails")

def test_preset(capsys):
    assert run_ok(capsys, ["-d", "0", "-p", "dice"]) in PRESETS["dice"]

def test_preset_random(capsys):
    everything = {label for labels in PRESETS.values() for label in labels}
    assert run_ok(capsys, ["-d", "0", "-p", "random"]) in everything

def test_file(capsys, tmp_path):
    f = tmp_path / "lunch.txt"
    f.write_text("pizza\n\nsushi\n")  # blank line is skipped
    assert run_ok(capsys, ["-d", "0", "-f", str(f)]) in ("pizza", "sushi")

def test_explicit_stdin(capsys, monkeypatch):
    monkeypatch.setattr(sys, "stdin", io.StringIO("red\ngreen\n"))
    assert run_ok(capsys, ["-d", "0", "-f", "-"]) in ("red", "green")

def test_implicit_piped_stdin(capsys, monkeypatch):
    monkeypatch.setattr(sys, "stdin", io.StringIO("red\ngreen\n"))
    assert run_ok(capsys, ["-d", "0"]) in ("red", "green")

def test_args_beat_piped_stdin(capsys, monkeypatch):
    monkeypatch.setattr(sys, "stdin", io.StringIO("ignored\n"))
    assert run_ok(capsys, ["-d", "0", "winner"]) == "winner"


# --- usage errors ---

def test_no_source_at_a_tty_errors_instead_of_blocking(capsys, monkeypatch):
    monkeypatch.setattr(sys, "stdin", FakeTtyStdin())
    assert "nothing to spin" in run_error(capsys, [])

def test_two_sources_conflict(capsys):
    assert "only one" in run_error(capsys, ["-p", "dice", "heads", "tails"])

def test_empty_file(capsys, tmp_path):
    f = tmp_path / "empty.txt"
    f.write_text("\n\n")
    assert "no labels" in run_error(capsys, ["-f", str(f)])

def test_radius_too_small(capsys):
    assert "radius" in run_error(capsys, ["-r", "1", "a", "b"])

def test_negative_delay(capsys):
    assert "delay" in run_error(capsys, ["-d", "-1", "a", "b"])

def test_unknown_preset(capsys):
    assert "invalid choice" in run_error(capsys, ["-p", "roulette"])

def test_overcrowded_labels_surface_as_usage_error(capsys):
    labels = [f"item{i:02d}" for i in range(40)]
    assert "increase the radius" in run_error(capsys, ["-d", "0", *labels])

def test_newline_label_surfaces_as_usage_error(capsys):
    assert "newline or tab" in run_error(capsys, ["-d", "0", "ok", "bad\nlabel"])


# --- --version ---

def test_version_flag(capsys):
    with pytest.raises(SystemExit) as e:
        main(["--version"])
    assert e.value.code == 0
    out = capsys.readouterr().out
    assert out.startswith("whirligig ")
    assert out.split()[1] == cli.__version__
