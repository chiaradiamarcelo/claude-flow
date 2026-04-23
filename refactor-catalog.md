# Refactor Catalog

A language- and codebase-independent catalog of code smells and the refactorings that resolve
them. Each entry follows the same structure so the refactor-advisor agent can match a smell it
observes against a known pattern and propose the appropriate fix.

Add a new entry whenever a refactoring session surfaces a recurring smell that is not yet listed.
Include a concrete example from the current codebase.

---

## Entry format

```
## <Pattern name>

### Smell
What the bad code looks like and why it hurts.

### Trigger
The specific moment when the smell becomes undeniable (usually: "we had to add a second/third X").

### Refactoring
Step-by-step transformation from the smelly code to the clean design.

### Structure after refactoring
The types / abstractions that emerge and their responsibilities.

### Tests
How to test the result. What the test suite looks like after the refactoring.

### Example
Pointer to a real codebase where this was applied.
```

---

## Specification (Criterion) pattern

### Smell
A use case or service accumulates `if` branches to decide which records to keep, mixed with
orchestration logic (loading data, sorting, pagination). Every new filter rule modifies the same
use case.

### Trigger
A second independent filtering rule is added. Inline conditionals grow and changes keep hitting a
class that should be stable.

### Refactoring
1. Extract a `Criterion<T>` interface with one method: `boolean matches(T item)`.
2. Implement one class per business rule. Each class owns only the data it needs.
3. Introduce a `Query` object that bundles criteria plus sorting/paging inputs.
4. Rewrite the use case pipeline:
   - caller builds criteria list from current request/state
   - use case delegates to repository with `Query`
   - repository (or use case) applies `criteria.stream().allMatch(c -> c.matches(item))`
5. New rule = new `Criterion` class; existing use case code stays unchanged.

### Structure after refactoring
- `Criterion<T>` interface
- One `*Criterion` class per rule
- `Query` value object (`List<Criterion<T>>`, sort/pagination hints)
- Use case focused on orchestration
- Caller (controller/application service) assembles the query

### Tests
- Unit tests per criterion: `true`, `false`, and edge-case behavior.
- Use case tests verify orchestration wiring, not rule internals.
- Caller tests verify query assembly from request/state.

### Example
**Allocation API**
Filtering candidates by threshold, date window, and status.
- `AllocationCriterion` with `ThresholdCriterion`, `DateRangeCriterion`, `StatusCriterion`
- `AllocationQuery(criteria, sortOrder)` passed to allocation use case
- Controller/application layer builds criteria from request filters
- After refactor: use case remains stable while rules evolve independently

---

## Anemic domain model to rich model

### Smell
Domain entities/records are only data containers while business rules and state transitions live in
controllers, use cases, or mappers. Rules become duplicated and easy to bypass.

### Trigger
The same domain rule appears in multiple places (for example create + update flows), or a new
behavior requires touching several orchestration classes to keep invariants consistent.

### Refactoring
1. Identify domain invariants and behaviors currently implemented outside the domain.
2. Move invariant enforcement into constructors/factories/value objects.
3. Move business operations into domain methods instead of rebuilding raw objects in controllers.
4. Keep controllers/use cases focused on orchestration (I/O, lookup, transaction boundaries).
5. Replace primitive parameters with value objects when rules are non-trivial.
6. Keep only simple mapping/transport concerns outside the domain.

### Structure after refactoring
- Entities/value objects own invariants and behavior.
- Use cases orchestrate collaborators, not business calculations/rules.
- Controllers map external input/output only.
- Invalid states become unrepresentable or fail fast at domain boundaries.

### Tests
- Domain tests validate invariants and business transitions directly.
- Controller/use case tests assert orchestration and status mapping, not duplicated rules.
- Add regression tests proving rules cannot be bypassed through different entry points.

### Example
**Order CRUD API**
- Keep required-field and currency invariants in the domain entity.
- Prefer adding domain behaviors when business rules grow, rather than spreading logic
  across create and update controllers.
- Keep API tests focused on contract and delegation; keep domain rule details in domain tests.

---

## Architecture guardrail sweep

### Smell
Code passes functional tests but the architecture starts drifting: layer boundaries blur, validation
is duplicated across adapters and core, acceptance tests stop running in CI, and business policy is
hard-coded in use cases.

### Trigger
A review finds that behavior is correct today, but extension risk rises because the next rule change
would require touching multiple layers or changing core code for policy-only updates.

