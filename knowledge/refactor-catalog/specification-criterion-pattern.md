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
