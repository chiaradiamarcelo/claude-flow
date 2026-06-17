# Finding 11 — Every fixture is a test.json (given/when/then) + one engine

**Date:** 2026-06 · **Area:** `evals/`
**Status:** migration done (chunk 1); cleanup + cache repoint (chunk 2)

The eval corpus was half-declarative: `input/` (GIVEN) + `expected.json` (THEN),
but the **WHEN** — how each fixture is run — lived implicitly in `run_all.sh`'s
per-kind bash phases. So "run one fixture by name" was impossible, and the
dispatch logic was spread across the suite runner.

## The change
Every fixture is now DATA: a single **`test.json`** manifest with
`given` / `when` / `then`. The WHEN is explicit and is a **closed enum**
(`when.do ∈ {agent, command, build}`) — deliberately *not* free-text steps, so
there is no Cucumber-style glue layer to rot. `run_fixture.py` (`./evals/evals`)
is the single engine: a handler per `do`, a grader registry mapping `then.grader`
to the existing pure `grade_*` functions. 92 fixtures across 11 corpora migrated;
`expected.json` is gone. A `$0` wiring test asserts every `when.do`/`then.grader`
in the real corpus is registered.

## Decision — preserve the fingerprint cache (option A)

Migrating off `expected.json` broke the two consumers that read it: `run_all.sh`
and `eval_grade.py` — the latter owns the **fingerprint cache** that makes
unchanged reviewer re-runs cost **$0** (finding 03). We had to choose how to
reconcile them.

**Decision: keep the cache.** Repoint `eval_grade`'s fingerprint / cache /
diff-scoping at `test.json` (the reviewer spec now comes from `then`), keep
`run_all.sh`'s **cached** reviewer dispatch path, and route the *other*
(non-reviewer) phases through the new `evals` engine. Delete `/run-evals`
(redundant — its job is `evals --test` + the cached `run_all.sh` path).

**Alternative rejected (B): one path, drop the cache.** Make `run_all.sh` a thin
loop over `evals --test` for everything and delete the cache. Maximally uniform
(one engine, one path) but the reviewer suite would re-dispatch every run
(~$1.7), regressing the cost optimization we deliberately built.

**Consequences.**
- ✅ `$0` cached reviewer re-runs preserved; no cost regression.
- ⚠️ Two dispatch paths remain for now: cached-bash for the reviewer corpus,
  the engine for everything else. A known, temporary non-uniformity.
- ⏭️ Full unification — port the fingerprint cache into the engine's batch mode
  (`evals --all/--agent/--changed`), then `run_all.sh` collapses to a thin caller
  and the two paths become one. Deferred, tracked in PROGRESS.

The tie-breaker: don't regress a measured optimization to buy architectural
tidiness we can reach later without the regression.
