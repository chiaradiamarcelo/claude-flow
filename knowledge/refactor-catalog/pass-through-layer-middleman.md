## Pass-through Layer (Middleman)

### Smell

A class adds no behavior. It receives a call, hands it to its single collaborator, and returns
the result. Renaming arguments and return types is not behavior. The class exists only to
preserve symmetry with other layers ("every entity needs a Service and a UseCase"), or as a
speculative seam that never accumulated logic.

### Trigger

Any of these patterns is enough to flag:

1. A **use case** whose `run()` body is one port call and a `return`. No orchestration of multiple ports, no policy, no invariant checks.
2. A **service** that wraps a single repository method and forwards the call (`getUser(id)` → `userRepository.findById(id)`).
3. A **controller** whose handler calls another controller (or another service that does the same).
4. A class with **only one method**, doing **one delegation**, with no extra value at the call site.

### Refactoring

1. Identify the underlying collaborator the middleman forwards to.
2. Inject the collaborator directly at the call site (e.g., into the controller).
3. Delete the middleman class and its tests.
4. If the middleman was the only thing standing between two layers and the rename it performed had
   meaning, **rename the collaborator** instead of preserving the wrapper. (Example: a read-side
   port called `*Repository` whose only consumer was a pass-through UseCase — rename the port
   to `*Query`. See *Read-side port named "Repository"* below.)
5. Update tests to use the collaborator (or its fake) directly. Controller integration specs that
   previously mocked the middleman now drive the collaborator's fake via `seed(...)` / `failWith(...)`.

### Structure after refactoring

- One fewer layer between the controller (or other caller) and the collaborator.
- The collaborator's name carries the intent the middleman tried to convey.
- The fake for the collaborator is the seam the integration tests use.

### Tests

- Tests of the deleted middleman go away — they only proved the forward call worked.
- Tests of the caller (controller, etc.) now drive the collaborator's fake directly. The behavior
  surface they cover is unchanged; the level they assert at moves closer to the real boundary.

### When NOT to refactor

Keep the middleman only if it represents a **stable seam about to acquire policy** — e.g.,
authorization, caching, rate limiting, projection assembly — and that work is in flight or
imminent. Document the upcoming reason in the class header. Don't keep speculative seams "in
case" they grow.

### Example (pseudocode)

```
# Before — the use case is a one-line forward.
class ListActiveUsersUseCase
  ctor(owners: ActiveUsersPort)
  run() -> Result<list<UserId>, Failure>
    return this.owners.listActive()

class Controller
  ctor(listActive: ListActiveUsersUseCase)
  GET /active-users
    return await this.listActive.run()
```

```
# After — middleman deleted; controller injects the port directly.
class Controller
  ctor(activeUsers: ActiveUsersPort)
  GET /active-users
    return await this.activeUsers.listActive()
```

The controller integration test switches from mocking the use case to driving the fake of the
collaborator. The behavior covered is the same; the level moves closer to the real boundary.

See `~/.claude/skills/cqrs/SKILL.md` for the read-side variant of this smell (CQRS context).