### Refactoring
1. Run a focused review pass with these rules:
   - layer dependency boundaries (no inward leaks from adapters/frameworks)
   - validation ownership and consistency (single authoritative boundary per invariant)
   - test lifecycle coverage (unit + integration + acceptance wired intentionally)
   - policy configurability (hard-coded thresholds/tiers extracted behind config/policy objects)
2. Classify findings by severity (`VIOLATIONS`, `WARNINGS`, `GOOD PRACTICES`) to prioritize work.
3. Refactor only the highest-impact guardrail breaks first, preserving behavior with regression
   tests.
4. Encode recurring findings in catalog entries so future reviews are faster and consistent.

### Structure after refactoring
- Clear adapter/application/domain boundaries with explicit dependency direction.
- Invariants enforced once at a deliberate boundary, with adapters mapping errors consistently.
- CI lifecycle intentionally includes the chosen test layers.
- Business policy represented as configurable input or dedicated policy abstraction.

### Tests
- Keep use case tests for rule behavior.
- Keep controller tests for API contract and validation mapping.
- Ensure acceptance tests are either wired in CI or explicitly documented as manual.
- Add regression tests when moving validation/policy ownership to prevent behavioral drift.

### Example
**Hotel Room Allocation API**
- Validation overlap found between controller input validation and domain constructor.
- Acceptance test exists but is excluded from CI lifecycle.
- Premium threshold is hard-coded in use case instead of being configurable.

---

## Formatting logic in domain entities

### Smell
A domain entity contains methods that format data for display (e.g., `displayLabel()`,
`formattedAddress()`, `shareText()`). These methods assemble human-readable strings using
domain fields but serve no domain invariant or business rule. They couple the domain to
presentation concerns — locale, label conventions, abbreviation rules — that change for
UI reasons, not business reasons.

### Trigger
A second display context appears (e.g., a share sheet alongside a detail screen) that needs
a different format from the same entity. The entity accumulates formatting variants, or the
same conditional logic (e.g., which address field to prefer) appears in multiple methods.

### Refactoring
1. Identify methods on domain entities that produce display strings (not enforce invariants).
2. Create a `*TextFormatter` object or class in the presentation layer.
3. Move the formatting methods to the formatter as static/companion functions that take the
   entity as a parameter: `OrderTextFormatter.summaryLine(order)`.
4. Extract shared derivation logic as a private helper inside the formatter.
5. Update all call sites in presentation/ViewModel code.
6. Move tests from the domain test directory to a presentation test directory.

### Structure after refactoring
- Domain entity: only invariant enforcement, domain queries, and equality. Zero string
  formatting.
- `*TextFormatter` in presentation: owns all display-string assembly. One place to change
  when label conventions evolve.
- Dependency direction preserved: formatter depends on domain, not the reverse.

### Tests
- Formatter tests live in the presentation test directory, exercising each formatting method
  with boundary inputs (missing optional fields, equal fields, differing fields, etc.).
- Domain entity tests only cover invariants and domain behavior.
- All existing assertions are preserved — only the call site changes.

### Example
**E-commerce order system**
`Order.summaryLine()`, `Order.shippingLabel()`, and `Order.receiptText()` were display-string
methods on the domain entity. Moved to `OrderTextFormatter` in the presentation layer. The
`recipientName()` helper became a private function in the formatter. Domain `Order` retained
only `total()`, `isShippable()`, and invariant enforcement.

---

## Shotgun surgery

### Smell
A change to one concept (adding a parameter, renaming a field, changing a type) requires
identical edits in many files. The knowledge of how to construct or configure that concept is
spread across every call site instead of living in one place.

Common forms:
- The same constructor call (with the same arguments) is copy-pasted across 5+ test methods or
  multiple test files.
- A data class gains a field and dozens of call sites need updating.
- A factory or formatter is instantiated inline in every ViewModel test with identical config.

### Trigger
A signature change touches 3+ files with identical edits, or you find yourself doing
find-and-replace across test files to add the same parameter everywhere.

### Refactoring
1. **Before the feature change**, scan call sites for the constructor/method being modified.
2. If 3+ sites use identical construction, extract a shared helper first:
   - Test fixtures: `aFestival(...)`, `testCardFormatter()`, `successState()`
   - Test render helpers: `renderDetailScreen(uiState = ...)`
   - Production factories: Koin module, companion factory method
