## Comment as a missing name

### Smell
A comment explains *what* the next block of code does, the meaning of a boolean expression, or
the role of a value. The code itself is mechanical; the comment is the translation key. Readers
have to keep both the code and the comment in their head, and the comment drifts out of sync
as the code changes.

This is distinct from a *why* comment (a non-obvious constraint, an external bug being worked
around, a deliberate divergence from a contract). *Why* comments survive refactoring; *what*
comments are usually a missing name in disguise.

### Trigger
You are about to type `// ` to explain:
- what the next 3–10 lines do,
- what a boolean expression represents in business language,
- why a magic number was chosen,
- which "phase" of a function is starting (`// validate`, `// transform`, `// dispatch`).

Or you are reading code where each block is preceded by such a comment and the function reads
like a heavily annotated script.

### Refactoring
1. For each *what* comment, ask: would a named variable or function replace it?
2. **Comment over a value or expression → Extract Variable.** Replace
   `// retention check\nif (date.before(now.minusDays(plan.retentionDays)))` with
   `const isWithinRetention = ...; if (isWithinRetention)`. Drop the comment.
3. **Comment over a block → Extract Method.** Replace
   `// fold rows into per-window totals\nfor (...) { ... }` with `const summary = summarize(rows)`.
   Drop the comment. (See *Compose method* for the multi-step variant.)
4. **Magic number with `// 16 = paddingXS`** → either substitute the token directly, or extract
   a `const TOKEN_PADDING_XS = 16` with a single-line comment if no real token is reachable.
5. After extraction, the surviving comments should all answer "why this code at all" —
   external behavior we work around, deliberate trade-offs, references to a ticket or contract.
   If you can't answer "why", delete the comment.

### Structure after refactoring
- The function body reads top-to-bottom as named steps and named expressions.
- Surviving comments are short, sit on a single helper, and explain a non-obvious *why*.
- Block comments that summarize the next N lines are gone — they were a missing function name.

### Tests
- Pure refactor — existing tests stay green.
- Named extractions can occasionally be unit-tested if they encode a non-trivial rule worth
  pinning on its own (rare; usually they stay private and are exercised through the caller).

### Example
**AI Discoverability KPI adapter (TypeScript)**

Before — block comments narrate each step:
```ts
async findKPIs(request) {
  // ...
  try {
    // run the consolidated analytics query plus the postgres total-pages lookup
    const [analytics, totalPages] = await Promise.all([...]);

    // fold per-crawler rows into the high-level numbers used by the KPI builders
    let distinctCrawlersCurrent = 0;
    let ...
    for (const row of analytics.data) { ... }

    // we have comparable history iff earliest activity exists and predates dateFrom
    const hasHistoryBeforeCurrentWindow = earliestActivity !== null && earliestActivity < dateFrom;

    // ClickHouse returns min(time) over no rows as '1970-01-01' — treat as null
    const earliestActivity = ...;
    // ...
  }
}
```

After — names carry the explanation; the only surviving comment is the *why* about ClickHouse:
```ts
async findKPIs(request) {
  // ...
  const [analytics, totalPages] = await Promise.all([...]);

  const summary = summarize(analytics);
  const hasHistory = hasHistoryBefore(summary.earliestActivity, dateFrom);

  return Ok({
    crawlersDetected: crawlersDetectedFrom(summary, hasHistory),
    pageCoverage:     pageCoverageFrom(summary, totalPages, hasHistory),
    errorRate:        errorRateFrom(summary, hasHistory),
  });
}

// ClickHouse returns min(time) over no rows as '1970-01-01 00:00:00' rather than NULL.
function parseEarliestTime(value: string | null | undefined): Date | null { ... }
```

The `summarize`, `hasHistoryBefore`, and three `*From` helpers replaced four blocks of narrating
comments. The remaining comment on `parseEarliestTime` survives because it documents
external ClickHouse behavior the reader cannot infer from the code.

See also *Compose method* for the case where the smell is a single long function with multiple
phases that each deserve their own extracted helper.
