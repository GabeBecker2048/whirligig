"""Tests for the spin() library API and the rendering engine.

Under pytest neither stdout nor stderr is a tty, so by the output contract the
animation is skipped -- which makes the whole contract testable headlessly.
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

def test_library_writes_nothing_to_the_callers_streams(capsys):
    # the label is returned, not printed: printing it is the CLI's job, so a
    # Python script that calls spin() under a pipe gets no surprise output
    result = whirligig.spin(LUNCH, delay=0)
    assert result in LUNCH
    out = capsys.readouterr()
    assert out.out == ""
    assert out.err == ""  # no tty anywhere: animation fully skipped


# --- input validation ---

def test_empty_list_raises():
    with pytest.raises(ValueError, match="non-empty"):
        whirligig.spin([])

@pytest.mark.parametrize("bad", ["two\nlines", "carriage\rreturn", "tab\tstop"])
def test_multiline_labels_raise(bad):
    with pytest.raises(ValueError, match="newline or tab"):
        whirligig.spin(["fine", bad])

@pytest.mark.parametrize("bad", ["", "   "])
def test_blank_labels_raise(bad):
    with pytest.raises(ValueError, match="empty or whitespace-only"):
        whirligig.spin(["fine", bad])

@pytest.mark.parametrize("bad", [1, 0, -5, 101, 10_000])
def test_radius_out_of_range_raises(bad):
    with pytest.raises(ValueError, match="radius must be between 2 and 100"):
        whirligig.spin(["a", "b"], radius=bad)

@pytest.mark.parametrize("ok", [2, 100])
def test_radius_bounds_are_inclusive(ok):
    assert whirligig.spin(["a", "b"], radius=ok, delay=0) in ("a", "b")

def test_negative_delay_raises():
    with pytest.raises(ValueError, match="delay must not be negative"):
        whirligig.spin(["a", "b"], delay=-0.1)

def test_zero_delay_is_allowed():
    assert whirligig.spin(["a", "b"], delay=0) in ("a", "b")


# --- public API surface ---

def test_version_attribute():
    from importlib.metadata import version
    assert whirligig.__version__ == version("whirligig")

def test_spin_has_a_docstring():
    assert "return the winner" in whirligig.spin.__doc__


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

def test_too_many_labels_for_any_radius_says_so():
    # more labels than even a MAX_RADIUS wheel can hold: no radius suggestion
    labels = [f"label{i:03d}" for i in range(600)]
    with pytest.raises(ValueError, match="fewer or shorter labels"):
        whirligig.spin(labels, delay=0)

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

COLORED = re.compile(r"(\x1b\[[0-9;]+m)([^\x1b]*)\x1b\[0m")


def colored_segments(frame: str) -> list[tuple[str, str]]:
    """(color code, text) for every colored run in a frame, wheel rows then result line."""
    return COLORED.findall(frame)


@pytest.mark.parametrize(
    "labels",
    [
        ["Pizza", "Pizza Hut", "Sushi", "Thai"],       # one label is a prefix of another
        ["Thai", "Thai Basil", "Pad Thai"],            # prefix and suffix
        ["a", "aa", "aaa", "b", "bb"],                 # nested substrings
    ],
)
def test_substring_labels_each_get_their_own_color(labels):
    wheel = Wheel(10, labels)
    for i, label in enumerate(labels):
        frame = spinner.render_frame(wheel, i)
        *rows, result = colored_segments(frame)
        # the wheel's colored runs are exactly one per label, each wrapping its own
        # text (plus the point marker) in that label's color -- no run contains a
        # neighbor's text, and no label text is left outside a colored run
        assert len(rows) == len(labels)
        for code, text in rows:
            owner = text.replace("*", "").strip()
            assert owner in labels
            assert code == wheel.color(labels.index(owner))
        assert sorted(text.replace("*", "").strip() for _, text in rows) == sorted(labels)
        assert result == (wheel.color(i), label)
        assert ANSI.sub("", frame).count(label) >= 1


def test_duplicate_labels_share_a_color_and_the_result_line_agrees():
    labels = ["Pizza", "Pizza", "Sushi"]
    wheel = Wheel(10, labels)
    assert wheel.color(0) == wheel.color(1) != wheel.color(2)
    for i in range(len(labels)):
        *rows, result = colored_segments(spinner.render_frame(wheel, i))
        pizza_codes = {code for code, text in rows if "Pizza" in text}
        assert pizza_codes == {wheel.color(0)}
        assert result == (wheel.color(i), labels[i])


def test_arm_is_never_colored():
    # the spinner arm shares the "*" glyph with the point markers; only the one
    # marker beside each label belongs to a colored run
    wheel = Wheel(10, LUNCH)
    for i in range(len(LUNCH)):
        *rows, _ = colored_segments(spinner.render_frame(wheel, i))
        assert all(text.count("*") == 1 for _, text in rows)


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

def test_zero_size_terminal_skips_the_check(monkeypatch):
    # a fresh pty (and some CI ttys) reports 0x0: that means "size unknown",
    # and must not be treated as a terminal too small for any wheel
    stream = FakeTty()
    monkeypatch.setattr(spinner, "animation_stream", lambda: stream)
    monkeypatch.setattr(os, "get_terminal_size", lambda fd=None: os.terminal_size((0, 0)))
    result = whirligig.spin(["a", "b"], radius=4, delay=0)
    assert result in ("a", "b")
    assert "\x1b[?1049h" in stream.getvalue()  # animation ran

def test_unsized_stream_skips_the_check(monkeypatch):
    # a tty-ish stream with no real fd behind it (IDE consoles, test harnesses):
    # the size check should be skipped, not crash
    stream = FakeTty()
    stream.fileno = lambda: (_ for _ in ()).throw(io.UnsupportedOperation("fileno"))
    monkeypatch.setattr(spinner, "animation_stream", lambda: stream)
    assert whirligig.spin(["a", "b"], radius=4, delay=0) in ("a", "b")
