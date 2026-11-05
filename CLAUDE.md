# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

whirligig — a fun wheel spinner for Python and CLI. It renders an ASCII wheel in the terminal, animates a spinner arm around it, and lands on a random label.

Packaged with `uv_build`; zero runtime dependencies; targets Python >=3.10 on Linux, macOS, and Windows 10+.

Support policy: nothing past EOL. Windows 10 is the floor because that's where conhost gained VT/ANSI support (which the `os.system('')` line in `animate()` switches on) — older consoles would print the escape codes as literal garbage, and we don't carry a `colorama` dependency to paper over it.

## Commands

```bash
uv sync                                 # create/refresh .venv from uv.lock
uv run whirligig Pizza Sushi Poke       # run the CLI
uv run whirligig -r 6 -d 0 heads tails  # small + zero-delay: the fastest way to eyeball a render change
uv run whirligig -p random              # spin a random preset (coin/dice/clock/alphabet)
uv run pytest                           # run the test suite
uv build                                # build sdist + wheel
```

Tests live in `tests/` and run headlessly: under pytest neither stdout nor stderr is a tty, so the output contract routes the bare label to stdout and skips the animation, which makes validation, exit codes, and the stdout contract all assertable. The animation path itself is exercised through a fake tty stream (see `FakeTty`). No linter or formatter is configured, and changes to the animation still need visual verification: run it and watch it.

## Architecture

The rendering engine is all of `src/whirligig/spinner.py`. `__init__.py` re-exports `spin` as the sole public Python API; `cli.py` is a thin `argparse` wrapper behind the `whirligig` entry point (also reachable as `python -m whirligig` via `__main__.py`), and it owns all CLI concerns — flag parsing, validation, exit codes, and the `PRESETS` dict — so that `spin()` stays a plain library function. Presets are deliberately CLI-only sugar: in Python, a list comprehension is the preset system.