3. Verify all tests still pass (the extraction is a pure refactor — no behavior change).
4. **Then** make the actual feature change — it lands in one place (the helper), not N call sites.

"Make the change easy (this might be hard), then make the easy change." — Kent Beck

### Structure after refactoring
- One shared helper/fixture per repeated construction pattern.
- Call sites specify only what differs from defaults.
- Adding a new parameter to the underlying constructor requires editing one helper, not N files.

### Tests
- The extraction step is green-to-green: all existing tests pass before and after.
- The feature change modifies only the helper — existing tests continue to pass or fail based
  on their own assertions, not on incidental constructor noise.

### Example
**WaWo Android app**
`FestivalCardFormatter(untilTemplate = "Bis %s", endsTodayLabel = "Endet heute")` was
constructed identically in 6 ViewModel test files. Adding `festivalImage` required touching
all 6. Extracted `testCardFormatter()` fixture — the `festivalImage` parameter change became
a one-liner.

---

## Duplicated sealed-class dispatch composable

### Smell
A `when` block that dispatches on a sealed class/interface is copy-pasted across multiple
composable functions. Each copy renders the same variants with the same parameters (image URL,
placeholder resource, content scale, error drawable) but in a slightly different modifier
context. Adding a new variant or changing shared behavior (e.g., adding a `placeholder`
parameter to `AsyncImage`) requires identical edits in every copy.

### Trigger
The same sealed-class `when` dispatch appears in 3+ composable files, or a change to one
variant (e.g., adding an error-placeholder to `Remote`) must be replicated across all copies.

### Refactoring
1. Extract a shared `@Composable` function that takes the sealed type and a `Modifier`,
   dispatches via `when`, and renders each variant.
2. The shared composable owns all variant-specific details (placeholder drawable, content
   description, content scale default).
3. Replace every inline `when` block with a call to the shared composable, passing only the
   sealed value and the caller-specific modifier.
4. If a caller needs a non-default `contentScale`, expose it as an optional parameter with a
   sensible default.

### Structure after refactoring
- One `FestivalImageView(source: FestivalImageSource, modifier, contentScale)` composable in
  `presentation/common/`.
- Callers pass `source` + `modifier` only.
- Adding a new `FestivalImageSource` variant compiles-fails in one place, not N.

### Tests
- Existing Compose UI tests continue to pass unchanged (the extraction is a pure refactor).
- No new unit tests needed — the shared composable is a thin rendering wrapper, tested
  transitively by each screen's UI tests.

### Example
**WaWo Android app**
`when (imageSource) { Remote -> AsyncImage(...); Placeholder -> Image(...) }` was duplicated
in `FestivalSearchCard`, `FestivalDetailHeroSection`, `FestivalMapInfoSheet`, and
`HomeScreen`. Extracted to `FestivalImageView` in `presentation/common/`. All four callers
now delegate to the shared composable. Adding `placeholder = painterResource(...)` to the
`Remote` branch required changing one file instead of four.

---

## Guard clauses

### Smell
A function uses nested `if/else` blocks or assigns to a local variable through conditional
branches before reaching the "real work." The happy path is buried inside indentation, and
the reader must mentally track which conditions lead to which outcomes. Error/edge-case
handling is interleaved with the main logic instead of being dispatched up front.

### Trigger
A function has 2+ levels of nesting for validation or precondition checks, or the main
logic is inside an `if` block whose `else` is an error/throw.

### Refactoring
1. Identify each precondition or invalid-state check in the function.
2. Invert the condition and return/throw immediately (early exit).
3. Remove the `else` branch — the rest of the function *is* the happy path.
4. The function now reads top-down: guards first, then linear main logic at the base
   indentation level.

### Structure after refactoring
- Each guard clause is a one-liner `if (!condition) throw/return`.
- Guards appear at the top of the function in order of cheapest-to-check first.
- The main logic follows at the same indentation level — no nesting.

### Tests
- No behavioral change — tests remain green throughout.
- Each guard maps to a test that triggers that specific early exit.

### Example
**Diagnostics report schema versioning (TypeScript)**
`parseDiagnosticsReportEnvelope` originally used nested `if/else` blocks to validate the
parsed JSON. Refactored to sequential guard clauses:
```typescript
if (!isPlainObject(parsed))           throw new Error(MALFORMED);
if (!hasNumericSchemaVersion(parsed))  throw new Error(MALFORMED);
if (isCurrentSchemaVersion(parsed))    return extractV1UserAgents(parsed);
throw new UnsupportedSchemaVersionError(parsed.schemaVersion);
```
Each line is a self-contained decision. The function reads as a checklist.

