## Feature envy → Move method

### Smell
A function or method reads multiple fields of *another* type and contributes nothing of its own.
It "envies" the other type's data — every call looks like `doX(other.a, other.b, other.c)` or
`doX(other, extraArg)`. The function lives in module scope (or in a different class) only because
the type started life as a plain data bag.

The visible cue: a free function whose first parameter is `summary`, `report`, `order`, `user`,
etc., and whose body reads ≥2 fields of that parameter to produce a derived value. If you ask
"could this method live on the data?" and the answer is "yes, nothing would be lost", the data
is the natural owner.

### Trigger
The moment of recognition is much earlier than the obvious "three free functions in a row"
signal. Every time you operate on data that belongs to someone else — reading two or more
fields of another object to compute or decide something — pause and ask whether that owner
should hold the behavior instead. Waiting for the obvious signal means fixing scattered code,
not avoiding it.

**The point is coupling, not aesthetics.** When the rule lives with the data, changing the
data shape (or the rule) is a single-file edit and the blast radius is bounded. When the rule
lives elsewhere, every change ripples — every function signature carries the data type, every
call site selects the right free function, every new rule adds a new function and threads it
through every caller.

Concrete questions to ask at the moment of writing:
- Am I reading two or more fields of the same parameter to derive my output?
- If that parameter's shape later changes (rename, split, new invariant), how many call sites
  break? More than one means the rule is on the wrong side of the line.
- Could a caller construct that parameter with values that contradict what I'm about to
  derive? If yes, the derivation belongs in the type's constructor or methods so the
  contradiction becomes unrepresentable.

The late, undeniable signals — two or three `do(thing, ...)` functions in a row; the type
exported as a plain record with no methods; call sites that read as `doX(thing, extras)`
instead of `thing.x(extras)` — are confirmations that you missed the early trigger, not the
trigger itself.

### Refactoring
1. Convert the plain data type into a class (or, in functional codebases, a module-level
   namespace that owns the operations and a factory).
2. Make the constructor private; expose a named static factory (`fromAnalytics`, `fromRequest`,
   `parse`) that performs whatever construction logic was previously in a free function. This
   blocks callers from constructing the type in an inconsistent state.
3. Move each "envious" function onto the class as a method. Drop the leading `<data>:` parameter
   — `this` is the data now. Other parameters that come from elsewhere (request-time inputs,
   cross-cutting context) stay as method parameters.
4. Where multiple related fields always travel together (current/previous windows, request/response
   sides), bundle them into a small inner record so the class isn't a flat heap of `*Current` /
   `*Previous` fields. Symmetry that exists in the domain should be visible in the type.
5. The orchestrator that used to thread the data through free functions now reads as a sequence
   of method calls on a single object.

### Structure after refactoring
- A class (or namespaced module) holding the data + the methods that derive from it.
- Private constructor + named static factory; callers cannot bypass invariants.
- Methods are short and self-contained — each derived value has one place to look.
- The orchestrator (use case / adapter / controller) shrinks: composition lives at the call site
  via method calls, not via free-function plumbing.

### Tests
- Pure refactor — existing tests stay green.
- If the new class encodes non-trivial rules (constructor invariants, derived methods that
  branch), unit-test it directly. The orchestrator's tests usually need no changes; they were
  already exercising the rules indirectly.

### Example
**AI Discoverability KPI adapter (TypeScript)**

Before — three free functions that all envy `Summary`:
```ts
type Summary = {
  distinctCrawlersCurrent: number;
  distinctCrawlersPrevious: number;
  totalRequestsCurrent: number;
  errorRequestsCurrent: number;
  totalRequestsPrevious: number;
  errorRequestsPrevious: number;
  trackedSeenInCurrent: ReadonlySet<TrackedAICrawler>;
  distinctCrawledPagesCurrent: number;
  distinctCrawledPagesPrevious: number;
  earliestActivity: Date | null;
};

function summarize(analytics): Summary { ... }
function hasHistoryBefore(earliest, boundary): boolean { ... }
function crawlersDetectedFrom(summary, hasHistory) { ... }
function pageCoverageFrom(summary, totalPages, hasHistory) { ... }
function errorRateFrom(summary, hasHistory) { ... }

// findKPIs:
const summary = summarize(analytics);
const hasHistory = hasHistoryBefore(summary.earliestActivity, dateFrom);
return {
  crawlersDetected: crawlersDetectedFrom(summary, hasHistory),
  pageCoverage:     pageCoverageFrom(summary, totalPages, hasHistory),
  errorRate:        errorRateFrom(summary, hasHistory),
};
```

After — data and behavior together, current/previous bundled into `WindowMetrics`:
```ts
type WindowMetrics = {
  distinctCrawlers: number;
  totalRequests: number;
  errorRequests: number;
  distinctCrawledPages: number;
};

class DiscoverabilityKPISummary {
  static fromAnalytics(analytics): DiscoverabilityKPISummary { ... }
  private constructor(
    private readonly current: WindowMetrics,
    private readonly previous: WindowMetrics,
    private readonly trackedSeenInCurrent: ReadonlySet<TrackedAICrawler>,
    private readonly earliestActivity: Date | null,
  ) {}

  hasHistoryBefore(boundary: Date): boolean { ... }
  crawlersDetected(hasHistory: boolean): CrawlersDetectedKPI { ... }
  pageCoverage(totalPages: number, hasHistory: boolean): PageCoverageKPI { ... }
  errorRate(hasHistory: boolean): ErrorRateKPI { ... }
}

// findKPIs:
const summary = DiscoverabilityKPISummary.fromAnalytics(analytics);
const hasHistory = summary.hasHistoryBefore(dateFrom);
return {
  crawlersDetected: summary.crawlersDetected(hasHistory),
  pageCoverage:     summary.pageCoverage(totalPages, hasHistory),
  errorRate:        summary.errorRate(hasHistory),
};
```

The orchestrator becomes a table of contents; the rules live on the data; the private
constructor blocks inconsistent states. Symmetry between current and previous is now visible
in the type (`WindowMetrics` × 2) rather than buried in pairs of `*Current` / `*Previous`
fields.

See also *Anemic domain model to rich model* — feature envy is the lightweight, module-local
sibling of the same idea applied to domain entities. Same fix shape (move behavior to the
data); different scope.
