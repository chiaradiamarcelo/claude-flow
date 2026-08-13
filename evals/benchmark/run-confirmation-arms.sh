#!/usr/bin/env bash
# Run confirmation arms one after another, never concurrently.
#
# Two arms in parallel would contend for CPU on the Gradle runs and inflate both
# spans — corrupting the exact metric the confirmation exists to pin down. The
# whole point of these arms is variance, so the runs must not perturb each other.
set -uo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CMD="${CMD:-/run-pipeline-layered bank-accounts}"

for ARM in "$@"; do
  echo "=== $ARM: preparing at $(date +%H:%M:%S) ==="
  "$HERE/run-arm.sh" "$ARM" >/dev/null || { echo "prepare failed for $ARM"; continue; }

  echo "=== $ARM: running at $(date +%H:%M:%S) ==="
  START=$(date +%s)
  ( cd "$HERE/runs/$ARM" && claude -p "$CMD" --dangerously-skip-permissions ) \
      >"$HERE/$ARM-run.log" 2>&1
  END=$(date +%s)
  echo "=== $ARM: finished at $(date +%H:%M:%S), $(( (END-START)/60 ))m$(( (END-START)%60 ))s ==="

  D="$HERE/runs/$ARM"
  echo "  scenarios ticked: $(/usr/bin/grep -c '^- \[x\]' "$D/docs/specifications/bank-accounts/specification.md" 2>/dev/null || echo 0)"
  echo "  plan files:       $(ls "$D"/LAYER-*.md "$D"/DESIGN.md 2>/dev/null | wc -l | tr -d ' ')"
done

echo "=== all confirmation arms complete at $(date) ==="
