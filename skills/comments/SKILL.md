---
name: comments
description: Use whenever writing or reviewing comments in production source. Defines which comments earn their place and which are liabilities, via a single falsifiability test. Stack-agnostic — examples are Kotlin, principles apply anywhere.
allowed-tools: Read, Glob, Grep
---

# Comments

Code is auto-explanatory or it is not finished. Tests document *what* the code must do; the
code documents *how*. A comment is only for a *why* the reader genuinely cannot reach — and
even then it is the weakest tool available, because nothing enforces it.

A comment cannot be run, cannot be asserted, and cannot fail. It drifts out of sync silently,
and a comment that has drifted does not merely stop helping — it lies, with the authority of
something a maintainer wrote on purpose.

## The test

Before writing any comment, ask:

> **Could this comment become false without a test going red?**
>
> **Yes** → it is a liability. Its size is the number of readers who will trust it.
> **No** — because what it describes is outside the code's reach — → it is carrying weight
> nothing else can. Write it.

Most comments you are about to write fail this test. That is the expected outcome.

## The four kinds

### 1. Earns its place — a fact the code cannot reach

Passes the test because nothing in the repository can contradict it:

- **External behaviour** you do not control — a vendor quirk, a platform bug, a protocol
  oddity, a library's undocumented contract.
- **A rejected alternative, and why.** A test proves what the code does; it can never say why
  the other option was worse. This is the single most valuable comment there is.
- **A fence** against a plausible future "improvement" that would break something subtle.
- **A cost knowingly accepted** — a slow path taken deliberately, with the reason.

```kotlin
/**
 * Deliberately **not** memoised: the bytes behind a boulder can change without the boulder
 * changing, which is exactly what replacing a photo in the setter's editor does.
 */
suspend fun photoBytes(boulderId: BoulderId): ByteArray?
```

Nothing in the codebase can make that false, and the next reader will otherwise "optimise" it.

### 2. A missing name

A comment translating what the next lines do. Fix by naming, not by writing. See the
*Comment as a missing name* catalog entry.

### 3. A rule a test already holds

A comment asserting behaviour that a named test enforces. Two copies of one specification,
one of them unenforced. Delete the comment; if the rule is untested, write the test instead —
the test name is the documentation and it fails when the rule changes. See the *Comment that
restates a test or cross-references foreign code* catalog entry.

### 4. A comment that argues — the one that slips through

**This is the failure mode to watch for, because it disguises itself as kind 1.**

Prose that re-derives the design decision the code already embodies:

- *"It lives here rather than in the screen because…"*
- *"It is carried rather than worked out from X because…"*
- *"This rides on `Success` rather than a variant of its own because…"*

It reads like a *why*, so it survives kinds 2 and 3. But it is not a why about an external
fact — it is a **transcript of the reasoning that produced the code**, addressed to a reviewer
who is no longer in the room. It fails the test outright: refactor the code and the argument
is stale, with nothing going red.

```kotlin
// BAD — argues, and is already false
/**
 * …lives here rather than in the screen so that turning the phone leaves it alone.
 */
private val selectedFilter = MutableStateFlow(CatalogFilter())
```

Real example. The same pipeline run that shipped this comment later established that the view
model is scoped to the *navigator screen*, and rotation survives only because the Android
manifest declares `configChanges`. The comment's reasoning was disproved by its own feature and
never updated, because no test could notice.

```kotlin
// BAD — argues, and narrates a bug already fixed
/**
 * A tap on a grade **toggles** it rather than only adding it: a selection that can only grow
 * can never widen the list again…
 */
fun onFilterIntent(intent: CatalogFilterIntent)
```

The method it documents calls `filter.toggling(...)`. The test is named
`a_tapped_in_grade_can_be_tapped_back_out`. The commit message says it. Four copies, one
enforced.

## Where the argument goes instead

The reasoning is worth keeping — it is just not source code's job:

| The thought | Where it belongs |
|---|---|
| Why this design over that one | the scenario plan file, or an ADR if it outlives the feature |
| What bug this shape prevents | the test name, plus the commit message |
| What the rule is | a named test |
| Why a *future* reader must not change this | a comment (kind 1 — a fence) |

Plan files and commit messages are already written, already durable, and **nobody has to keep
them true** — they are records of a moment, not claims about current code. Move the argument
there and the source keeps only what must stay accurate.

## Production vs tests — a hard carve-out

**This skill governs production source.** Test files are different and are not thinned by it.

A test's doc block routinely does something no production comment can: it names the specific
wrong implementation the test discriminates against, and the seed chosen to catch it.

```kotlin
/**
 * A grade-five boulder as well as a grade-three one, because a filter written as a comparison
 * rather than a membership — `grade <= FOUR` — is green against whichever side of grade four
 * is missing from the seed.
 */
```

That is a mutation proof, not narration. It is falsifiable by construction — weaken the test
and the stated mutant survives. Never delete it, and never apply the production rules to it.

## Mechanical rules

- **One doc block per declaration.** Consecutive doc blocks with no declaration between them
  are orphaned: in Kotlin only the last attaches, and the others are invisible dead text. If
  you are documenting several fields, document each on its own field.
- **Never repeat a comment.** The same explanation on two declarations in one file is two
  copies to drift. Put it on one and let the name carry the other.
- **No commented-out code.** Version control holds it.
- **A file where comments outnumber code is a design signal**, not a documentation
  achievement — the names are not carrying their weight.

## Reviewing

When you find a comment that fails the test, say which kind it is (2, 3 or 4) and what
replaces it — a name, a test, or a line in the plan file. "Delete this comment" without a
destination for the knowledge is how the argument gets lost.
