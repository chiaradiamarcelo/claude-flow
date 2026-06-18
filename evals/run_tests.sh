#!/usr/bin/env bash
# evals/run_tests.sh — harness self-tests (model-free, $0, deterministic).
#
# These test the HARNESS itself — the graders, manifest loading, and workspace
# setup — via direct calls to the pure functions. No `claude -p`, no tokens.
# Distinct from run_all.sh, which dispatches the real agents to judge quality.
set -uo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
python3 -m unittest discover -s evals/tests -t . "$@"
