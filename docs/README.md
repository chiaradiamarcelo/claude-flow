# Engineering findings (lab notebook)

Measured discoveries from building and running the pipeline's own eval harness
("using the tool to build the tool"). Each entry records **what changed**,
**what it caused** (performance / cost / quality), and **why** (the mechanism) —
so a decision is never re-litigated from a hunch.

Every number here was *measured*, not estimated — mostly via
`claude -p ... --output-format stream-json` (`total_cost_usd` + token usage) and
the eval suite (`evals/run_all.sh`).

## Findings

1. [A deterministic grader bug masqueraded as agent flakiness](findings/01-grader-bug-masquerades-as-agent-flakiness.md)
   — a one-character regex flaw (`\s` vs `[ \t]`) looked like the model "routing
   by topic" and cost a quarantine + a whole router script before we found it.
2. [Skill loading: always-on `@`-include vs on-demand `Skill` tool](findings/02-skill-loading-include-vs-on-demand.md)
   — moving the skill from an `@`-include to a frontmatter `skills:` + `Skill`
   tool cost **~1.8× per dispatch** and ~1.7× wall-clock for **zero** quality
   gain. Rejected.
3. [Eval cost model](findings/03-eval-cost-model.md)
   — ~$0.06 per reviewer dispatch, ~$1.7 for the 29-fixture corpus cold, **$0**
   on cached re-runs. What's cached, what isn't, what invalidates it.
4. [Writing robust agent evals](findings/04-writing-robust-agent-evals.md)
   — fresh-process requirement, tolerant assertions, `mustMention` substring
   pitfalls, when (not) to quarantine.
5. [Exhaustive corpora for the other four reviewers](findings/05-exhaustive-corpora-for-all-reviewers.md)
   — 50 fixtures across api/arch/refactor/ui. Clean *controls* split reviewers in
   two: **structural** reviewers PASS clean code; the **advisory** reviewer never
   can (the strict-gate evidence, now encoded as a regression test).
6. [Testing a generative agent (the architect)](findings/06-testing-a-generative-agent-the-architect.md)
   — the architect *writes a plan file*, so we **grade the artifact, not stdout**:
   new `check_plan.py` + a scratch-dir dispatch (`run_all.sh` Phase 1b). Confirms
   it plans-not-implements (`writesNoCode`), embeds `201`+`Location` for creates,
   and routes read-side scenarios to a `Query` port.
7. [Developer integration on a golden repo](findings/07-developer-integration-golden-repo.md)
   — the integration layer: the real `opus` developer agent runs a TDD loop in a
   buildable Kotlin/JUnit5 repo, then **we independently run `./gradlew test`** and
   grade the objective outcome (`check_build.py`, `run_all.sh` Phase 1c, opt-in).
   First proof that *generated code compiles and passes* — Kotlin over TS for
   fidelity, framework-free core for speed.
8. [Acceptance layer: full pipeline + self-correcting fix-loop](findings/08-acceptance-layer-full-pipeline-fixloop.md)
   — the top rung: `/intent-and-goal` → architect → developer → reviewers →
   **Phase 5 fix-loop**, end to end from a one-line feature description. Caught a
   real test-quality VIOLATION in the developer's output and **self-corrected it
   in one fix round**. Gate = build-green + zero VIOLATIONs (advisory non-gating).
9. [The Agent port + FakeAgent](findings/09-agent-port-and-fakeagent.md)
   — testing the *harness*, not the model. The two-questions reframe (agent
   quality needs the real model; orchestration glue is fakeable), why FakeAgent
   is useless for reviewer fixtures but gold for orchestration. Slice 1: the
   `Agent` port + `FakeAgent` + the finding-01 parser regression. Slice 2a: the
   fix-loop lifted behind the port + $0 control-flow tests. Slice 2b: the
   **CLAUDE.md choreography** test — real orchestrator + fake worker agent
   definitions that self-log; a minimal prompt drove the full plan→implement→
   review→fix→re-review→stop dance.
