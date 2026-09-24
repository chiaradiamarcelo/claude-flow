#!/usr/bin/env bash
# Asserts that the bundled-reviewer table in commands/run-reviewers.md (Step 2a) still
# matches the agents' own frontmatter, in both directions.
#
# The table exists because a plugin's agents are not on the consuming project's
# filesystem, so /claude-flow:run-reviewers cannot discover them by grepping. That buys
# correctness under a plugin install at the price of stating the triggers twice. This
# check keeps the price honest: a silent mismatch shows up as a reviewer that never
# fires — the failure mode that looks exactly like a clean review.
#
#   bash scripts/check-reviewers.sh
set -uo pipefail

cd "$(dirname "$0")/.." || exit 1

table=commands/run-reviewers.md
fail=0
checked=0

normalise() {           # ["a", "b"]  ->  a\nb   (sorted, one per line)
  tr ',' '\n' | sed -e 's/[][]//g' -e 's/"//g' -e "s/'//g" -e 's/`//g' \
                    -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//' | sed '/^$/d' | sort
}

for agent in agents/*.md; do
  grep -q '^type: reviewer' "$agent" || continue
  name="$(basename "$agent" .md)"
  checked=$((checked + 1))

  from_agent="$(sed -n 's/^triggers: *//p' "$agent" | head -1 | normalise)"
  row="$(grep -F "| \`$name\` |" "$table" | head -1)"

  if [ -z "$row" ]; then
    echo "  FAIL  $name is a reviewer but has no row in the Step 2a table"
    fail=$((fail + 1))
    continue
  fi

  from_table="$(printf '%s' "$row" | awk -F'|' '{print $3}' | normalise)"
  if [ "$from_agent" != "$from_table" ]; then
    echo "  FAIL  $name triggers differ"
    diff <(printf '%s\n' "$from_agent") <(printf '%s\n' "$from_table") \
      | sed -e 's/^</    agent:/' -e 's/^>/    table:/' | grep -E 'agent:|table:'
    fail=$((fail + 1))
  else
    echo "  ok    $name"
  fi
done

for name in $(sed -n 's/^| `\([a-z-]*\)` |.*/\1/p' "$table"); do
  if ! grep -q '^type: reviewer' "agents/$name.md" 2>/dev/null; then
    echo "  FAIL  the Step 2a table lists $name, but agents/$name.md is not a reviewer"
    fail=$((fail + 1))
  fi
done

# A bundled reviewer must be spawned by its namespaced name: a bare name can resolve to a
# personal or project agent of the same name, tuned for another stack.
if ! grep -q 'subagent_type="<claude-flow:name for a bundled reviewer' "$table"; then
  echo "  FAIL  Step 5 no longer spawns bundled reviewers as claude-flow:<name>"
  fail=$((fail + 1))
fi

echo
if [ "$fail" -eq 0 ]; then
  echo "$checked reviewers in sync"
else
  echo "$fail problem(s) across $checked reviewers"
  exit 1
fi
