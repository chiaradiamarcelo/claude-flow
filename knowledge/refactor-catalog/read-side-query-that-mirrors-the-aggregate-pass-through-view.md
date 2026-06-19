## Read-side Query that mirrors the aggregate (pass-through View)

### Smell

A `*Query` port returns a `*View` whose shape is `{ ...aggregate, derivedProp: aggregate.method() }`,
and its adapter reads the same single row, by the same primary key, that the Repository writes.
The View duplicates the aggregate's fields and the only "extra" is materializing the aggregate's
own derivation methods as properties. The split adds a parallel read model, a real adapter, a fake,
a contract spec, and a mapper — all behaving identically to the Repository read with renamed fields.

This is the read-side counterpart of *Pass-through Layer (Middleman)*: instead of an extra class
between layers, it's an extra port between the controller and the same data the Repository already
exposes.

### Trigger

Any of:

- The `*View` type's fields equal `aggregate`'s fields plus methods-as-properties
  (`view.status = aggregate.statusLevel()`, `view.triggers = aggregate.triggers()`).
- The `*QueryAdapter` reads the same table, by the same primary key (`user_id`, `order_id`, …)
  that the `*RepositoryAdapter` writes.
- The controller would work identically if it injected the Repository and called
  `findByUserId(...)`, then projected the aggregate via the DTO mapper.

### Refactoring

1. Add `findByX(...)` to the `*Repository` interface, returning the aggregate (Vernon: Repositories
   load aggregates whole by identity).
2. Implement `findByX` on the `*RepositoryAdapter` (often a one-line knex/sql query).
3. Update the HTTP DTO mapper to take the aggregate (not the View) and call the aggregate's
   derivation methods (`aggregate.statusLevel()`, `aggregate.triggers()`) inline at projection
   time.
4. Update the controller to inject the Repository and call `findByX(...)`. Map null → 404.
5. Delete the `*Query` port, its `*View` model, its contract spec, its fake, and its Postgres
   (or other) adapter.
6. Delete any failure types that were only consumed by the Query (`*LookupFailure`) — unless
   the Repository also needs them.

### Structure after refactoring

- One port (`*Repository`) for the aggregate, with both `save` and `findByX`.
- One adapter.
- One fake.
- One contract spec, exercising the roundtrip.
- HTTP DTO mapper runs derivation methods on the aggregate inline.

### Tests

- Repository contract gains the `findByX` scenarios (returns aggregate; returns null when absent;
  per-user isolation).
- The old Query contract scenarios disappear; their coverage is subsumed by the Repository
  contract.
- Controller integration spec switches from `FakeQuery.seed(view)` to
  `fakeRepository.save(aggregate)`. The HTTP response assertions stay — the projection still
  produces the same payload.

### When NOT to refactor (when to keep the Query split)

Keep the Query split when the read genuinely diverges from the aggregate:

- Filters on columns the aggregate doesn't carry (`WHERE status = 'critical'` over many rows —
  wants a denormalized indexed column).
- Joins across aggregates (`OrderSummaryView { order, customerName, lineItemCount }`).
- Pagination / list shapes (`PageOf<UserListItem>`).
- Projection-only data (counts, sums, denormalized facts).
- Read load heavy enough that eager pre-computation at write time pays off.

If none of those apply, the Query is a middleman — collapse it.

### Example (pseudocode)

```
# Before — Query reads the same row the Repository writes, returns a View
# that just lifts the aggregate's methods into properties.

interface DiscoverabilityStatusQuery
  findByUserId(userId) -> Result<DiscoverabilityStatusView?, LookupFailure>

type DiscoverabilityStatusView = {
  status: aggregate.statusLevel()    # derived
  triggers: aggregate.triggers()     # derived
  evaluatedAt
  domains: aggregate.domainIssues    # renamed
}

class Controller(query: DiscoverabilityStatusQuery)
  GET /status -> toResponseDto(query.findByUserId(...).value)
```

```
# After — Query / View / QueryAdapter / FakeQuery / Query-contract all deleted.
# Repository has both save and findByUserId; DTO mapper takes the aggregate.

interface DiscoverabilityStatusRepository
  save(status)
  findByUserId(userId) -> DiscoverabilityStatus?

class Controller(repo: DiscoverabilityStatusRepository)
  GET /status:
    let s = repo.findByUserId(...)
    if s == null: 404
    return { status: s.statusLevel(), triggers: s.triggers(), evaluatedAt: s.evaluatedAt, domains: s.domainIssues }
```

See `~/.claude/skills/cqrs/SKILL.md` Rule 5 — *Don't introduce a Query when the read IS the
aggregate by primary key* — for the underlying convention.
