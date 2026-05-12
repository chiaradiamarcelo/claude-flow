---
name: cqrs
description: CQRS conventions — when to split write side (Repository + UseCase) from read side (Query). Invoke when planning a new port, deciding whether a UseCase is needed, naming a port, shaping a read model, choosing where to place it, or evaluating whether a class is a pass-through middleman. Stack-agnostic — example is in Kotlin.
---

## When to invoke

Use this skill whenever you are:

- Planning a new port + UseCase (e.g. from an `architect` agent).
- Reviewing whether an existing class is a pass-through middleman (e.g. from a `refactor-advisor` agent).
- Naming a port (write side ⇒ `*Repository`; read side ⇒ `*Query`).
- Shaping a read model (what fields it carries, whether it has methods, where to put it).
- Deciding whether a controller should call a UseCase or inject a port directly.

## The split

|                                | Write side                                       | Read side                                  |
|--------------------------------|--------------------------------------------------|--------------------------------------------|
| What it does                   | Changes state                                    | Returns projections                        |
| Crosses a consistency boundary | Yes                                              | No                                         |
| Operates on aggregates         | Yes                                              | No                                         |
| Needs a UseCase                | Usually yes                                      | Usually no                                 |
| Port name                      | **`*Repository`**                                | **`*Query`**                               |
| Port methods                   | `save`, `findById`, `delete` (aggregate-shaped)  | `findAll`, `findBy*`, `count`, `list*`     |
| Folder placement               | `domain/models/<aggregate>/` (next to aggregate) | `domain/query/` (peer of `models/`)        |

## Folder placement (Vaughn Vernon-shaped)

```
domain/
  models/
    <aggregate>/                       # write side: one package per aggregate
      <Aggregate>.kt
      <ValueObject>.kt
      <DomainEvent>.kt
      <Aggregate>Repository.kt         # WRITE-side port lives WITH the aggregate
      <Aggregate>Repository.contract.kt
  query/                               # READ side: peer of models/
    <Topic>Query.kt
    <Topic>Query.contract.kt
    <Topic>View.kt                     # only when the read genuinely diverges (see Rule 5)
application/                           # UseCases — never *Service
  <Action>UseCase.kt
infrastructure/                        # adapters for both sides
  <Aggregate>PostgresAdapter.kt
  <Topic>QueryPostgresAdapter.kt
api/
  <Resource>Controller.kt
```

