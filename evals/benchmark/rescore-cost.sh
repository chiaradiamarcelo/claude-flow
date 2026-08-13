#!/usr/bin/env bash
# Re-derive the COST side of every arm on record, without re-running the oracle.
#
# Mutation/CRAP/DRY are properties of the produced code and do not change when
# the transcript extractor changes; they stay as scored. This script exists
# because extract_run.py was summing `usage` per assistant log event instead of
# per API request, which inflated cache-read 1.76x and made "turns" a count of
# log lines. Every arm's cost numbers had to be recomputed from the same
# transcripts.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

for WS in "$HERE"/runs/*/; do
  ARM="$(basename "$WS")"
  OUT="$HERE/scorecards/$ARM"
  [ -d "$OUT" ] || continue

  SLUG="$(echo "${WS%/}" | sed 's|[/.]|-|g')"
  SESSDIR="$(ls -dt "$HOME/.claude/projects/$SLUG"/*/subagents 2>/dev/null | head -1 || true)"
  if [ -z "$SESSDIR" ]; then
    echo "!! $ARM: no session transcripts under $SLUG — skipped" >&2
    continue
  fi

  # The layered arms wrote DESIGN.md / LAYER-*.md to the repo root rather than
  # the spec folder, so their plan dir differs. Pick whichever holds the plans.
  PLANS="${WS}docs/specifications/bank-accounts"
  if ! ls "$PLANS"/SCENARIO-*.md >/dev/null 2>&1 && ls "${WS}"LAYER-*.md >/dev/null 2>&1; then
    PLANS="${WS%/}"
  fi

  echo "== $ARM (plans: ${PLANS#$HERE/}) =="
  python3 "$HOME/.claude/evals/scorecard/extract_run.py" "$SESSDIR" \
    --plans "$PLANS" --label "$ARM" --scenarios 9 \
    --json "$OUT/scorecard.json" > "$OUT/scorecard.md"
  head -6 "$OUT/scorecard.md" | tail -5
  echo
done