10. [Orchestration belongs in a command, not a test-only Python harness](findings/10-orchestration-as-a-command.md)
    — reverses finding 09's injectable Python orchestrator. `run_pipeline.py` was
    artificial (no user invokes it) and duplicated CLAUDE.md's choreography.
    Extracted the pipeline into a real **`/run-pipeline` command** (CLAUDE.md
    shrinks to a thin pointer → `/intent-and-goal` → handoff); deleted the Agent
    port + `FakeAgent` + Python orchestrator; tests now drive the **real
    command**. Won: no drift, real artifact under test. Lost: the $0 deterministic
    fix-loop test. Phase 1f, on the real command, drove the full dance.
11. [Every fixture is a test.json (given/when/then) + one engine](findings/11-test-json-migration.md)
    — the corpus was half-declarative (WHEN lived in `run_all.sh`'s bash phases).
    Now every fixture is DATA: a `test.json` with `given`/`when`/`then`, `when.do`
    a **closed enum** (no Cucumber glue), run by one engine (`./evals/evals`). 92
    fixtures migrated. **Decision recorded (option A): preserve the fingerprint
    cache** — repoint `eval_grade` at `test.json`, keep the cached reviewer path,
    route other kinds through the engine, delete `/run-evals`; rejected dropping
    the cache for a single path (would regress `$0` re-runs to ~$1.7). Full
    one-path unification deferred.
12. [v2 integration: a framework-ful golden repo (Spring/JPA vertical slice)](findings/12-v2-spring-jpa-integration.md)
    — finding 07's developer ran on a framework-*free* repo; this adds a second
    buildable skeleton `golden-repo-spring` (Spring Boot 4 + Spring Data JPA + H2)
    so the pipeline is proven on a **full vertical slice** (HTTP + persistence),
    building green on JDK 25 / Kotlin 2.1 / Gradle 9.4.
13. [Strict row-by-row TDD vs batch-red-per-class (developer inner loop)](findings/13-batch-vs-strict-tdd.md)
    — an A/B across **three structurally different scenarios + a 4×-per-arm variance
    study**: batching red-green **per class** ran the test suite ~⅓ as often and was
    ~30–50% cheaper with **no quality regression** (mutation/CRAP/duplication/reviewer
    parity). Promoted to the developer's inner-loop rule; made the standalone `tdd`
    skill redundant → **removed it** and the CLAUDE.md TDD prose.
14. [Mutation/CRAP/DRY as a pipeline gate — spike](findings/14-mutation-gate-spike.md)
    — spiked before building: a *naive* mutation gate is **100% false positives** on
    clean pipeline output (all survivors are boilerplate/Kotlin intrinsics); a
    *filtered* gate is silent on good output but caught a genuine test regression.
    CRAP/CPD produced 0 findings. Recommend filtered mutation as an **optional
    safety-net** gate only; skip CRAP/DRY. Not wired.
15. [Pipeline cost programme — Stage 1 and Stage 2](findings/15-pipeline-cost-stage-1-and-2.md)
    — the plan files were the cost. Capping the architect's `Structure & Contracts`,
    making the test-designer's tables *be* the deliverable, moving the developer's
    narrative out of the plan, and fixing the reviewer gate to fail only on VIOLATIONs:
    **−18% wall-clock, −24% output tokens**, filtered mutation survivors **2 → 0**.
    Also rejects Stage 3 (planning scenarios ahead) at both depths — red arrival collapses
    89% → 64%, because a scenario is only red thanks to what its predecessor deliberately
    left out.
16. [The layered pipeline is rejected; its specification review is kept](findings/16-layered-pipeline-rejected.md)
    — changing the unit of work from the scenario to the **layer** saved ~10% time and 20%
    tokens and cost **2.3 candidate-real mutation survivors against 0**, across four arms.
    Coarsen the test-designer's per-scenario mutation reasoning and finding 14's reason for
    *not* gating on mutation goes with it. One idea was kept and is worth more
    than the fork it came from: checking each business rule against the scenarios, now
    folded into `/intent-and-goal` Phase 2's own iteration. The agent extracted to hold it
    was dropped — measured against a plain review pass it added nothing and mis-certified a
    rule as covered — and so was the separate review phase, whose disposition step was
    wrong: an uncovered rule has to become a question to the user, not a labelled note.

## Conventions used across these notes

- **Change / Effect / Why / Verdict** structure per finding.
- Costs are Sonnet-tier (`model: sonnet` reviewers) unless noted.
- "dispatch" = one `claude -p --agent <reviewer>` reviewing one fixture.
