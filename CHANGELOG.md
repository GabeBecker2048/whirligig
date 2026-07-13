# Changelog

## 0.4.0 — unreleased

Hardened for release: input validation everywhere (empty or blank labels, overcrowded wheels, too-small terminals — all clear errors now), piped stdin without needing `-f -`, a `--version` flag, `whirligig.__version__` and a typed/documented Python API, the `spin()` parameter `w_radius` renamed to `radius`, and a test suite with CI across all supported platforms and Python versions.

## 0.3.0 — 2026-07-12 (git only, never published)

The `whirligig` CLI arrives: `--radius`/`--delay` flags, ready-made presets (`--preset coin/dice/clock/alphabet/random`), label files via `--file`, per-spin randomized label colors, guards against multi-line labels, and a tty-aware output contract that keeps stdout clean for scripting (`LUNCH=$(whirligig ...)`).

## 0.2.0 — 2026-07-10

Smoother animation: frames redraw in place instead of clearing the screen, eliminating flicker.

## 0.1.0 — 2026-07-10

Initial release: an animated ASCII wheel of fortune with the `spin()` Python API.