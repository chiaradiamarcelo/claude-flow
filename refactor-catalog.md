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
