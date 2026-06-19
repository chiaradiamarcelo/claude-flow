## Verb-prefixed query methods (Command-Query naming)

### Smell
A side-effect-free method that returns a value carries a verb prefix that names *how* the answer is
produced — `calculate*`, `compute*`, `build*`, `derive*`, `resolve*`, `get*`. The name leaks the
implementation strategy (a calculation? a stored field? a cached lookup? an aggregation?) to every
caller. Code that reads the call site has to mentally translate the verb back into the noun the
method actually represents. If the implementation later changes (cached → recomputed, stored →
derived), the verb becomes a lie but renaming is now a breaking change for every caller.

The corollary: a method whose name reveals nothing about its implementation lets the implementation
evolve freely.

### Trigger
A method on an entity / value object / data structure has all of:
- no side effects, no `void` return, no thrown exception path that callers handle as control flow,
- input is only `this` state (or a small parameter that narrows what part of `this` to query),
- name starts with a verb such as `calculate`, `compute`, `build`, `derive`, `resolve`, `get`,
  `make`, `produce`,
- the noun the method returns is the entity's own concept (`statusLevel`, `total`, `summary`, …).

### Refactoring
1. Identify side-effect-free query methods on entities/value objects.
2. Strip the verb; the method becomes the noun it returns.
   `calculateStatusLevel()` → `statusLevel()`, `getTotalAmount()` → `totalAmount()`,
   `buildSummary()` → `summary()`.
3. If a `get*` prefix conveyed a meaningful nuance (collections often distinguish `findById` vs
   `getById` for null vs throw), keep the verb only when that distinction is part of the contract.
4. Mutations / commands / methods that throw on failure keep their verb prefix. The naming itself
   should make Command-Query Separation visible at the call site.

### Structure after refactoring
- Query methods read like properties: `order.totalAmount()`, `report.summary()`.
- Command methods keep verbs: `order.cancel()`, `report.markCompleted()`.
- Implementation can switch between stored field, cached property, and on-demand derivation without
  touching call sites.

### Tests
- Pure rename: existing tests update only the call site.
- No behavior change.

### Example (pseudocode)
```
# Before — the verb leaks "I am a calculation"
class Order
  computeTotal() -> Money
    sum each line item

caller:
  amount = order.computeTotal()

# After — the caller asks for the noun, the class chooses the strategy
class Order
  total() -> Money
    sum each line item

caller:
  amount = order.total()

# A later optimization can store `total` as a memoized field,
# fetch it from a precomputed projection, or recompute every call.
# The name does not change. Callers do not change.
```
