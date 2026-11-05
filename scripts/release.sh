#!/usr/bin/env bash
# Cut a release of the version in pyproject.toml: check everything, then push an
# annotated tag vX.Y.Z. GitHub Actions (.github/workflows/release.yml) does the
# rest: PyPI, then the GitHub release with the CHANGELOG entry as its notes. No
# tokens are needed here: PyPI trusts the workflow (trusted publishing).
#
# Before running: in a pull request, bump `version` in pyproject.toml, run
# `uv lock`, and add a "## X.Y.Z — YYYY-MM-DD" section to the top of
# CHANGELOG.md. Merge it, then run this from an up-to-date main.
#
#   ./scripts/release.sh              tag and push the version in pyproject.toml
#   ./scripts/release.sh --dry-run    run every check, print the notes, push nothing
set -euo pipefail
cd "$(dirname "$0")/.."

die()  { printf '\033[31merror:\033[0m %s\n' "$*" >&2; exit 1; }
note() { printf '\033[2m%s\033[0m\n' "$*"; }
step() { printf '\033[1m==>\033[0m %s\n' "$*"; }

dry_run=0
case "${1:-}" in
    "") ;;
    --dry-run) dry_run=1 ;;
    -h|--help) sed -n '2,12p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) die "unknown argument '$1' (the version comes from pyproject.toml; try --help)" ;;
esac

version=$(grep -E '^version *= *' pyproject.toml | head -1 | sed -E 's/version *= *"(.*)".*/\1/')
tag="v${version}"
notes=$(mktemp)
trap 'rm -f "$notes"' EXIT

# --- the same checks the workflow makes, but on your laptop ------------------
# Each of these would fail the run a minute after pushing. Failing here means
# there is no tag to delete and no red cross on the repo.
[[ "$(git branch --show-current)" == main ]] || die "not on main"
[[ -z "$(git status --porcelain --untracked-files=no)" ]] || die "uncommitted changes to tracked files; commit or stash first"
untracked="$(git ls-files --others --exclude-standard)"
[[ -z "$untracked" ]] || note "note: untracked files are not part of this release: $(echo "$untracked" | tr '\n' ' ')"

git fetch --quiet --tags origin
[[ "$(git rev-parse HEAD)" == "$(git rev-parse origin/main)" ]] || die "main isn't the same as origin/main (push or pull first)"
git rev-parse -q --verify "refs/tags/${tag}" >/dev/null && die "${tag} already exists locally"
[[ -z "$(git ls-remote --tags origin "refs/tags/${tag}")" ]] || die "${tag} already exists on origin"

# The release notes are the CHANGELOG section, so a missing one is a release
# with no notes. The dash after the version may be an em dash or a hyphen.
awk -v v="$version" '
    $0 ~ "^## " v "( |$)" {on=1; next}
    on && /^## / {exit}
    on {print}' CHANGELOG.md | sed -e '/./,$!d' > "$notes"
[[ -s "$notes" ]] || die "no '## ${version}' section in CHANGELOG.md"

uv lock --check >/dev/null 2>&1 || die "uv.lock is out of date (run uv lock)"

step "checking whirligig ${version}..."
uv run pytest -q

step "${tag} -> $(git rev-parse --short HEAD)  ($(git log -1 --format=%s | cut -c1-60))"
echo "--- release notes, from CHANGELOG.md ---"
cat "$notes"
echo "--- end ---"

if [[ "$dry_run" -eq 1 ]]; then
    note "dry run; would tag and push ${tag}"
    exit 0
fi

read -r -p "tag and release whirligig ${version}? [y/N] " ok
[[ "$ok" == [yY] ]] || die "cancelled"

# Annotated, and dated to the commit: GitHub derives a release's created_at from
# the tag and orders the releases page by it.
GIT_COMMITTER_DATE="$(git log -1 --format=%cI HEAD)" git tag -a "$tag" -m "whirligig ${version}"
git push origin "refs/tags/${tag}"

step "pushed ${tag}: the release builds at https://github.com/GabeBecker2048/whirligig/actions"
note "watch it: gh run watch \$(gh run list --workflow=release.yml --limit 1 --json databaseId --jq '.[0].databaseId')"
