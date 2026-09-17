#!/usr/bin/env bash
# run-variance.sh <round-slug> <arm> <run-index>
# Same treatment as run-arm.sh, into a per-run directory, for the variance study.
set -uo pipefail
LAB="$(cd "$(dirname "$0")" && pwd)"
SLUG="${1:?slug}"; ARM="${2:?arm}"; IDX="${3:?run index}"
ARMDIR="$LAB/variance/$SLUG/run$IDX/arm-$ARM"
REPO="$ARMDIR/repo"
rm -rf "$ARMDIR"; mkdir -p "$REPO"
rsync -a --exclude '.gradle' --exclude '.kotlin' --exclude 'build' \
  /Users/mchiaradia/.claude/evals/golden-repo-spring/ "$REPO/"
mkdir -p "$REPO/docs/specifications/$SLUG"
cp "$LAB/specs/$SLUG/specification.md" "$REPO/docs/specifications/$SLUG/specification.md"
( cd "$REPO" && git init -q && git add -A && git commit -qm baseline )

PROMPT="/exptopology:arm-$ARM $SLUG"
echo "$PROMPT" > "$ARMDIR/prompt.txt"
cd "$REPO"
START=$(date +%s)
claude -p "$PROMPT" --plugin-dir "$LAB/plugin" \
  --allowedTools Read Write Edit Glob Grep Bash Agent Task Skill \
  --output-format stream-json --verbose \
  > "$ARMDIR/transcript.jsonl" 2> "$ARMDIR/stderr.log" < /dev/null
EXIT=$?
WALL=$(( $(date +%s) - START ))
python3 "$LAB/oracle/metrics2.py" "$ARMDIR/transcript.jsonl" --wall "$WALL" > "$ARMDIR/metrics.json"
TESTS=$(grep -rh '@Test' --include='*.kt' "$REPO/src/test" 2>/dev/null | wc -l | tr -d ' ')
echo "$TESTS" > "$ARMDIR/tests.count"
python3 - "$ARMDIR/metrics.json" "$ARM" "$IDX" "$TESTS" "$EXIT" <<'PY'
import json,sys
m=json.load(open(sys.argv[1]))
print(f"run{sys.argv[3]} arm={sys.argv[2]} exit={sys.argv[5]} cost=${m['total_cost_usd']:.2f} "
      f"wall={int(m['wall_seconds'])}s gradle={m['gradle_runs_total']} tests={sys.argv[4]}")
PY
