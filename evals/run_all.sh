#!/usr/bin/env bash
# evals/run_all.sh — run the pipeline's own test suite.
#
#   ./evals/run_all.sh             # all phases
#   ./evals/run_all.sh --commands  # only command routing tests (cheap-ish)
#   ./evals/run_all.sh --agents    # only agent fixture evals
#   ./evals/run_all.sh api-reviewer            # only that reviewer's corpus
#   ./evals/run_all.sh --agents api-reviewer   # same (explicit)
#
# Phase 0 (structural) is free. Phases 1 & 2 spend tokens via `claude -p`
# (Phase 1 is fingerprint-cached; Phase 2 uses the cheap --dry-run path).
set -uo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
# Least-privilege tool allowlists for the headless `claude -p` runs (read-only;
# no Edit/Write). Reviewers need only Read/Glob/Grep; the command also runs git.
AGENT_TOOLS=(--allowedTools Read Glob Grep)
CMD_TOOLS=(--allowedTools "Bash(git *)" Grep Glob Read)
fail=0
do_agents=1; do_commands=1
ONLY_AGENT=""; ONLY_FIXTURE=""
case "${1:-}" in
  --agents)   do_commands=0; ONLY_AGENT="${2:-}" ;;
  --commands) do_agents=0 ;;
  --*)        echo "usage: run_all.sh [--agents|--commands] [agent-name] | <agent-name> [fixture-name]"; exit 2 ;;
  "")         ;;
  *)          ONLY_AGENT="$1"; ONLY_FIXTURE="${2:-}" ;;  # bare agent name (+ optional single fixture)
esac
# A specific reviewer filter means the command routing tests don't apply.
[ -n "$ONLY_AGENT" ] && [ "$ONLY_AGENT" != "run-reviewers" ] && do_commands=0

echo "== Phase 0: structural (free, no model) =="
for d in evals/*/; do
  [ -d "${d}fixtures" ] || continue
  # the agent-fixture schema check applies only to agent corpora
  [ -f "agents/$(basename "$d")/Agent.md" ] || continue
  [ -n "$ONLY_AGENT" ] && [ "$(basename "$d")" != "$ONLY_AGENT" ] && continue
  python3 evals/eval_grade.py --evals-dir "$d" --check-corpus || fail=1
done

if [ "$do_agents" = 1 ]; then
  echo ""; echo "== Phase 1: agent fixture evals (claude -p, cached) =="
  for adir in evals/*/; do
    [ -d "${adir}fixtures" ] || continue
    agent="$(basename "$adir")"
    [ -f "agents/$agent/Agent.md" ] || continue   # skip command-test corpora
    [ "$agent" = "architect" ] && continue        # plan-producing agent: Phase 1b
    [ "$agent" = "developer" ] && continue         # build-outcome agent: Phase 1c
    [ -n "$ONLY_AGENT" ] && [ "$agent" != "$ONLY_AGENT" ] && continue
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
fi

if [ "$do_agents" = 1 ] && { [ -z "$ONLY_AGENT" ] || [ "$ONLY_AGENT" = "architect" ]; } \
   && [ -d evals/architect/fixtures ]; then
  echo ""; echo "== Phase 1b: plan-producing agent evals (architect) =="
  # The architect WRITES a plan file rather than emitting a JSON verdict, so it
  # can't use the Phase 1 reviewer path. Dispatch it in a scratch copy of the
  # fixture input/ (it reads specification.md, writes SCENARIO-XX.md), then grade
  # the artifact with check_plan.py (no fingerprint cache — always dispatches).
  ARCH_TOOLS=(--allowedTools Read Write Edit Glob Grep Skill)
  for fx in evals/architect/fixtures/*/; do
    [ -f "${fx}expected.json" ] || continue
    scratch="$(mktemp -d)"
    cp -R "${fx}input/." "$scratch/" 2>/dev/null
    prompt="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1])).get("prompt",""))' "${fx}expected.json")"
    ( cd "$scratch" && claude -p "$prompt" --agent architect "${ARCH_TOOLS[@]}" </dev/null >/dev/null 2>&1 )
    python3 evals/check_plan.py "${fx}expected.json" --input-dir "${fx}input" --scratch-dir "$scratch" || fail=1
    rm -rf "$scratch"
  done
fi

if [ "$do_agents" = 1 ] && { [ -z "$ONLY_AGENT" ] || [ "$ONLY_AGENT" = "intent-and-goal" ]; } \
   && [ -d evals/intent-and-goal/fixtures ]; then
  echo ""; echo "== Phase 1e: command artifact evals (/intent-and-goal) =="
  # /intent-and-goal is a COMMAND (not an agent) and interactive, so dispatch it
  # by prompt (no --agent) with the fixture's non-interactive instruction, then
  # grade the specification.md it writes with check_spec.py.
  IAG_TOOLS=(--allowedTools Read Write Glob Grep Skill)
  for fx in evals/intent-and-goal/fixtures/*/; do
    [ -f "${fx}expected.json" ] || continue
    scratch="$(mktemp -d)"
    cp -R "${fx}input/." "$scratch/" 2>/dev/null
    prompt="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1])).get("prompt",""))' "${fx}expected.json")"
    ( cd "$scratch" && claude -p "$prompt" "${IAG_TOOLS[@]}" </dev/null >/dev/null 2>&1 )
    python3 evals/check_spec.py "${fx}expected.json" --input-dir "${fx}input" --scratch-dir "$scratch" || fail=1
    rm -rf "$scratch"
  done
