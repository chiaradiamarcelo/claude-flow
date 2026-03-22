#!/usr/bin/env bash
# Runs all pending BDD scenarios from a specification folder, one at a time.
# Each scenario gets a fresh Claude context via /continue-scenario.
#
# Usage:
#   ./scripts/run-scenarios.sh <feature-slug>
#
# Example:
#   ./scripts/run-scenarios.sh deposit-money

set -euo pipefail

RETRY_WAIT=300   # seconds to wait after a rate-limit / spending-limit error

# --- Resolve specification folder ---
FEATURE_SLUG="${1:-}"

if [[ -z "$FEATURE_SLUG" ]]; then
  echo "ERROR: Feature slug required." >&2
  echo "Usage: ./scripts/run-scenarios.sh <feature-slug>" >&2
  echo "Example: ./scripts/run-scenarios.sh deposit-money" >&2
  exit 1
fi

SPEC_DIR="docs/specifications/${FEATURE_SLUG}"
SOT_FILE="${SPEC_DIR}/specification.md"

if [[ ! -f "$SOT_FILE" ]]; then
  echo "ERROR: Specification file not found: $SOT_FILE" >&2
  exit 1
fi

# --- Setup ---
LOG_DIR="logs/scenarios"
mkdir -p "$LOG_DIR"

echo "Feature: $FEATURE_SLUG"
echo "Specification: $SOT_FILE"
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

  echo "Log: $LOG_FILE"
  echo ""
  SCENARIO_START=$(date +%s)

  # --- Run Claude with retry on transient/rate-limit errors ---
  while true; do
    # Heartbeat: cycles A B C every 5 s so the terminal never looks frozen.
    (i=0; chars=(A B C); while true; do sleep 5; printf '%s' "${chars[i % 3]}"; i=$((i+1)); done) &
    HEARTBEAT_PID=$!

    set +e
    claude --dangerously-skip-permissions --output-format stream-json --verbose -p "/continue-scenario ${SPEC_DIR}" \
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
