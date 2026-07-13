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
uv run python -m whirligig.spinner      # run the demo in __main__ (random dice/clock/alphabet/coin wheel)
uv build                                # build sdist + wheel
```

There is no test suite, linter, or formatter configured. Verification is visual: run the animation and watch it.

## Architecture

The rendering engine is all of `src/whirligig/spinner.py`. `__init__.py` re-exports `spin` as the sole public Python API; `cli.py` is a thin `argparse` wrapper behind the `whirligig` entry point, and it owns all CLI concerns (flag parsing, validation, exit codes) so that `spin()` stays a plain library function.

The two interfaces are named differently on purpose: `whirligig` on the CLI (a `$PATH` name must be unique and brand-like — and `spin` is already taken by Scientific Python's dev tool), `spin()` in Python (namespaced by the package, so a verb reads better at the call site). Documented usage is `import whirligig` / `whirligig.spin([...])`, which keeps brand-then-verb consistent across both. Don't "fix" this by renaming either one or by adding a `whirligig = spin` alias.

**`Wheel`** is a mutable ASCII canvas, not a data model. `self.m` is a list of equal-length strings forming a `(2r+1) x (2r+1)` grid, indexed as `wheel[x, y]` via `__setitem__`/`__getitem__` (note the reversed order — `m[y][x]`). Labels are placed evenly around the circle by angle; `self.points[i]` is the grid coordinate of label `i`.

The render pipeline is a chain of `deepcopy`-and-return transforms so the base wheel is never mutated during animation:

`Wheel` → `draw_line(i)` (spinner arm from center to point `i`) → `add_labels()` (horizontally stretches the grid 3x, writes label text to the left or right of each point depending on which half of the circle it's in, then colorizes by string-replacing `" {label} *"` / `"* {label} "` patterns) → `str()` → `render_frame` appends the "You got X!" line.

Two consequences worth knowing before editing:
- `add_labels` colorizes via `str.replace` on rendered rows, so labels that are substrings of each other, or that contain the padding/`*` characters, can mis-colorize. Coordinate math happens *before* the 3x stretch; the `x * 2` terms in `add_labels` compensate for it.
- The wheel is drawn to whichever stream `animation_stream()` picks — see the output contract below before adding any `print()`.

**Terminal handling in `spin()`** is the fiddly part and is deliberately defensive. It enters the alternate screen buffer (`\033[?1049h`) with the cursor hidden, disables scroll-to-arrow-key reporting (`\033[?1007l`), and turns off tty `ECHO` via `termios` so mouse scrolls don't paint stray characters onto the wheel. All of that is restored in a `finally` (including a `tcflush` so buffered input doesn't leak into the shell prompt). `termios` is imported guardedly — it does not exist on Windows, where `os.system('')` is used instead to enable ANSI codes in the legacy console. Frames are drawn by jumping home (`\033[H`) and erasing to end-of-line (`\033[K`) per row rather than clearing the screen.

Since the alternate screen is discarded on exit, `spin()` reprints the final frame to the normal screen at the end — that's why the last frame appears twice in the code path.

## Output contract

`spin()` decides the winner up front (`random.randrange`) and returns the label; the animation is then played *to land on* that choice. Where the bytes go is decided by `animation_stream()`:

| stdout | stderr | animation | stdout gets |
| --- | --- | --- | --- |
| tty | — | stdout | nothing (the frame already showed the result) |
| redirected | tty | stderr | the bare label |
| redirected | redirected | none | the bare label |

The rule behind the table: **the animation is a terminal effect, stdout is data.** stdout is only ever the chosen label, plain and uncolored, and only when it's redirected — which is exactly when someone is capturing it (`LUNCH=$(whirligig ...)`). Interactive output stays unduplicated. Anything that writes frames, ANSI escapes, or the "You got X!" line must go to the stream from `animation_stream()`, never to a bare `print()`, or it will corrupt the pipe.

There's deliberately no `--color` / `NO_COLOR` handling yet: color only reaches a tty by construction, so it isn't leaking anywhere. It'd become worth adding if someone wants `| less -R` to stay colorized.
