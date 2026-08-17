## Comment that argues the design

### Smell

A doc block on a **declaration** — a class, a property, a function — that re-derives the design
decision the code already embodies:

- *"It lives here rather than in the screen because…"*
- *"It is carried rather than worked out from X because…"*
- *"This rides on `Success` rather than a variant of its own because…"*

It reads like a *why*, so it survives both *Comment as a missing name* (it is not narrating
mechanics) and *Comment that restates a test* (it is not asserting a rule a test holds). But it
is not a *why* about a fact outside the code's reach. It is a **transcript of the reasoning that
produced the code**, addressed to a reviewer who is no longer in the room.

Apply the `comments` skill's test: *could this become false without a test going red?* It always can —
refactor the code and the argument is stale, silently.

This is the dominant shape produced by an agent pipeline, because the agent has just spent a
plan file arguing the decision and the argument comes out attached to the code.

### Trigger

You are reading a declaration's doc block and:

- its subject is a **choice between alternatives**, not a fact about the world;
- removing it would not make the code harder to *use*, only harder to *justify*;
- the same reasoning already exists in a scenario plan file, an ADR, or a commit message;
- the file's comment lines outnumber its code lines.

### Refactoring

1. **Locate the durable home.** The scenario plan file for a decision local to one feature; an
   ADR when it outlives the feature; the commit message when it is about a bug just fixed.
   Those records are already written and **nobody has to keep them true** — they describe a
   moment, not current code.
2. **Move the argument there verbatim.** Do not compress it; the reasoning is worth keeping.
3. **Delete the doc block.** If something genuinely local survives — a fence against a future
   change, an accepted cost — keep only that sentence.
4. **If the argument is load-bearing at the call site**, it was a missing name or a missing
   test. Name the thing after the decision, or write the test that makes the alternative fail.

### Structure after refactoring

- Declarations carry doc blocks only where a fact outside the code's reach needs stating.
- The design argument is in a record that no maintainer has to keep in sync.
- Comment lines are a small fraction of code lines, in tests as well as in production.

### Tests

Pure documentation change; existing tests stay green. Where the deleted comment was standing in
for an untested rule, add the test — that is the only production-adjacent change this refactor
produces.

### Example

**boulder-friend, PR #19 (`filter-by-grade`)** — 369 of 942 production lines added were
comments (39%). `BoulderCatalogViewModel.kt` carried 103 comment lines to 91 code lines.

Its `selectedFilter` property was documented *"…lives here rather than in the screen so that
turning the phone leaves it alone."* Later in the **same pipeline run**, SCENARIO-14 established
that the view model is scoped to the navigator screen and that rotation survives only because
the Android manifest declares `configChanges`. The specification's own follow-up records that the
premise was "false as reasoned." The comment was never updated — no test could notice.

`BoulderCatalogScreenState.kt` was the extreme case: 39 comment lines to 16 code lines, arranged
as five consecutive doc blocks above one `data class`. In Kotlin only the last attaches, so three
of them documented nothing at all. Five reviewers over two rounds did not catch it, because it is
a syntactic defect and they were reading for meaning.