---

## Extract named conditions

### Smell
A boolean expression appears inline in an `if` statement or ternary. The expression uses
low-level checks (`typeof`, `in`, `===`, `instanceof`) whose combined intent is not obvious
without reading every operand. Readers must reverse-engineer what the condition *means* from
how it is *computed*.

### Trigger
An `if` condition spans multiple lines, combines 2+ operators, or requires a comment to
explain its purpose. Or the same compound check appears in more than one place.

### Refactoring
1. Extract the condition into a named function or variable whose name states the business
   or structural intent (e.g., `hasNumericSchemaVersion`, `isExpired`, `isEligibleForDiscount`).
2. Use a type-narrowing return type when the language supports it (TypeScript `is`, Kotlin
   smart cast) so subsequent code benefits from the narrowed type.
3. Replace the inline expression with a call to the named function.
4. If the condition is used once and is short, a `const` with a descriptive name is sufficient;
   a function is preferred when type narrowing is needed or when reuse is likely.

### Structure after refactoring
- Each `if` reads as a domain/structural assertion: `if (!isPlainObject(parsed))`.
- Named predicates live as private helpers near the function that uses them.
- Type guards carry narrowing information so callers don't need follow-up casts.

### Tests
- Pure refactor — existing tests stay green.
- If the extracted predicate is non-trivial, consider a focused unit test.

### Example
**Diagnostics report schema versioning (TypeScript)**
```typescript
// Before
if (!('schemaVersion' in record) || typeof record.schemaVersion !== 'number') { ... }

// After
function hasNumericSchemaVersion(
  record: Record<string, unknown>,
): record is Record<string, unknown> & { schemaVersion: number } {
  return 'schemaVersion' in record && typeof record.schemaVersion === 'number';
}
if (!hasNumericSchemaVersion(parsed)) { ... }
```
The `if` now reads as a structural assertion. The type narrowing flows into subsequent code.

---

## Compose method

### Smell
A function is long and mixes multiple levels of abstraction: low-level mechanics (parsing,
casting, null-checking) alongside high-level decisions (dispatching on a version, selecting
a strategy). The reader must constantly shift mental gears between *what* the function does
and *how* it does each step. The function is hard to scan because the outline (the sequence
of steps) is buried in implementation details.

### Trigger
A function exceeds ~15 lines, or you can identify 2+ distinct "phases" within it (validate,
transform, dispatch) that each involve their own low-level logic.

### Refactoring
1. Identify the high-level steps the function performs (e.g., parse → validate → dispatch).
2. Extract each step into a named private function whose name describes *what* it does, not
   *how*: `extractV1UserAgents(record)`, `assertWellFormed(condition)`.
3. The composed function becomes a short sequence of calls at a single level of abstraction —
   a table of contents for the algorithm.
4. Each extracted function owns one concern and can be understood independently.
5. Keep extracted helpers private/local unless reuse is proven.

### Structure after refactoring
- The public function reads like pseudocode: 5–10 lines, each a named step.
- Private helpers contain the mechanical details (type checks, casts, error construction).
- Each helper has a clear input → output contract.

### Tests
- No behavioral change — existing tests stay green.
- Helpers are tested indirectly through the composed function; extract a dedicated test only
  when a helper has complex branching worth pinning independently.

### Example
**Diagnostics report schema versioning (TypeScript)**
`parseDiagnosticsReportEnvelope` was refactored from a single function with inline validation
and extraction into a composed method:
```typescript
export function parseDiagnosticsReportEnvelope(json: string): UserAgentChecks {
  const parsed: unknown = JSON.parse(json);
  if (!isPlainObject(parsed))            throw new Error(MALFORMED);
  if (!hasNumericSchemaVersion(parsed))   throw new Error(MALFORMED);
  if (isCurrentSchemaVersion(parsed))     return extractV1UserAgents(parsed);
  throw new UnsupportedSchemaVersionError(parsed.schemaVersion);
}
```
Each helper (`isPlainObject`, `hasNumericSchemaVersion`, `isCurrentSchemaVersion`,
`extractV1UserAgents`) owns a single concern. The main function is a readable checklist.
