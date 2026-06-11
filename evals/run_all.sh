#!/usr/bin/env bash
# evals/run_all.sh — run the pipeline's own test suite.
#
#   ./evals/run_all.sh             # all phases
#   ./evals/run_all.sh --commands  # only command routing tests (cheap-ish)
#   ./evals/run_all.sh --agents    # only agent fixture evals
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
case "${1:-}" in
  --agents)   do_commands=0 ;;
  --commands) do_agents=0 ;;
  "")         ;;
  *) echo "usage: run_all.sh [--agents|--commands]"; exit 2 ;;
esac

echo "== Phase 0: structural (free, no model) =="
for d in evals/*/; do
  [ -d "${d}fixtures" ] || continue
  # the agent-fixture schema check applies only to agent corpora
  [ -f "agents/$(basename "$d")/Agent.md" ] || continue
  python3 evals/eval_grade.py --evals-dir "$d" --check-corpus || fail=1
done

if [ "$do_agents" = 1 ]; then
  echo ""; echo "== Phase 1: agent fixture evals (claude -p, cached) =="
  for adir in evals/*/; do
    [ -d "${adir}fixtures" ] || continue
    agent="$(basename "$adir")"
    [ -f "agents/$agent/Agent.md" ] || continue   # skip command-test corpora
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
