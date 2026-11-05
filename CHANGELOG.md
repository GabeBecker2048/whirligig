# Changelog

All notable changes, newest first. Versions follow [semantic versioning](https://semver.org/).

## 1.0.0 — 2026-11-05

First stable release: the CLI flags, the `spin()` signature and the stdout contract are now covered by semantic versioning. One behavior change for Python callers: `spin()` no longer prints the winning label to stdout when stdout is redirected. It only returns it, and the `whirligig` command does the printing, so `$(whirligig ...)` captures exactly what it did before. Also fixed: labels that are substrings of each other (`Pizza`, `Pizza Hut`) no longer steal each other's color, and landing on a repeated label shows the same color on the result line as on the wheel. Releases are now published to PyPI and GitHub by CI from a pushed tag.

## 0.5.0 — 2026-07-13

The winning frame is now held on screen for a second before the animation view closes, so the result no longer vanishes the instant the wheel lands. `--delay 0` still skips straight to the result with no hold.

## 0.4.0 — 2026-07-13

Hardened for release: input validation everywhere (empty or blank labels, overcrowded wheels, radius out of its new 2–100 range, negative delays, too-small terminals — all clear errors now), piped stdin without needing `-f -`, a `--version` flag, `whirligig.__version__` and a typed/documented Python API, the `spin()` parameter `w_radius` renamed to `radius`, `--file` moved off the deprecated `argparse.FileType`, and a test suite with CI across all supported platforms and Python versions.

## 0.3.0 — 2026-07-12 (published 2026-07-13)

The `whirligig` CLI arrives: `--radius`/`--delay` flags, ready-made presets (`--preset coin/dice/clock/alphabet/random`), label files via `--file`, per-spin randomized label colors, guards against multi-line labels, and a tty-aware output contract that keeps stdout clean for scripting (`LUNCH=$(whirligig ...)`).

## 0.2.0 — 2026-07-10

Smoother animation: frames redraw in place instead of clearing the screen, eliminating flicker.

## 0.1.0 — 2026-07-10

Initial release: an animated ASCII wheel of fortune with the `spin()` Python API.