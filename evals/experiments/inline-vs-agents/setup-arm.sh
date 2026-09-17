#!/usr/bin/env bash
# setup-arm.sh <round-slug> <arm: agents|inline>
# Builds a pristine arm repo: golden-repo-spring + that round's specification, nothing else.
set -euo pipefail
LAB="$(cd "$(dirname "$0")" && pwd)"
SLUG="${1:?round slug}"; ARM="${2:?agents|inline}"
DEST="$LAB/rounds/$SLUG/arm-$ARM/repo"
rm -rf "$DEST"; mkdir -p "$DEST"
# copy the golden repo, excluding build caches so both arms start identical and cold-ish
rsync -a --exclude '.gradle' --exclude '.kotlin' --exclude 'build' \
  /Users/mchiaradia/.claude/evals/golden-repo-spring/ "$DEST/"
mkdir -p "$DEST/docs/specifications/$SLUG"
cp "$LAB/specs/$SLUG/specification.md" "$DEST/docs/specifications/$SLUG/specification.md"
( cd "$DEST" && git init -q && git add -A && git commit -qm "baseline: golden-repo-spring + $SLUG specification" )
echo "$DEST"
