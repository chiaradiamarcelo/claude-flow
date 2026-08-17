## Comment that restates a test or cross-references foreign code

### Smell
A comment explains a *behavior* (not just what the next line mechanically does) that is **already
pinned by a test**, or it narrates **how some other part of the codebase works**. Two recurring
shapes:

1. **Restates a test.** A comment asserts a rule the code obeys — "only tracked crawlers count
   toward detected", "`chatgpt` aliases `gptbot` so it is excluded" — and a named test already
   locks that exact rule (`it('counts gptbot and chatgpt as one crawler')`). The test is the
   living specification: it fails when the behavior changes. The comment does not — it silently
   drifts until it is actively misleading. The behavior is now documented twice, and only one
   copy is enforced.
2. **Cross-references foreign code.** A comment describes a sibling/foreign module —
   "this is how we do it in the private-cache", "mirrors the throttling in the SQS consumer". It
   has no anchor: when the referenced code moves or changes, nothing here fails, so the note rots
   in place and sends the next reader to a description that no longer matches reality.

This is the layer beneath *Comment as a missing name*. There the fix was a better name; here the
comment may be a grammatically fine *what/why* sentence — it is redundant because the **test**
already says it, or unanchored because it points at **code this file does not own**.

### Trigger
You are reading a diff or a file and land on a comment where one of these is true:
- A test already exists (or obviously should) whose name is the same sentence as the comment. The
  `chatgpt`/`gptbot` alias comment is the canonical case — the test name *is* the documentation.
- The comment's subject is another file, module, or service, not the code it sits above.
- The comment explains the *consequence* of a rule ("so the alias is not double-counted") rather
  than an external fact the reader genuinely cannot infer (a vendor quirk, a worked-around bug,
  a ticket reference).

### Refactoring
1. **Restated by a test → delete the comment; make the test the documentation.** If the rule is
   not yet tested, write the test instead of the comment — the test name carries the explanation
   and enforces it. At most, leave a one-line pointer to the test when the rule is genuinely
   surprising at the call site (`// invariant pinned by AIDiscoverabilityKPIAdapter spec`); never
   re-explain the rule prose.
2. **Cross-reference → delete.** If two places must stay in lockstep, encode the link in *code*
   (a shared constant, a shared helper, a type) so a change forces both to move, or assert it in a
   test that touches both. A prose "see also" that nothing checks is worse than silence.
3. After the pass, every surviving comment answers "why this code at all" with a fact local to
   *this* file that no test could express: an external/vendor behavior, a deliberate trade-off, a
   ticket or contract reference. If a comment fails that test, the test suite (or a name) should
   carry it instead.

### Structure after refactoring
- Behavioral rules live in named tests; the code is free of prose that re-asserts them.
- No comment describes the internals of a module it does not own.
- Surviving comments are local *why*s about external facts — exactly the set *Comment as a
  missing name* also leaves standing.

### Tests
- Pure documentation change — existing tests stay green.
- Where a deleted comment described an *untested* rule, add the test that the comment was standing
  in for. That is the only production-adjacent change this refactor produces, and it strengthens
  the suite rather than just thinning comments.

### Example
**AI Discoverability KPI adapter (TypeScript)** — a block above the crawler-folding loop read
*"Only tracked crawlers count toward 'detected'. `chatgpt` aliases `gptbot` (same OpenAI bot) and
is excluded from `TRACKED_AI_CRAWLERS`, so …"*. Both sentences were already enforced by tests
(`it('counts gptbot and chatgpt as one crawler')` and the tracked-crawler filtering specs). The
comment was deleted: the test names are the specification, and unlike the comment they fail when
the aliasing rule changes. Surfaced in PR #3471 review.

The full doctrine — the falsifiability test and the four kinds of comment
— is in the `comments` skill (`~/.claude/skills/comments/SKILL.md`). This entry covers
kind 3. See *Comment that argues the design* for kind 4, which asserts no rule and restates no
test, so it passes both of this entry's triggers while still going stale.
