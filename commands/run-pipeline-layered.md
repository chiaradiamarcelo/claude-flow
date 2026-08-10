---
description: EXPERIMENTAL fork of /run-pipeline. Designs the whole feature up front, then builds it layer by layer instead of scenario by scenario. Keeps the test-designer and batch-red verification.
argument-hint: <feature-slug, e.g. bank-accounts>
allowed-tools: Read, Glob, Grep, Edit, Bash, Agent, Skill
---

Run the **layered** implementation pipeline for: **$ARGUMENTS**

> **This is a fork under measurement, not the default.** `/run-pipeline` remains the
> adopted pipeline. This one changes the unit of work from the **scenario** to the
> **layer**, on the hypothesis that a whole-feature design plus coarser test batches is
> cheaper and opens the door to parallel workers. Do not mix the two on one feature.

## Step 0: Resolve project skill injection

Identical to `/run-pipeline`'s Step 0. Read `.claude/pipeline.json`'s optional
`agentSkills` map and append the injection line to each dispatched agent that has a
non-empty entry. `system-architect` takes injections the same way the others do.

## Step 1: Design the whole feature, once

Read `docs/specifications/<feature-slug>/specification.md`. If it does not exist,
**STOP** and report that no approved specification was found — write no code.

Run **`system-architect`**. It produces `DESIGN.md`: the layer map, the contracts and
signatures, the API surface, the scenario × layer matrix, the build order, and the
list of **specification gaps**.

**Read `## Specification Gaps` before going further.** For each gap, report it to the
user in your running output — a business rule that no scenario would falsify is a hole
the feature will ship with. Do **not** amend the specification and do **not** invent
scenarios to close them; the specification is the user's. Record them so they are
decisions rather than accidents.

## Step 2: Build layer by layer, in `DESIGN.md`'s build order

**For each layer, in order — one layer at a time:**

1. Run **`test-designer`** scoped to the layer (pass the layer name, not a scenario ID).
   It writes `LAYER-<name>.md` with the ordered test list for every artifact in that
   layer, across all scenarios.
2. Run **`developer`** scoped to the same layer. It executes that list with
   **batch-red per class**, exactly as it does for a scenario — the batch boundary is
   still the class, not the layer, because that is the granularity measured at −46%
   cost with no quality regression.
3. **Commit the layer's work** with the layer name in the message.
4. Using `DESIGN.md`'s scenario × layer matrix, **tick every scenario whose last
   marked layer has now been built**, in `## BDD Acceptance Progress`. A scenario is
   not observable before then, so ticking it earlier would be a lie.

## Step 3: Reviewers and triage

Identical to `/run-pipeline`. Run **`/run-reviewers`**, then:
- **Every VIOLATION is fixed.** No exceptions.
- Then warnings and suggestions, most-consequential first — data loss, broken named
  invariants, and misleading code rank above style.
- **At most 2 fix rounds.** Everything unfixed goes to the specification's
  `## Follow-ups` with its reason.
- **If any VIOLATION remains unfixed when the budget is spent, headline it.**

## Step 4: Verify every scenario is actually covered

Before reporting done, check each scenario in `## BDD Acceptance Progress` against the
test suite: **is there at least one test that would fail if that scenario's `Then` were
violated?**

Building by layer makes it possible to satisfy every layer's contract and still leave a
scenario unfalsified — the failure mode scenario-at-a-time cannot have. Any scenario
you cannot trace to a failing-if-violated test is reported as **not covered**, by name,
in your final report. Do not tick it.

**Rules:**
- **One layer at a time, and one `developer` in flight.** Concurrency across layers is
  the *next* experiment; this arm measures the design change alone, so that a bad
  result has one cause.
- Batch-red per class stays. It is the only thing that catches a test and its
  production code co-adapted into a fake green, and mutation testing is near-silent on
  this pipeline's output (finding 14), so nothing else would.
- Never skip `/run-reviewers`.
- Auto-continue — do not ask for permission between steps.
