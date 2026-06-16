#!/usr/bin/env bash
# evals/run_tests.sh — harness self-tests (model-free, $0, deterministic).
#
# These test the HARNESS itself — the graders and orchestration glue — using the
# FakeAgent and direct grader calls. No `claude -p`, no tokens. Distinct from
# run_all.sh, which dispatches the real agents to judge agent quality.
set -uo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
python3 -m unittest discover -s evals/tests -t . "$@"
