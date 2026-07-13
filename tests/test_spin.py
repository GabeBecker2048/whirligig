"""Tests for the spin() library API and the rendering engine.

Under pytest neither stdout nor stderr is a tty, so by the output contract the
animation is skipped and the bare label lands on stdout -- which makes the
whole contract testable headlessly.
"""

import io
import os
import re

import pytest

import whirligig
from whirligig import spinner
from whirligig.spinner import Wheel, _smallest_fitting_radius

ANSI = re.compile(r"\x1b\[[0-9;]*[a-zA-Z]")

LUNCH = ["Pizza", "Sushi", "Mexican", "Thai", "Chicken Wings", "Poke", "Burgers"]


class FakeTty(io.StringIO):
    """A stream that claims to be a terminal, for exercising the animation path."""

    def isatty(self):
        return True

    def fileno(self):
        return 2


# --- the result contract ---

def test_returns_a_label():
    assert whirligig.spin(["heads", "tails"], delay=0) in ("heads", "tails")

def test_every_label_is_reachable():
    seen = {whirligig.spin(["a", "b", "c"], delay=0) for _ in range(100)}
    assert seen == {"a", "b", "c"}

def test_single_label_wins():
    assert whirligig.spin(["solo"], delay=0) == "solo"

def test_duplicate_labels_are_separate_slots():
    assert whirligig.spin(["dup", "dup"], delay=0) == "dup"

def test_redirected_stdout_gets_bare_label(capsys):
    result = whirligig.spin(LUNCH, delay=0)
    out = capsys.readouterr()
    assert out.out == result + "\n"
    assert "\x1b[" not in out.out  # no color codes in captured data
    assert out.err == ""  # no tty anywhere: animation fully skipped


# --- input validation ---

def test_empty_list_raises():
    with pytest.raises(ValueError, match="non-empty"):
        whirligig.spin([])

@pytest.mark.parametrize("bad", ["two\nlines", "carriage\rreturn", "tab\tstop"])
def test_multiline_labels_raise(bad):
    with pytest.raises(ValueError, match="newline or tab"):
        whirligig.spin(["fine", bad])


# --- overcrowding ---

def test_overcrowded_wheel_raises_with_radius_hint():
    labels = [f"item{i:02d}" for i in range(40)]
    with pytest.raises(ValueError, match=r"increase the radius to (\d+)") as e:
        whirligig.spin(labels, radius=10, delay=0)
    suggested = int(re.search(r"increase the radius to (\d+)", str(e.value)).group(1))
    assert Wheel(suggested, labels).fits()

def test_suggested_radius_is_minimal():
    labels = [f"item{i:02d}" for i in range(40)]
    fit = _smallest_fitting_radius(labels, 10)
    assert Wheel(fit, labels).fits()
    assert not Wheel(fit - 1, labels).fits()

@pytest.mark.parametrize(
    "labels",
    [
        ["heads", "tails"],
        [str(i + 1) for i in range(6)],  # dice
        [str((i + 2) % 12 + 1) for i in range(12)],  # clock
        [chr(c) for c in range(ord("a"), ord("z") + 1)],  # alphabet
        LUNCH,
    ],
)
def test_presets_and_demo_labels_fit_default_radius(labels):
    assert Wheel(10, labels).fits()


# --- rendering ---

def test_frame_contains_every_label_and_result_line():
    wheel = Wheel(10, LUNCH)
    frame = ANSI.sub("", spinner.render_frame(wheel, 3))
    for label in LUNCH:
        assert label in frame
    assert frame.splitlines()[-1] == f"You got {LUNCH[3]}!"

def test_frame_size_matches_rendered_frame():
    wheel = Wheel(10, LUNCH)
    cols, rows = wheel.frame_size()
    lines = ANSI.sub("", spinner.render_frame(wheel, 0)).splitlines()
    assert len(lines) == rows - 1  # frame_size reserves a row for the trailing newline
    assert all(len(line) == cols for line in lines[:-1])  # wheel rows are padded to width

def test_base_wheel_untouched_by_rendering():
    wheel = Wheel(6, ["a", "b", "c"])
    before = list(wheel.m)
    spinner.render_frame(wheel, 1)
    assert wheel.m == before


# --- terminal size pre-flight (animation path, via a fake tty) ---

def test_too_small_terminal_raises(monkeypatch):
    monkeypatch.setattr(spinner, "animation_stream", lambda: FakeTty())
    monkeypatch.setattr(os, "get_terminal_size", lambda fd=None: os.terminal_size((40, 12)))
    with pytest.raises(ValueError, match="terminal"):
        whirligig.spin(LUNCH, radius=10, delay=0)

def test_big_enough_terminal_animates(monkeypatch):
    stream = FakeTty()
    monkeypatch.setattr(spinner, "animation_stream", lambda: stream)
    monkeypatch.setattr(os, "get_terminal_size", lambda fd=None: os.terminal_size((300, 100)))
    result = whirligig.spin(LUNCH, radius=10, delay=0)
    frames = stream.getvalue()
    assert "\x1b[?1049h" in frames  # entered the alternate screen
    assert "You got" in frames
    assert ANSI.sub("", frames).rstrip().endswith(f"You got {result}!")

def test_unsized_stream_skips_the_check(monkeypatch):
    # a tty-ish stream with no real fd behind it (IDE consoles, test harnesses):
    # the size check should be skipped, not crash
    stream = FakeTty()
    stream.fileno = lambda: (_ for _ in ()).throw(io.UnsupportedOperation("fileno"))
    monkeypatch.setattr(spinner, "animation_stream", lambda: stream)
    assert whirligig.spin(["a", "b"], radius=4, delay=0) in ("a", "b")
