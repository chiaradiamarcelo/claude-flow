# Finding 03 — Eval cost model

**Date:** 2026-06 · **Area:** `evals/` suite economics
**Status:** measured baseline

## The change

Establishing what it actually costs to run the agent eval suite, so cost is a
known quantity rather than a worry. Measured via
`claude -p ... --output-format stream-json` (`total_cost_usd`).

## Measured numbers (Sonnet reviewers)

| Item | Cost |
|---|---|
| **One reviewer dispatch** (1 fixture, skill in cached prefix) | **~$0.060** |
| Token shape of one dispatch | ~9k cache-write + ~22k cache-read + ~1.2k output |
| **Exhaustive `test-reviewer` corpus (29 fixtures), cold** | **~$1.7** |
| Full agent suite, all 5 reviewers, cold (~33 dispatches) | **~$2** |
| **Re-run with nothing changed** | **$0** (fingerprint cache → all CACHED) |
| Re-run after editing **one fixture** | ~$0.06 |
| Re-run after editing the **agent or the skill** | full ~$1.7 (invalidates all its fixtures) |
| Command routing test (`--commands`, per live run) | ~$0.12, **not cached** |

## Why — where the money goes and why caching matters

A reviewer dispatch is **almost all input tokens**, dominated by the
`@`-referenced skill (`testing/SKILL.md` ≈ the bulk of the ~22k cache-read) plus
the agent/system prompt. The fixture file (~300 tokens) and the JSON verdict
(~1.2k output) are tiny.

Two independent caches:

1. **Eval fingerprint cache** (`evals/<agent>/.eval-cache.json`, git-ignored):
   a fixture is fingerprinted over `(Agent.md + @-referenced skills + input +
   expected.json)`. Unchanged → `CACHED` → **no dispatch at all** → $0. This is
   what makes day-to-day re-runs free.
2. **Anthropic prompt cache** (server-side, 5-min TTL): within a run, the static
   skill+system prefix is reused across dispatches → `cache_read` at $0.30/M
   instead of $3/M. This is why a *warm* dispatch is ~$0.06 vs a cold ~$0.13.

## The headline

**Pay ~$1.7 once to establish the regression net, then $0 on every re-run** until
you change the agent, the skill, or a fixture — exactly when you *want* to
re-verify. The only always-paid cost is the routing tests at ~$0.12/run, because
they exercise the live command and aren't fingerprint-cached.

So: budget **~$2 for a from-scratch full run**, ~nothing for the routine "did my
prompt edit break anything" checks.

## Gotcha

`run_all.sh` writes the fingerprint cache **after** grading. If you run an
*experiment* on an agent (changing its `Agent.md`), the cache is overwritten with
the experiment's fingerprints; reverting the agent then no longer matches, so the
next run re-dispatches once (~$1.7) and re-caches the baseline. The cache is
git-ignored and self-heals — just don't expect "free" immediately after an
agent-level experiment.
