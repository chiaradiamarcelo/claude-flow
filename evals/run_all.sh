#!/usr/bin/env bash
# evals/run_all.sh — run the pipeline's own test suite.
#
#   ./evals/run_all.sh                  # default: structural + reviewers (cached) + architect + intent + routing
#   ./evals/run_all.sh <corpus>         # just that corpus (api-reviewer, architect, developer, pipeline, orchestration, run-reviewers, ...)
#   ./evals/run_all.sh <corpus> <fixt>  # one fixture in a non-reviewer corpus
#   ./evals/run_all.sh --commands       # only the routing tests
#   ./evals/run_all.sh --agents [name]  # only agent fixture evals
#
# Reviewers run through the fingerprint-CACHED path (eval_grade) — unchanged
# fixtures cost $0. Every other kind runs through the SINGLE engine
# (run_fixture.py / ./evals/evals), which reads each fixture's test.json. The
# heavy kinds (developer, pipeline, orchestration) are opt-in — they run only
# when named. Phase 0 is free; the rest spend tokens via `claude -p`.
#
# For one fixture in the red/green TDD loop, prefer:  ./evals/evals --test <name>
set -uo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
AGENT_TOOLS=(--allowedTools Read Glob Grep)
REVIEWERS="api-reviewer arch-reviewer refactor-advisor test-reviewer ui-test-reviewer android-ui-test-reviewer"
OPTIN=" developer pipeline orchestration "   # heavy/paid — run only when named
fail=0
do_agents=1; do_commands=1
ONLY_AGENT=""; ONLY_FIXTURE=""
case "${1:-}" in
  --agents)   do_commands=0; ONLY_AGENT="${2:-}" ;;
  --commands) do_agents=0 ;;
  --*)        echo "usage: run_all.sh [--agents|--commands] [corpus] | <corpus> [fixture]"; exit 2 ;;
  "")         ;;
  *)          ONLY_AGENT="$1"; ONLY_FIXTURE="${2:-}" ;;
esac
[ -n "$ONLY_AGENT" ] && [ "$ONLY_AGENT" != "run-reviewers" ] && [ "$ONLY_AGENT" != "run-pipeline" ] && do_commands=0

want() {  # want <corpus> — run it given ONLY_AGENT + the opt-in rule?
  local c="$1"
  if [ -n "$ONLY_AGENT" ]; then [ "$ONLY_AGENT" = "$c" ]; return; fi
  case "$OPTIN" in *" $c "*) return 1 ;; esac   # opt-in kinds are skipped by default
  return 0
}

engine_corpus() {  # run every fixture of a corpus through the single engine
  local c="$1"
  [ -d "evals/$c/fixtures" ] || return 0
  echo ""; echo "== $c (engine: run_fixture.py) =="
  for fx in evals/"$c"/fixtures/*/; do
    [ -f "${fx}test.json" ] || continue
    local name; name="$(basename "$fx")"
    [ -n "$ONLY_FIXTURE" ] && [ "$name" != "$ONLY_FIXTURE" ] && continue
    python3 evals/run_fixture.py --test "$name" --agent "$c" || fail=1
  done
}

echo "== Phase 0: structural (free, no model) =="
for d in evals/*/; do
  [ -d "${d}fixtures" ] || continue
  [ -f "agents/$(basename "$d")/Agent.md" ] || continue   # only agent corpora have a schema check
  [ -n "$ONLY_AGENT" ] && [ "$(basename "$d")" != "$ONLY_AGENT" ] && continue
  python3 evals/eval_grade.py --evals-dir "$d" --check-corpus || fail=1
done

if [ "$do_agents" = 1 ]; then
  echo ""; echo "== Phase 1: reviewer evals (claude -p, fingerprint-cached) =="
  for agent in $REVIEWERS; do
    [ -d "evals/$agent/fixtures" ] || continue
    [ -n "$ONLY_AGENT" ] && [ "$agent" != "$ONLY_AGENT" ] && continue
    adir="evals/$agent/"
    vd="$(mktemp -d)"
    # Capture RUN pairs first. A `--plan | while read` pipe would let `claude -p`
    # (which reads stdin) swallow the remaining pairs — only the first dispatches.
    runs="$(python3 evals/eval_grade.py --evals-dir "$adir" --plan | awk '/^- RUN/{print $3}')"
    for pair in $runs; do
      stem="${pair%%::*}"
      claude -p "Review the file(s) under $ROOT/${adir}fixtures/$stem/input/. Read them directly with the Read tool. Return ONLY your machine-first JSON verdict." \
        --agent "$agent" "${AGENT_TOOLS[@]}" </dev/null 2>/dev/null \
        | python3 -c 'import sys,re; t=sys.stdin.read(); m=re.search(r"\{.*\}",t,re.S); print(m.group(0) if m else "{}")' \
        > "$vd/$stem.json"
    done
    actuals="$(mktemp)"
    python3 - "$agent" "$vd" "$actuals" <<'PY'
import json, glob, os, sys
agent, vd, out = sys.argv[1], sys.argv[2], sys.argv[3]
a = {}
for p in glob.glob(os.path.join(vd, "*.json")):
    stem = os.path.basename(p)[:-5]
    try: v = json.load(open(p))
    except Exception: v = {}
    a.setdefault(stem, {}).setdefault("agents", {})[agent] = v
json.dump(a, open(out, "w"))
PY
    python3 evals/eval_grade.py --evals-dir "$adir" --actuals "$actuals" --write-cache \
      || { fail=1; echo "--- verdicts ($agent) ---"; cat "$actuals"; echo; }
    rm -rf "$vd" "$actuals"
  done

  # Every non-reviewer kind runs through the single engine. architect + intent
  # run by default; developer/pipeline/orchestration are opt-in (heavy/paid).
  for c in architect test-designer intent-and-goal developer pipeline orchestration; do
    want "$c" && engine_corpus "$c"
  done
fi

if [ "$do_commands" = 1 ]; then
  echo ""; echo "== Phase 2: command dry-run tests (engine) =="
  want run-reviewers && engine_corpus run-reviewers
  want run-pipeline  && engine_corpus run-pipeline
fi

echo ""
if [ "$fail" = 0 ]; then echo "ALL PASS"; else echo "FAILURES (exit 1)"; fi
exit $fail
