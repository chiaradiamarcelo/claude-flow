---
name: legacy-code
description: Use when working on untested, tangled, or outdated code — adding tests to a system that has none, untangling shared mutable state, replacing deprecated patterns, language/framework migrations, dependency rewrites. Follows Michael Feathers' "Working Effectively With Legacy Code" approach. Language-agnostic.
---

The order of phases matters. Do not skip ahead. **Get the code under test before you change it.**

## Phase 0 — Audit

- Map the boundary: what calls into the target, what the target calls out to.
- Risk-rank each touched file by branching, side-effects, and current test coverage gap.
- Document **surprising findings** as locked-in tests, not silent fixes. If you discover dead code, an obvious bug, or a contradictory invariant, add a test that pins the *current* (possibly wrong) behavior, comment why, and put the fix in a separate PR with its own ticket. Conflating "lock in current behavior" with "fix the bug while you're there" makes both reviews worse.

## Phase 1 — Safety net (Feathers' rule: get it under test before you change it)

- Choose the smallest seam that lets you observe behavior. Mocks, fakes, stubs, recording adapters — whatever gets you a passing test for the current behavior.
- Mocks for infrastructure (databases, queues, third-party APIs) are acceptable as **interim** — acknowledge in the PR body what they don't catch (schema drift, network behavior, transactional edges, library quirks) and that this is a migration-window risk only.
- Defer real-infra integration tests (containers, fakes + contract tests) to Phase 4. Introducing them inside the migration PR widens the change too much and stalls progress.

## Phase 2 — Untangle shared mutable state during the change, not after

- Module-level / static / singleton mutable state is the most common reason tests are awkward. File-top caches, registries, session maps, environment-coupled config readers — these all fight reset between tests.
- Lift them into named factories with their tunables passed in (`createCache(ttl)`, `createRegistry(loader)`). Have the consumer be a factory that takes the state as input.
- Tests then construct fresh instances per scenario. No reset rituals, no module reloads, no fake-timer dances around hidden initialization.
- Do this in the **same PR** as the change you're already making. Splitting it into a follow-up tends to leave the seam half-built and the tests stay awkward.

## Phase 3 — Modernize incrementally

- One concern per PR. Keep review surface small.
- **Leaf-first.** Start with files that have no inbound or outbound local dependencies; they're the safest renames/conversions. Work outward.
- Plan the waves before writing them down — write the wave list into the first PR's description and tick them off in subsequent PRs. Reviewers can follow the plan; future you can resume after a context break.
- Don't interleave migrations with feature work. Pause feature work on the touched files until the migration through them is complete.

## Phase 4 — Replace interim mocks

- Once the system is on the new language / framework / pattern, swap mocks for real-infra tests: containers, fakes + contract tests run against the real dependency, recorded interactions verified against a current capture.
- Target the files identified as infrastructure-touching during Phase 0.
- This is its own PR(s), after the migration is complete — it's awkward to introduce when the surrounding code is mid-rewrite.

## Cross-cutting principles

- **Pin behavior, then change.** Never change behavior in the same commit that captures it. The test commit is reviewable on its own; the change commit shows exactly what shifted.
- **Surprising things become tests, not silent fixes.** Even if you "know" something is wrong, prove the current behavior with a test first. Then a separate PR fixes it. The audit is more valuable than the fix.
- **No backwards-compatibility cruft for a one-shot migration.** If you're replacing a pattern wholesale, replace it. Don't carry both versions forward unless there's a real partial-rollout reason (canary, dual-write, staged rollout).
- **Track gotchas as you find them.** The first migration of a kind hits surprises. Write them in the PR body; they become the playbook for the next one. After three migrations of the same kind, the gotchas list is the most valuable artifact.
- **Mocks → fakes → real infra is a one-way street.** Don't introduce mocks "for now" without a concrete plan to remove them. If you're not going to remove them, just write a fake from the start.

## Out of scope (use a different skill)

- **Greenfield code** → use `tdd` + `clean-architecture`.
- **Pure dependency upgrades** with no behavior change → standard upgrade work, not legacy-code.
- **Architectural redesign** → a separate planning concern that follows once the legacy code is testable.

---

This skill is intentionally generic and language-agnostic. Project-specific applications (e.g. JavaScript → TypeScript wave templates, monorepo toolchain notes, reference PRs) live in project-level skill files that complement this one.
