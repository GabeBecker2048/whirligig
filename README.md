# whirligig

[![PyPI](https://img.shields.io/pypi/v/whirligig)](https://pypi.org/project/whirligig/)
[![Python versions](https://img.shields.io/pypi/pyversions/whirligig)](https://pypi.org/project/whirligig/)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue)](https://github.com/GabeBecker2048/whirligig/blob/main/LICENSE)
[![CI](https://github.com/GabeBecker2048/whirligig/actions/workflows/test.yml/badge.svg)](https://github.com/GabeBecker2048/whirligig/actions/workflows/test.yml)

![whirligig spinning a wheel of lunch options and landing on Burgers](https://raw.githubusercontent.com/GabeBecker2048/whirligig/main/demo/demo.gif)

<sub>Recorded from the real thing: `whirligig Pizza Sushi Tacos Thai "Chicken Wings" Poke Burgers`.</sub>

**Let the wheel decide.** whirligig spins a colorful ASCII wheel of fortune in
your terminal and lands on one of your choices: what's for lunch, who reviews
the PR, heads or tails. It's a CLI and a one-function Python library.

- A proper spin: the arm sweeps the wheel, slows down, and holds on the winner.
- Scripting-safe: the animation plays on your terminal, but stdout is only the
  chosen label, so `LUNCH=$(whirligig ...)` just works.
- Weight the odds by repeating a label; read labels from a file or a pipe; or
  spin a ready-made wheel (`coin`, `dice`, `clock`, `alphabet`).
- Zero dependencies. Python 3.10+ on Linux, macOS and Windows 10+.

## Try it

No install needed if you have [uv](https://docs.astral.sh/uv/) or
[pipx](https://pipx.pypa.io/):

```sh
uvx whirligig Pizza Sushi Tacos Thai "Chicken Wings" Poke Burgers
```

## Install

```sh
pip install whirligig    # or: uv tool install whirligig
```

Requires Python 3.10 or newer, on Linux, macOS or Windows 10+.

## CLI

Pass the choices as arguments, quoting any that contain spaces:

```sh
whirligig Pizza Sushi Tacos Thai "Chicken Wings" Poke Burgers
```

Labels can repeat, and each copy is its own slot on the wheel, so
`whirligig Pizza Pizza Sushi` lands on Pizza twice as often. Copies of a label
share one color, so they read as one choice spread across the wheel.

| flag             | default | meaning                                        |
|------------------|---------|------------------------------------------------|
| `-r`, `--radius` | `10`    | radius of the wheel, in characters (2–100)     |
| `-d`, `--delay`  | `0.1`   | seconds each frame is held; lower spins faster |
| `-f`, `--file`   | —       | read labels from a file, one per line          |
| `-p`, `--preset` | —       | `coin`, `dice`, `clock`, `alphabet` or `random` |

```sh
whirligig -d 0.3 Yes No Maybe               # milk the suspense
whirligig -r 6 -d 0.02 heads tails          # just flip the coin already
whirligig -p dice                           # a ready-made wheel
whirligig -p random                         # surprise me
whirligig -f lunch.txt                      # one label per line; blank lines are skipped
grep -v alice teammates.txt | whirligig     # piped input works too (alice is on vacation)
ls ~/Desktop | whirligig                    # a random file from your Desktop
```

### Scripting

The wheel is drawn on your terminal, but stdout is just the choice, so you can
watch the spin and capture the answer at the same time:

```sh
LUNCH=$(whirligig Pizza Sushi Tacos Thai "Chicken Wings" Poke Burgers)
echo "ordering $LUNCH"
```

The captured value is the bare label: no color codes, no animation frames. With
no terminal at all (in CI, or under `whirligig ... &> file`) the animation is
skipped and only the choice is printed.

## Python

`whirligig.spin` draws the same wheel and returns the label it lands on:

```python
import whirligig

result = whirligig.spin(["Pizza", "Sushi", "Tacos", "Thai", "Chicken Wings", "Poke", "Burgers"])
```

It takes the CLI's knobs as keyword arguments: `radius` (default `10`) and
`delay` (default `0.1`). The call blocks while the wheel animates; pass
`delay=0` to skip straight to the result:

```python
result = whirligig.spin(["heads", "tails"], radius=6, delay=0)
```

Bad input raises `ValueError`: blank or multi-line labels, more labels than the
radius can hold (the error suggests one that fits), or a terminal too small for
the wheel. Full details live in `help(whirligig.spin)`.

> **Known quirk:** wide characters (emoji, CJK) occupy two terminal columns
> where the wheel's geometry counts one, so a 🍕 label can bend the circle
> slightly. The spin works fine; the wheel just loses a little roundness.

## Contributing

Issues and pull requests are welcome. The project is managed with
[uv](https://docs.astral.sh/uv/):

```sh
uv sync                                  # create .venv from uv.lock
uv run pytest                            # the test suite
uv run whirligig -r 6 -d 0 heads tails   # the fastest way to eyeball a render change
```

CI runs the suite on Python 3.10 to 3.14 across Linux, macOS and Windows.
[CLAUDE.md](https://github.com/GabeBecker2048/whirligig/blob/main/CLAUDE.md)
explains how the code fits together, and
[CHANGELOG.md](https://github.com/GabeBecker2048/whirligig/blob/main/CHANGELOG.md)
what changed in each release.

## License

MIT, see [LICENSE](https://github.com/GabeBecker2048/whirligig/blob/main/LICENSE).