The write side is organized **by aggregate** (Vernon's per-aggregate packaging): the aggregate root, its value objects, its events, and its Repository port all live together because they share a consistency boundary. The read side is organized **by query topic** — projections don't have aggregate boundaries, so they don't get the same treatment.

**Do not** split as `read/` + `write/` peer folders. That suggests symmetric structures, but the two sides are asymmetric: write is aggregate-shaped, read is topic-shaped. Vernon explicitly avoids that split, and so should you.

## Rules

### 1. Repository is for the write side only

A `*Repository` port deals with **aggregates** — it loads them whole, mutates them, saves them whole, and is responsible for the consistency boundary that the aggregate enforces. If your "Repository" only has read methods (`findAll`, `count`, `findActive…`), it isn't a Repository — rename it to `*Query`.

The Repository interface **lives next to its aggregate** in `domain/models/<aggregate>/`. Vernon's canon: the Repository is part of the aggregate's contract, not a separate `port/` concept.

### 2. Read-side ports are named `*Query`

One name. Not `Finder`, `Reader`, `Report`, `Locator`, `Lookup`, or anything else. **`*Query`**. This keeps grep/autocomplete predictable across the codebase.

Examples: `DiscoverabilityStatusQuery`, `ActiveUsersQuery`, `OrderSummaryQuery`.

### 3. UseCases are for the write side

A UseCase orchestrates ports, applies policy, and protects invariants across multiple operations on aggregates. If your "UseCase" is one line that forwards to one port, it's a middleman — delete it.

**Naming:** the class name is `*UseCase`, never `*Service`. Vernon's "application services" are our UseCases; the rename reflects what the class actually is (one business action).

### 4. Pure reads plug directly into the controller

A controller injecting a `*Query` and calling `findAll()` (or similar) is fine. There's no aggregate, no consistency boundary, nothing for a UseCase to orchestrate. Only introduce a read-side UseCase when there's real logic on the way out (authorization, filtering, projection assembly, joining multiple sources). A read-side wrapper that just forwards is dead weight.

### 5. Don't introduce a Query when the read IS the aggregate by primary key

Before splitting, ask: **does the read shape diverge from the aggregate, or is it `{ ...aggregate, derivedProp: aggregate.method() }`?**

If the controller would load the same row, by the same key, that the Repository already loads — and the only "extra" the read needs is calling the aggregate's own derivation methods (`statusLevel()`, `triggers()`, `total()`) — **don't introduce a `*Query`**. You'd be paying for a parallel read model, a real adapter, a fake, a contract spec, and a mapper that all duplicate the Repository's behavior with renamed fields.

Instead:
- Keep one `*Repository` with `save` + `findByX` (returning the aggregate — Rule 1 allows this; loading aggregates whole is what Repositories do).
- Inject the Repository directly in the controller (Rule 4 applies — no UseCase to orchestrate).
- Let the HTTP DTO mapper call `aggregate.derivedProp()` inline. This is the explicit exception to Rule 6 ("read model carries no derivation"): when there is no read model, there's nothing to violate. The aggregate is the data shape; the DTO mapper is the projection.

**Split into a `*Query` when the read genuinely diverges:**
- Filters on columns the aggregate doesn't carry (`WHERE status = 'critical'` over many rows wants a denormalized indexed column).
- Joins across aggregates (`OrderSummaryView { order, customerName, lineItemCount }`).
- Pagination / list shapes (`PageOf<UserListItem>`).
- Projection-only data (counts, sums, denormalized facts).
- Read load that would benefit from eager pre-computation at write time.

**Smell:** you wrote a `*Query` port whose `View` is `{ ...aggregate, derivedA: aggregate.derivedA(), derivedB: aggregate.derivedB() }` and whose adapter reads the same single row, by the same primary key, that the Repository writes. That's a pass-through middleman. Collapse it — keep the Repository, drop the Query.

### 6. The read model is pure data — no methods, no derivation

When the read side is split (Rule 5 didn't apply), the read model is a flat projection shaped for the consumer. It carries `readonly` fields and **nothing else**. No `statusLevel()`, no `isCritical()`, no `triggers()`, no `total()`. If the value can be derived, derive it **at the adapter (or on the write side) and store it in the read model**, not at request time in the controller or a mapper.

**Why:** the whole point of a separate read model is to skip work. Deriving on every read defeats it and re-implements rules already enforced on the write side. The read adapter projects once; everything downstream is pass-through.

**Smell:** the read controller imports functions like `statusLevelFor(view)` or `triggersFor(view)` and calls them inline. Push that derivation into the adapter (or precompute on the write side and store it).

### 7. Read models carry stable identifiers, not presentation labels

Ship internal IDs (`gptbot`, `claudebot`), enum values, ISO timestamps — things that don't change when marketing renames a product or the UI redesigns. The view layer (frontend) maps stable identifiers to display labels.

**Why:** keeps the backend stable across product naming changes, keeps a single source of truth for display vocabulary on the frontend, and avoids FE↔BE drift.

### 8. Read model file placement

Default: read models (`*View`) live in `domain/query/` next to the Query interface that returns them. **Do not put a read model inside an aggregate's package** — Vernon: read models are not part of the aggregate's contract.

**Vocabulary types** (enums, value objects used by both sides — e.g. `StatusLevel`) stay at the shared `domain/models/` root, not nested under an aggregate folder.

### 9. Read-side controller pattern

```kotlin
val result = someQuery.findByX(...) // Result<View?, Failure>
when (result) {
  is Failure -> throw InternalServerErrorException(cause = result.failure)
  null       -> throw NotFoundException("...")
  else       -> toResponseDto(result.value)
}
```

- Failure first, then null/missing, then map.
- `toResponseDto` is a near pass-through: serialization concerns only. No derivation (Rule 6).

### 10. Read-side fake conventions

Every `*Query` port ships with a fake that exposes:
- `seed(...)` — populate the underlying store with a ready view.
- `failWith(failure)` — force the next call to return a failure result.

This makes the fake the test seam for read-side controllers (no UseCase mock needed) and gives integration specs a clean way to exercise both success and failure paths.

### 11. Contract tests are mandatory for every port

Each port has a `*.contract.*` file next to it that exports a reusable suite. Every adapter (the fake, the real Postgres/ClickHouse/etc. adapter) calls the suite from its own spec. The contract file is excluded from direct test runs; it's invoked indirectly through the implementation specs. This guarantees adapters stay behaviorally interchangeable.

## Litmus test

When you see a class on the application or controller side, ask:

- *Does it do anything besides forward to one port call?*
- *Is the data it returns part of an aggregate that needs a consistency boundary on write?*

If both answers are **no**, delete the class and inject the port directly. If the port is read-only, rename it to drop the `Repository` suffix — use `Query`.

When you see a read model, ask:

- *Does it equal `{ ...aggregate, derivedProp: aggregate.method() }` and is its query a primary-key lookup against the same row the Repository writes?* (It probably shouldn't exist — see Rule 5. Drop the Query, drop the View, use the Repository.)
- *Does it have methods?* (It shouldn't.)
- *Does anyone compute derived values from it at request time?* (Nobody should — derive at the adapter.)
- *Does it carry display strings, formatted dates, or other presentation concerns?* (It shouldn't — ship stable identifiers and ISO timestamps.)

## Example

```kotlin
// Before — the UseCase is a one-line forward; the port is named "Repository" but reads only.

class ListActiveUsersUseCase(private val owners: IntegratedDomainOwnersRepository) {
  fun run(): Result<List<UserId>, LookupFailure> =
    owners.listActiveUserIds()
}

interface IntegratedDomainOwnersRepository {
  fun listActiveUserIds(): Result<List<UserId>, LookupFailure>
}

class ActiveUsersController(private val listActiveUsers: ListActiveUsersUseCase) {
  fun activeUserIds(): Response =
    when (val r = listActiveUsers.run()) {
      is Failure -> Response.status(500)
      is Success -> Response.ok(mapOf("userIds" to r.value))
    }
}
```

```kotlin
// After — UseCase deleted; port renamed to *Query; controller injects the port directly.

interface ActiveUsersQuery {
  fun findAll(): Result<List<UserId>, LookupFailure>
}

class ActiveUsersController(private val activeUsers: ActiveUsersQuery) {
  fun activeUserIds(): Response =
    when (val r = activeUsers.findAll()) {
      is Failure -> Response.status(500)
      is Success -> Response.ok(mapOf("userIds" to r.value))
    }
}
```

The controller's integration spec drives the real `FakeActiveUsersQuery` via `seed(...)` / `failWith(...)` — the Query *is* the seam now, no UseCase mock.

## Cross-references

- Skill: `clean-architecture` — Vernon-shaped folder layout and dependency rules. This skill is the read/write complement explaining when a UseCase is *not* required and how the read model should be shaped/placed.
- Skill: `testing` — read-side controller tests drive the real fake of the Query (with `seed(...)` / `failWith(...)`), not a UseCase mock; the contract spec is the conformance check shared by every adapter.
