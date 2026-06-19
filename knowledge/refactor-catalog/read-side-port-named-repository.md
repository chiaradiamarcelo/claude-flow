## Read-side port named "Repository"

### Smell

A port called `*Repository` whose only methods are read-shaped: `findAll`, `count`, `findBy*`,
`list*`. No `save`, no `delete`, no aggregate-shaped operations. The "Repository" suffix promises
a consistency boundary the port doesn't actually enforce.

**Not a smell:** a Repository with **both** `save` *and* a `findByX` that loads the aggregate
whole by its identity. Loading aggregates is part of a Repository's job (Vernon). The smell is
purely read-only ports that borrow the Repository name.

### Trigger

You review a port's surface area and notice every method is a read, no method changes state.
The port doesn't load aggregates for mutation and doesn't participate in any write transaction.
It exists purely to answer queries.

### Refactoring

1. Rename the port from `*Repository` to **`*Query`** (one name — not Finder/Reader/Report; this
   project standardizes on `*Query` for every read-side port).
2. Rename the symbol/injection token to match (`*_REPOSITORY` → `*_QUERY`).
3. Rename the method if `Repository`-style verb prefixes leaked in (`listActiveUserIds` →
   `findAll` if the port is the active-users query).
4. Move the port file from `domain/models/<aggregate>/` (write-side location) to `domain/query/`
   (read-side peer folder). Read-side ports don't belong inside an aggregate's package.
5. Update the adapter's `implements` clause and its method body — body usually doesn't change,
   only the method name and signature.
6. Update fakes (rename file, class, method).
7. Update the contract test (rename function, file). The scenarios stay.
8. Often co-occurs with *Pass-through Layer (Middleman)* — when you remove a pass-through UseCase
   from above the read-side port, the rename happens in the same refactor.

### Structure after refactoring

- Port named `*Query`, located in `domain/query/`.
- Symbol named `*_QUERY`.
- Controllers (or other application-layer callers) can inject the query directly per the CQRS
  convention.

### Tests

- Contract tests rename but keep the same scenarios.
- Adapter integration test renames its `describe` heading and the contract-invocation function.
- Fake spec renames the file and contract import.
- No behavioral change.

### Example (pseudocode)

```
# Before
interface IntegratedDomainOwnersRepository
  listActiveUserIds() -> Result<list<UserId>, LookupFailure>

token INTEGRATED_DOMAIN_OWNERS_REPOSITORY
```

```
# After
interface ActiveUsersQuery
  findAll() -> Result<list<UserId>, LookupFailure>

token ACTIVE_USERS_QUERY
```

The adapter's `implements` clause changes from the old name to the new one; the body of the
read method is unchanged.

See `~/.claude/skills/cqrs/SKILL.md` for the write/read split rationale.
