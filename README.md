# whirligig

[![PyPI](https://img.shields.io/pypi/v/whirligig)](https://pypi.org/project/whirligig/)
[![Python versions](https://img.shields.io/pypi/pyversions/whirligig)](https://pypi.org/project/whirligig/)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue)](LICENSE)

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

| flag             | default | meaning                                        |
|------------------|---------|------------------------------------------------|
| `-r`, `--radius` | `10`    | radius of the wheel, in characters             |
| `-d`, `--delay`  | `0.1`   | seconds each frame is held; lower spins faster |

```bash
whirligig -d 0.3 Yes No Maybe        # milk the suspense
whirligig -r 6 -d 0.02 heads tails   # just flip the coin already
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

It takes the same two options as the CLI, and returns the label it landed on. The call blocks while the wheel animates; pass `delay=0` to skip straight to the result:

```python
result = whirligig.spin(["heads", "tails"], w_radius=6, delay=0)
```

## License

[MIT](LICENSE)