fi

# Phase 1c is the integration layer (developer → real build). It's EXPENSIVE
# (opus agent + a full TDD loop + Gradle, minutes & ~$1-4) so it is strictly
# opt-in: it runs ONLY for `run_all.sh developer`, never in the default suite or
# a bare --agents run.
if [ "$ONLY_AGENT" = "developer" ] && [ -d evals/developer/fixtures ]; then
  echo ""; echo "== Phase 1c: developer integration evals (golden repo, ./gradlew test) =="
  DEV_TOOLS=(--allowedTools Read Write Edit Glob Grep Bash Skill)
  for fx in evals/developer/fixtures/*/; do
    [ -f "${fx}expected.json" ] || continue
    [ -n "$ONLY_FIXTURE" ] && [ "$(basename "$fx")" != "$ONLY_FIXTURE" ] && continue
    scratch="$(mktemp -d)"
    cp -R evals/golden-repo/. "$scratch/" 2>/dev/null   # pristine buildable skeleton
    rm -rf "$scratch/build" "$scratch/.gradle"
    cp -R "${fx}input/." "$scratch/" 2>/dev/null         # overlay frozen spec + plan
    prompt="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1])).get("prompt",""))' "${fx}expected.json")"
    echo "  dispatching developer on $(basename "$fx") — full TDD loop, may take minutes ..."
    ( cd "$scratch" && claude -p "$prompt" --agent developer "${DEV_TOOLS[@]}" </dev/null >"$scratch/.agent.log" 2>&1 )
    # Independent verdict: WE run the build, never trust the agent's self-report.
    ( cd "$scratch" && ./gradlew test --console=plain >"$scratch/.gradle.log" 2>&1 ); ge=$?
    if python3 evals/check_build.py "${fx}expected.json" --scratch-dir "$scratch" --build-exit "$ge"; then
      rm -rf "$scratch"
    else
      fail=1
      echo "    --- gradle tail ---"; tail -25 "$scratch/.gradle.log" 2>/dev/null | sed 's/^/    /'
      echo "    (scratch kept for debugging: $scratch)"
    fi
  done
fi

# Phase 1d is the ACCEPTANCE layer (full pipeline: architect -> developer ->
# reviewers, from a frozen single-scenario spec). Most expensive of all (sonnet
# architect + opus developer + 3 sonnet reviewers + a real build, ~$2-6, many
# minutes), so it is strictly opt-in: ONLY for `run_all.sh pipeline`.
if [ "$ONLY_AGENT" = "pipeline" ] && [ -d evals/pipeline/fixtures ]; then
  echo "== Phase 1d: full-pipeline acceptance (architect -> developer -> reviewers) =="
  # The orchestration (optional intent -> architect -> developer -> build ->
  # reviewers -> fix-loop) lives in evals/harness/pipeline.py, driven by the
  # Agent port. Here we set up the scratch workspace and hand off to the real
  # entrypoint (ClaudeCliAgent + real ./gradlew). The SAME run_pipeline is driven
  # by a FakeAgent in evals/tests/test_pipeline.py — single source of truth.
  for fx in evals/pipeline/fixtures/*/; do
    [ -f "${fx}expected.json" ] || continue
    [ -n "$ONLY_FIXTURE" ] && [ "$(basename "$fx")" != "$ONLY_FIXTURE" ] && continue
    scratch="$(mktemp -d)"
    cp -R evals/golden-repo/. "$scratch/" 2>/dev/null   # pristine buildable skeleton
    rm -rf "$scratch/build" "$scratch/.gradle"
    cp -R "${fx}input/." "$scratch/" 2>/dev/null         # overlay frozen spec (+ plan, if any)
    echo "  orchestrating $(basename "$fx") (intent -> architect -> developer -> build -> reviewers -> fix-loop) ..."
    if python3 evals/harness/run_pipeline.py "${fx}expected.json" "$scratch"; then
      rm -rf "$scratch"
    else
      fail=1
      echo "    --- gradle tail ---"; tail -20 "$scratch/.gradle.log" 2>/dev/null | sed 's/^/    /'
      echo "    (scratch kept for debugging: $scratch)"
    fi
  done
fi

if [ "$do_commands" = 1 ]; then
  echo ""; echo "== Phase 2: command routing tests (claude -p --dry-run) =="
  for fxdir in evals/run-reviewers/fixtures/*/; do
    [ -f "${fxdir}expected.json" ] || continue
    scratch="$(mktemp -d)"
    ( cd "$scratch" && git init -q )
    # routing is path-only: create the changed files empty, leave them untracked
    # (the command detects them via `git ls-files --others`).
    python3 - "${fxdir}expected.json" "$scratch" <<'PY'
import json, os, sys
exp = json.load(open(sys.argv[1])); root = sys.argv[2]
for f in exp["changed_files"]:
    p = os.path.join(root, f)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    open(p, "w").close()
PY
    out="$(mktemp)"
    # </dev/null: don't let `claude -p` read the script's inherited stdin (same
    # hygiene as Phase 1) — without it the headless run can misbehave.
    ( cd "$scratch" && claude -p "/run-reviewers --dry-run" "${CMD_TOOLS[@]}" </dev/null 2>/dev/null ) > "$out"
    python3 evals/check_routing.py "${fxdir}expected.json" "$out" || fail=1
    rm -rf "$scratch" "$out"
  done
fi

echo ""
if [ "$fail" = 0 ]; then echo "ALL PASS"; else echo "FAILURES (exit 1)"; fi
exit $fail