The two interfaces are named differently on purpose: `whirligig` on the CLI (a `$PATH` name must be unique and brand-like — and `spin` is already taken by Scientific Python's dev tool), `spin()` in Python (namespaced by the package, so a verb reads better at the call site). Documented usage is `import whirligig` / `whirligig.spin([...])`, which keeps brand-then-verb consistent across both. Don't "fix" this by renaming either one or by adding a `whirligig = spin` alias.

**`Wheel`** is a mutable ASCII canvas, not a data model. `self.m` is a list of equal-length strings forming a `(2r+1) x (2r+1)` grid, indexed as `wheel[x, y]` via `__setitem__`/`__getitem__` (note the reversed order — `m[y][x]`). Labels are placed evenly around the circle by angle; `self.points[i]` is the grid coordinate of label `i`.

The render pipeline is a chain of `deepcopy`-and-return transforms so the base wheel is never mutated during animation:

`Wheel` → `draw_line(i)` (spinner arm from center to point `i`) → `add_labels()` (horizontally stretches the grid 3x, writes label text to the left or right of each point depending on which half of the circle it's in, then colorizes by string-replacing `" {label} *"` / `"* {label} "` patterns) → `str()` → `render_frame` appends the "You got X!" line.

Two consequences worth knowing before editing:
- `add_labels` colorizes by position: it records the span (text plus the point's `*` marker) of each label as it places it, then wraps those spans in escape codes right-to-left per row, since inserting codes shifts everything after them. Never colorize by searching rows for label text — that was the old approach, and labels that were substrings of each other (`Pizza`, `Pizza Hut`) stole each other's color. Coordinate math happens *before* the 3x stretch; an original column `x` lands at `pad + 3x`, marker at `pad + 3x + 1`.
- Label colors come from `wheel.colors`, a palette shuffled once in `Wheel.__init__` — random per spin, stable across the frames of one spin (deepcopy carries it). Color anything through `wheel.color(i)`, never `Colors.colors` or `wheel.colors[i]` directly: it keys the color by label text, so copies of a repeated label share one color and the result line always matches the wheel.
- The wheel is drawn to whichever stream `animation_stream()` picks — see the output contract below before adding any `print()`.

**Validation in `spin()`** happens before anything is drawn, in this order: labels must be a non-empty list of non-blank, single-line strings; radius must be within 2–`MAX_RADIUS` (100 — the O(r²) canvas makes big wheels a memory footgun) and delay non-negative (0 is legal and documented — don't add a floor); `Wheel.fits()` dry-runs label placement (`add_labels(strict=True)`) and refuses overcrowded wheels with a smallest-fitting-radius suggestion capped at `MAX_RADIUS` (checked even headless, so a command doesn't succeed in a pipeline but fail on a tty); and when there is an animation stream, `frame_size()` is compared against `os.get_terminal_size()` so an oversized frame raises instead of wrapping and ghosting (the failure mode behind the demo-GIF glitches).

**Terminal handling in `spin()`** is the fiddly part and is deliberately defensive. It enters the alternate screen buffer (`\033[?1049h`) with the cursor hidden, disables scroll-to-arrow-key reporting (`\033[?1007l`), and turns off tty `ECHO` via `termios` so mouse scrolls don't paint stray characters onto the wheel. All of that is restored in a `finally` (including a `tcflush` so buffered input doesn't leak into the shell prompt). `termios` is imported guardedly — it does not exist on Windows, where `os.system('')` is used instead to enable ANSI codes in the legacy console. Frames are drawn by jumping home (`\033[H`) and erasing to end-of-line (`\033[K`) per row rather than clearing the screen.

Since the alternate screen is discarded on exit, `spin()` reprints the final frame to the normal screen at the end — that's why the last frame appears twice in the code path.

## Output contract

`spin()` decides the winner up front (`random.randrange`) and returns the label; the animation is then played *to land on* that choice. `spin()` itself never prints the result — it is a library function and the caller's stdout is not its to write to — so the "stdout gets" column below is implemented in `cli.py`, after `spin()` returns. Where the animation bytes go is decided by `animation_stream()`:

| stdout | stderr | animation | stdout gets |
| --- | --- | --- | --- |
| tty | — | stdout | nothing (the frame already showed the result) |
| redirected | tty | stderr | the bare label |
| redirected | redirected | none | the bare label |

The rule behind the table: **the animation is a terminal effect, stdout is data.** stdout is only ever the chosen label, plain and uncolored, and only when it's redirected — which is exactly when someone is capturing it (`LUNCH=$(whirligig ...)`). Interactive output stays unduplicated. Anything that writes frames, ANSI escapes, or the "You got X!" line must go to the stream from `animation_stream()`, never to a bare `print()`, or it will corrupt the pipe.

There's deliberately no `--color` / `NO_COLOR` handling yet: color only reaches a tty by construction, so it isn't leaking anywhere. It'd become worth adding if someone wants `| less -R` to stay colorized.

## Releasing

`./scripts/release.sh X.Y.Z` is the whole release. It checks that the version matches `pyproject.toml`, that `CHANGELOG.md` has a `## X.Y.Z` section, that you are on `main` at the same commit as `origin/main` with a clean tree, that the tag is unused locally and on origin, and that `uv.lock` is current, then pushes an annotated tag `vX.Y.Z` without asking. `--dry-run` runs the checks and prints the notes without pushing. It runs no tests: CI ran them on the PR, and the release workflow runs them again. No tokens are involved. The script is identical in anchorless, chesssnake and whirligig; change all three together.

`.github/workflows/release.yml` fires on the tag and, in order: **checks** that the tag matches `pyproject.toml`, extracts the CHANGELOG section as the release notes, runs the suite, builds the sdist and wheel, runs `twine check`, and installs the wheel into a clean venv to run `whirligig --version` and a headless spin from it; **publishes to PyPI** through trusted publishing (the `pypi` environment); then **creates the GitHub release** last, with the notes and the built artifacts attached, so the release page only exists once PyPI has the version.

Per release, in a pull request: bump `version` in `pyproject.toml`, run `uv lock`, add a `## X.Y.Z — YYYY-MM-DD` section (a sentence or two) to the top of `CHANGELOG.md`. Merge, then run the script from an up-to-date `main`.

One-time PyPI setup (already done if a release has shipped this way): on <https://pypi.org/manage/project/whirligig/settings/publishing/> add a trusted publisher with owner `GabeBecker2048`, repository `whirligig`, workflow `release.yml`, environment `pypi`. The environment name must match the workflow's `environment: name: pypi`.

If it goes wrong: a tag/version mismatch or a failing test stops the run before anything is published, so delete the tag (`git push origin :refs/tags/vX.Y.Z`, `git tag -d vX.Y.Z`), fix, and rerun. PyPI never accepts a version twice, even after deletion, so a bad release that already uploaded gets yanked on PyPI and followed by the next patch version.
