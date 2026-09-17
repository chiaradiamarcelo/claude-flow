#!/usr/bin/env bash
# run-arm.sh <round-slug> <arm: agents|inline>
# Dispatches one arm against its pristine repo and records transcript + metrics.
set -euo pipefail
LAB="$(cd "$(dirname "$0")" && pwd)"
SLUG="${1:?round slug}"; ARM="${2:?agents|inline}"
ARMDIR="$LAB/rounds/$SLUG/arm-$ARM"
REPO="$ARMDIR/repo"
[ -d "$REPO" ] || { echo "no repo at $REPO — run setup-arm.sh first" >&2; exit 1; }

PROMPT="/exptopology:arm-$ARM $SLUG"
echo "$PROMPT" > "$ARMDIR/prompt.txt"

cd "$REPO"
START=$(date +%s)
set +e
claude -p "$PROMPT" \
  --plugin-dir "$LAB/plugin" \
  --allowedTools Read Write Edit Glob Grep Bash Agent Task Skill \
  --output-format stream-json --verbose \
  > "$ARMDIR/transcript.jsonl" 2> "$ARMDIR/stderr.log" < /dev/null
EXIT=$?
set -e
WALL=$(( $(date +%s) - START ))
echo "arm=$ARM round=$SLUG exit=$EXIT wall=${WALL}s"
python3 "$LAB/oracle/metrics2.py" "$ARMDIR/transcript.jsonl" --wall "$WALL" > "$ARMDIR/metrics.json"
python3 - "$ARMDIR/metrics.json" <<'PY'
import json,sys
m=json.load(open(sys.argv[1]))
print(f"  cost=${m['total_cost_usd']:.2f}  gradle_runs={m['gradle_runs_total']}  "
      f"wall={m.get('wall_seconds')}s  subagents={m['subagents_dispatched']}")
PY
