# whirligig

[![PyPI](https://img.shields.io/pypi/v/whirligig)](https://pypi.org/project/whirligig/)
[![Python versions](https://img.shields.io/pypi/pyversions/whirligig)](https://pypi.org/project/whirligig/)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue)](LICENSE)
[![CI](https://github.com/GabeBecker2048/whirligig/actions/workflows/test.yml/badge.svg)](https://github.com/GabeBecker2048/whirligig/actions/workflows/test.yml)

Spin a colorful ASCII wheel of fortune in your terminal and let fate decide: what's for lunch, who reviews the PR, heads or tails.

![whirligig spinning a wheel of lunch options and landing on Burgers](https://raw.githubusercontent.com/GabeBecker2048/whirligig/refs/heads/main/demo/demo.gif)

## Try it

No install needed if you have [uv](https://docs.astral.sh/uv/) or [pipx](https://pipx.pypa.io/):

```bash
uvx whirligig Pizza Sushi Mexican Thai "Chicken Wings" Poke Burgers
```

## Install

```bash
pip install whirligig
```

Requires Python 3.10+, on Linux, macOS, or Windows 10+.

## CLI

Pass the choices as arguments; quote any that contain spaces.

```bash
whirligig Pizza Sushi Mexican Thai "Chicken Wings" Poke Burgers
```

Labels can repeat: each copy is its own slot on the wheel, so repeating a label is an easy way to weight the odds — `whirligig Pizza Pizza Sushi` lands on Pizza twice as often. All copies of the same label share one color, so they read as one choice spread across the wheel.

> **Known quirk:** wide characters — emoji, CJK — occupy two terminal columns where the wheel's geometry counts one, so a 🍕 label can bend the circle slightly. The spin works fine; the wheel just loses a little roundness.

| flag             | default | meaning                                        |
|------------------|---------|------------------------------------------------|
| `-r`, `--radius` | `10`    | radius of the wheel, in characters (2–100)     |
| `-d`, `--delay`  | `0.1`   | seconds each frame is held; lower spins faster |
| `-f`, `--file`   | —       | read labels from a file, one per line          |

```bash
whirligig -d 0.3 Yes No Maybe        # milk the suspense
whirligig -r 6 -d 0.02 heads tails   # just flip the coin already
```

A few wheels come ready-made — `coin`, `dice`, `clock`, and `alphabet` — and `random` spins one of them:

```bash
whirligig --preset dice
whirligig -p random          # surprise me
```

Keep a standing list in a file, one label per line, and spin it with `-f`. Blank lines are skipped:

```bash
whirligig -f lunch.txt
```

Piped input is read the same way, no flag needed (`-f -` also works):

```bash
grep -v alice teammates.txt | whirligig   # alice is on vacation
ls ~/Desktop | whirligig   # select a random file from your Desktop
```

### Scripting

The wheel is drawn on your terminal, but `stdout` is just the choice — so you can watch the spin and capture the answer at the same time:

```bash
LUNCH=$(whirligig Pizza Sushi Mexican Thai "Chicken Wings" Poke Burgers)
echo "ordering $LUNCH"
```

The captured value is the bare label, with no color codes and no animation frames. With no terminal at all (in CI, or under `whirligig ... &> file`) the animation is skipped and only the choice is printed.

## Python

`whirligig.spin` draws the same wheel:

```python
import whirligig

result = whirligig.spin(["Pizza", "Sushi", "Mexican", "Thai", "Chicken Wings", "Poke", "Burgers"])
```

It returns the label the wheel landed on, and takes the CLI's knobs as keyword arguments: `radius` (default `10`) is the wheel's size in characters, and `delay` (default `0.1`) is the seconds each frame is held. The call blocks while the wheel animates; pass `delay=0` to skip straight to the result:

```python
result = whirligig.spin(["heads", "tails"], radius=6, delay=0)
```

Bad input raises `ValueError`: blank or multi-line labels, more labels than the radius can hold (the error suggests one that fits), or a terminal too small for the wheel. Full details live in `help(whirligig.spin)`.

## License

[MIT](LICENSE)