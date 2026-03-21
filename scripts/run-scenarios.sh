#!/usr/bin/env bash
# Runs all pending BDD scenarios from a SoT specification file, one at a time.
# Each scenario gets a fresh Claude context. Claude plans, implements, tests, and marks done.
#
# Usage:
#   ./scripts/run-scenarios.sh [path/to/specifications/feature-slug]
#
# If no argument is given, auto-discovers the single specification folder in docs/specifications/.

set -euo pipefail

RETRY_WAIT=300   # seconds to wait after a rate-limit / spending-limit error

# --- Resolve specification folder ---
SPEC_DIR="${1:-}"

if [[ -z "$SPEC_DIR" ]]; then
  DIRS=(); while IFS= read -r d; do DIRS+=("$d"); done < <(find docs/specifications -mindepth 1 -maxdepth 1 -type d 2>/dev/null || true)
  if [[ ${#DIRS[@]} -eq 1 ]]; then
    SPEC_DIR="${DIRS[0]}"
  elif [[ ${#DIRS[@]} -eq 0 ]]; then
    echo "ERROR: No specification folders found in docs/specifications/." >&2
    echo "Run /intent-and-goal first." >&2
    exit 1
  else
    echo "ERROR: Multiple specification folders found. Specify one:" >&2
    printf '  %s\n' "${DIRS[@]}" >&2
    exit 1
  fi
fi

SOT_FILE="${SPEC_DIR}/specification.md"

if [[ ! -f "$SOT_FILE" ]]; then
  echo "ERROR: Specification file not found: $SOT_FILE" >&2
  exit 1
fi

# --- Setup ---
LOG_DIR="logs/scenarios"
mkdir -p "$LOG_DIR"

echo "Specification: $SPEC_DIR"
echo "SoT: $SOT_FILE"
echo ""

# --- Loop ---
while true; do
  # Find next unchecked scenario
  NEXT=$(grep -m1 '^\- \[ \] SCENARIO-' "$SOT_FILE" | grep -oE 'SCENARIO-[0-9]+' || true)

  if [[ -z "$NEXT" ]]; then
    echo "All scenarios complete!"
    exit 0
  fi

  echo "========================================"
  echo "  Starting: $NEXT"
  echo "========================================"

  TIMESTAMP=$(date +%Y%m%d_%H%M%S)
  LOG_FILE="$LOG_DIR/${NEXT}_${TIMESTAMP}.log"

  PROMPT="Implement ONLY ${NEXT} from ${SOT_FILE}. Do not implement any other scenario. Follow the pipeline:
1. Invoke the 'architect' agent to plan ${NEXT}: it reads ${SOT_FILE}, identifies layers needed, and creates ${SPEC_DIR}/${NEXT}.md with the implementation checklist.
2. Invoke the 'developer' agent to implement: it reads ${SOT_FILE} for context and ${SPEC_DIR}/${NEXT}.md for the checklist, executes each step with TDD, and marks steps done.
3. Run /run-reviewers (no arguments) to discover all reviewer agents, filter by changed files, spawn relevant reviewers in parallel, and produce a consolidated report.
4. If the review verdict is FAIL, invoke the 'developer' agent in fix mode with ALL findings (violations, warnings, and suggestions). Developer addresses everything in one pass.
5. Mark ${NEXT} as done in ${SOT_FILE} by changing its '- [ ]' to '- [x]' in the BDD Acceptance Progress section."

  echo "Log: $LOG_FILE"
  echo ""
  SCENARIO_START=$(date +%s)

  # --- Run Claude with retry on transient/rate-limit errors ---
  while true; do
    # Heartbeat: cycles A B C every 5 s so the terminal never looks frozen.
    (i=0; chars=(A B C); while true; do sleep 5; printf '%s' "${chars[i % 3]}"; i=$((i+1)); done) &
    HEARTBEAT_PID=$!

    set +e
    claude --dangerously-skip-permissions --output-format stream-json --verbose --model claude-sonnet-4-6 -p "$PROMPT" \
      > "$LOG_FILE" 2>&1
    CLAUDE_EXIT=$?
    set -e

    kill "$HEARTBEAT_PID" 2>/dev/null; wait "$HEARTBEAT_PID" 2>/dev/null || true
    printf '\n'

    # Transient "no messages" error — skip iteration, move on
    if grep -q "No messages returned" "$LOG_FILE" 2>/dev/null; then
      echo "  WARNING: Claude returned no messages (transient). Skipping $NEXT..." >&2
      break
    fi

    # Success
    if [[ $CLAUDE_EXIT -eq 0 ]]; then
      break
    fi

    # Rate limit / spending limit — wait and retry
    echo "  WARNING: Claude exited with code $CLAUDE_EXIT. Waiting ${RETRY_WAIT}s before retry..." >&2
    sleep "$RETRY_WAIT"
    echo "  Retrying $NEXT..."
  done

  # Confirm the scenario was actually marked done before looping
  if grep -q "^\- \[x\] ${NEXT}" "$SOT_FILE"; then
    ELAPSED=$(( $(date +%s) - SCENARIO_START ))
    echo ""
    echo "  $NEXT done in $(( ELAPSED / 60 ))m $(( ELAPSED % 60 ))s."
  else
    echo "" >&2
    echo "ERROR: $NEXT was not marked done in $SOT_FILE." >&2
    echo "Claude may have failed silently. Check: $LOG_FILE" >&2
    exit 1
  fi

  echo ""
done
