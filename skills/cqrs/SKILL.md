---
name: cqrs
description: CQRS conventions — when to split write side (Repository + UseCase) from read side (Finder / Query / Reader / Report). Invoke when planning a new port, deciding whether a use case is needed, naming a port, or evaluating whether a class is a pass-through middleman. Stack-agnostic — example is in Kotlin.
---

## When to invoke

Use this skill whenever you are:

- Planning a new port + use case (e.g. from the `architect` agent).
- Reviewing whether an existing class is a pass-through middleman (e.g. from the `refactor-advisor` agent).
- Naming a port: deciding between `*Repository`, `*Finder`, `*Query`, `*Reader`, `*Report`.
- Deciding whether a controller should call a use case or inject a port directly.

## The split

|                                | Write side                                       | Read side                                  |
|--------------------------------|--------------------------------------------------|--------------------------------------------|
| What it does                   | Changes state                                    | Returns projections                        |
| Crosses a consistency boundary | Yes                                              | No                                         |
| Operates on aggregates         | Yes                                              | No                                         |
| Needs a use case               | Usually yes                                      | Usually no                                 |
| Port name                      | **Repository**                                   | **Finder / Query / Reader / Report**       |
| Port methods                   | `save`, `findById`, `delete` (aggregate-shaped)  | `findAll`, `findBy*`, `count`, `list*`     |

## Rules

1. **Repository is for the write side only.** A `*Repository` port deals with **aggregates** — it loads them whole, mutates them, saves them whole, and is responsible for the consistency boundary that the aggregate enforces. If your "repository" only has read methods (`findAll`, `count`, `findActive...`), it isn't a repository — rename it. Use **Finder**, **Query**, **Reader**, or **Report** instead.

2. **Use cases are for the write side.** A use case orchestrates ports, applies policy, and protects invariants across multiple operations. If your "use case" is one line that forwards to one port, it's a middleman — delete it. See the *Pass-through Layer (Middleman)* entry in the refactor catalog.

3. **Pure reads may be plugged directly into the controller.** A controller injecting a `*Finder` and calling `findAll()` is fine. There's no aggregate, no consistency boundary, nothing for a use case to orchestrate. Only introduce a read-side use case when there's actual logic on the way out (authorization, filtering, projection assembly, joining multiple sources).

4. **Naming the method.** Methods on a finder/query are search-shaped: `findAll`, `findById`, `findByStatus`, `count`, `list`. Don't borrow `save` / `delete` for reads.

## Litmus test

When you see a class on the application or controller side, ask:

- *Does it do anything besides forward to one port call?*
- *Is the data it returns part of an aggregate that needs a consistency boundary on write?*

If the answer to both is **no**, delete the class and inject the port directly. If the port is read-only, rename it to drop the `Repository` suffix.

## Example

```kotlin
// Before — the use case is a one-line forward; the port is named "Repository" but reads only.

class ListActiveUsersUseCase(private val owners: IntegratedDomainOwnersRepository) {
    fun run(): Result<List<UserId>, LookupFailure> =
        owners.listActiveUserIds()
}

interface IntegratedDomainOwnersRepository {
    fun listActiveUserIds(): Result<List<UserId>, LookupFailure>
}

class ActiveUsersController(private val listActiveUsers: ListActiveUsersUseCase) {
    fun activeUserIds(): Response = when (val result = listActiveUsers.run()) {
        is Failure -> Response.status(500)
        is Success -> Response.ok(mapOf("userIds" to result.value))
    }
}
```

```kotlin
// After — use case deleted; port renamed to Finder; controller injects the port directly.

interface ActiveUsersFinder {
    fun findAll(): Result<List<UserId>, LookupFailure>
}

class ActiveUsersController(private val activeUsers: ActiveUsersFinder) {
    fun activeUserIds(): Response = when (val result = activeUsers.findAll()) {
        is Failure -> Response.status(500)
        is Success -> Response.ok(mapOf("userIds" to result.value))
    }
}
```

The controller's integration spec switches from mocking the (now-deleted) use case to driving the real `FakeActiveUsersFinder` via its `seed(...)` / `failWith(...)` convenience methods — because the finder *is* the seam now.

## Cross-references

- Refactor catalog → **Pass-through Layer (Middleman)** (layer smell, multiple triggers).
- Refactor catalog → **Read-side port named "Repository"** (naming smell).
- Skill: `clean-architecture` (folder structure, layer dependencies) — does **not** mandate a use case for reads; this skill is the read-side complement.
- Skill: `testing` — read-side controller tests drive the real fake of the finder (with `seed(...)` / `failWith(...)`), not a use-case mock.
