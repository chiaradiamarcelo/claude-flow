# Refactor Catalog — index

A language- and codebase-independent catalog of code smells and the refactorings
that resolve them. **This index is the entry point: match an observed smell to a
row below, then read only that pattern's file** (e.g. `compose-method.md`) for the
full Smell / Trigger / Refactoring / Structure / Tests / Example. Each file is
self-contained; you never need to load the whole catalog.

## Patterns

| Pattern (file) | Smell signal — reach for it when… |
|---|---|
| [`specification-criterion-pattern.md`](specification-criterion-pattern.md) | A use case accumulates `if` branches deciding which records to keep, mixed with orchestration; every new filter rule edits the same use case. |
| [`anemic-domain-model-to-rich-model.md`](anemic-domain-model-to-rich-model.md) | Entities are pure data containers; business rules live in controllers, use cases, mappers, or `*Service`/calculator classes. |
| [`architecture-guardrail-sweep.md`](architecture-guardrail-sweep.md) | Code passes functional tests but the architecture drifts: blurred layers, validation duplicated across adapters and core, acceptance tests dropped from CI, policy hard-coded in use cases. |
| [`formatting-logic-in-domain-entities.md`](formatting-logic-in-domain-entities.md) | A domain entity carries display-formatting methods (`displayLabel()`, `formattedAddress()`, `shareText()`) that serve no invariant. |
| [`shotgun-surgery.md`](shotgun-surgery.md) | One conceptual change (add a param, rename a field) forces identical edits across many files/call sites. |
| [`duplicated-sealed-class-dispatch-composable.md`](duplicated-sealed-class-dispatch-composable.md) | A `when` over a sealed type is copy-pasted across composables, each rendering the same variants with the same params. |
| [`guard-clauses.md`](guard-clauses.md) | Nested `if/else` (or conditional local assignment) buries the happy path in indentation before the real work. |
| [`extract-named-conditions.md`](extract-named-conditions.md) | An inline boolean of low-level checks (`typeof`, `in`, `===`, `instanceof`) whose combined intent isn't obvious without reading every operand. |
| [`compose-method.md`](compose-method.md) | A long function mixes abstraction levels — low-level mechanics (parse, cast, null-check) alongside high-level decisions. |
| [`comment-as-a-missing-name.md`](comment-as-a-missing-name.md) | A comment translates *what* the next block, boolean, or value means — the comment is standing in for a missing name. |
| [`comment-that-restates-a-test-or-cross-references-foreign-code.md`](comment-that-restates-a-test-or-cross-references-foreign-code.md) | A comment restates a behavior already pinned by a test, or narrates how some *other* part of the codebase works. |
| [`comment-that-argues-the-design.md`](comment-that-argues-the-design.md) | A doc block on a declaration re-derives *why* the code is shaped this way. Reads like a legitimate *why*, so the two rows above miss it. |
| [`feature-envy-move-method.md`](feature-envy-move-method.md) | A method reads several fields of *another* type and contributes nothing of its own — `doX(other.a, other.b, other.c)`. |
| [`verb-prefixed-query-methods-command-query-naming.md`](verb-prefixed-query-methods-command-query-naming.md) | A side-effect-free, value-returning method has a verb prefix (`calculate*`, `compute*`, `build*`, `get*`) that leaks *how* the answer is produced. |
| [`pass-through-layer-middleman.md`](pass-through-layer-middleman.md) | A class adds no behavior — it receives a call, forwards to its single collaborator, and returns the result. |
| [`read-side-port-named-repository.md`](read-side-port-named-repository.md) | A `*Repository` whose only methods are read-shaped (`findAll`, `count`, `findBy*`, `list*`) — no `save`, no `delete`. |
| [`read-side-query-that-mirrors-the-aggregate-pass-through-view.md`](read-side-query-that-mirrors-the-aggregate-pass-through-view.md) | A `*Query`/`*View` duplicates the aggregate, reading the same row by the same key the Repository writes. |
| [`misplaced-projection-in-a-foreign-write-side-table-orphaned-ownership.md`](misplaced-projection-in-a-foreign-write-side-table-orphaned-ownership.md) | A read projection is materialized as a column on a foreign write-side table, refreshed by a service owning neither the source nor the sink. |

## Adding an entry

Add a new file here whenever a refactoring session surfaces a recurring smell not
yet listed, then add its row above. Include a concrete example from a real
codebase. Each file follows this structure:

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
