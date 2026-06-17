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

## Conventions used across these notes

- **Change / Effect / Why / Verdict** structure per finding.
- Costs are Sonnet-tier (`model: sonnet` reviewers) unless noted.
- "dispatch" = one `claude -p --agent <reviewer>` reviewing one fixture.
