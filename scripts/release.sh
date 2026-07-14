#!/usr/bin/env bash
# Build from the current checkout and publish it to PyPI.
# The PyPI token is read from .env (PYPI_TOKEN=...), which is gitignored
# and must never be committed.
set -euo pipefail

if [[ ! -f .env ]]; then
    echo "error: no .env file next to this script (expected it to contain PYPI_TOKEN=...)" >&2
    exit 1
fi

set -a
source ./.env
set +a

if [[ -z "${PYPI_TOKEN:-}" ]]; then
    echo "error: PYPI_TOKEN is not set in .env" >&2
    exit 1
fi

version=$(grep -E '^version *= *' pyproject.toml | head -1 | sed -E 's/version *= *"(.*)".*/\1/')
echo "building whirligig ${version} from $(git describe --tags --always --dirty 2>/dev/null || echo 'unknown checkout')..."

rm -rf dist
uv build

echo "publishing whirligig ${version} to PyPI..."
uv publish --token "$PYPI_TOKEN"

echo "done: https://pypi.org/project/whirligig/${version}/"
