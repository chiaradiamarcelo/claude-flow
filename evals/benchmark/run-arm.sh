#!/usr/bin/env bash
# Materialise one experimental arm, then score it.
#
#   ./run-arm.sh <arm-label>            # prepare the workspace and print the launch command
#   ./run-arm.sh <arm-label> --score    # after the pipeline has run: run the oracle + scorecard
#
# An arm MUST run in its own fresh Claude Code session, in its own workspace. It
# cannot be run from the session that is designing the experiment: the scorecard
# reads ~/.claude/projects/<workspace-slug>/<session>/subagents/, and an
# orchestrator carrying the experiment's own conversation is not the orchestrator
# whose cost we are trying to measure.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ARM="${1:?usage: run-arm.sh <arm-label> [--score]}"
MODE="${2:-prepare}"
RUNS="$HERE/runs"
WS="$RUNS/$ARM"

if [ "$MODE" != "--score" ]; then
  if [ -e "$WS" ]; then
    echo "refusing to overwrite existing arm workspace: $WS" >&2
    echo "an arm is a measurement; re-running one in place destroys its record." >&2
    exit 1
  fi

  mkdir -p "$WS"
  cp -R "$HERE/fixture/." "$WS/"
  rm -rf "$WS/build" "$WS/.gradle"
  mkdir -p "$WS/docs/specifications/bank-accounts"
  cp "$HERE/bank-accounts/specification.md" "$WS/docs/specifications/bank-accounts/"

  # The arm is a git repo so /run-pipeline's changed-file detection and the WIP
  # commit treatment behave as they do in a real project.
  git -C "$WS" init -q
  # Pin a neutral identity in the ARM's OWN config, not just on this one commit.
  # /run-pipeline commits after each green scenario, and those commits would
  # otherwise fall through to the machine's global user.email — which is a
  # personal/work identity that has no business in a throwaway measurement repo.
  git -C "$WS" config user.email eval@local
  git -C "$WS" config user.name  eval
  git -C "$WS" add -A
  git -C "$WS" commit -qm "arm $ARM: fixture + frozen spec"

  cat >"$WS/NOTES.md" <<EOF
# Arm: $ARM

Frozen spec: docs/specifications/bank-accounts/specification.md
Run \`/run-pipeline bank-accounts\` and nothing else. Do NOT run /intent-and-goal —
the spec is already approved and frozen; regenerating it would make this arm
incomparable to every other.
EOF

  echo "workspace ready: $WS"
  echo
  echo "launch the arm in a FRESH session:"
  echo "  cd $WS && claude"
  echo "  > /run-pipeline bank-accounts"
  exit 0
fi

# ---- scoring ----
OUT="$HERE/scorecards/$ARM"
mkdir -p "$OUT"

echo "== oracle: tests, coverage, mutation =="
( cd "$WS" && ./gradlew --init-script "$HERE/oracle/oracle.init.gradle.kts" \
    test jacocoTestReport pitest --no-daemon )

cp "$WS/build/reports/pitest/mutations.xml" "$OUT/$ARM.mutations.xml"

echo "== mutation (filtered) =="
python3 ~/.claude/tools/mutation/classify-survivors.py "$OUT" | tee "$OUT/mutation.txt"

echo "== CRAP =="
python3 ~/.claude/tools/mutation/crap.py \
  "$WS/build/reports/jacoco/test/jacocoTestReport.xml" | tee "$OUT/crap.txt"

echo "== DRY =="
npx --yes jscpd "$WS/src" --reporters json --output "$OUT/jscpd" \
    --min-tokens 50 --silent >/dev/null 2>&1 || true
if [ -f "$OUT/jscpd/jscpd-report.json" ]; then
  python3 ~/.claude/tools/mutation/dry.py "$OUT/jscpd/jscpd-report.json" | tee "$OUT/dry.txt"
else
  echo "jscpd produced no report" | tee "$OUT/dry.txt"
fi

echo "== cost + row-level scorecard =="
# Claude Code's project slug replaces both '/' and '.' with '-', so ~/.claude
# becomes '--claude'. Getting this wrong silently loses the whole cost side.
SLUG="$(echo "$WS" | sed 's|[/.]|-|g')"
SESSDIR="$(ls -dt "$HOME/.claude/projects/$SLUG"/*/subagents 2>/dev/null | head -1 || true)"
if [ -z "$SESSDIR" ]; then
  echo "no session transcripts found for $SLUG — was the arm run from $WS?" >&2
  exit 1
fi
python3 ~/.claude/evals/scorecard/extract_run.py "$SESSDIR" \
  --plans "$WS/docs/specifications/bank-accounts" \
  --label "$ARM" --scenarios 9 \
  --json "$OUT/scorecard.json" | tee "$OUT/scorecard.md"

echo
echo "scorecard written to $OUT"
