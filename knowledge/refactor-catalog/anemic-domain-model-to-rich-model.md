## Anemic domain model to rich model

### Smell
Domain entities/records are only data containers while business rules and state transitions live
elsewhere — most commonly in controllers, use cases, mappers, **or in standalone domain services
("calculators", "evaluators", "*Service" classes) that operate on a single domain type and hold no
state of their own**. Rules become duplicated, easy to bypass, and the entity carries values it
cannot defend.

A frequent variant in TDD/Clean-Architecture codebases:
- The entity is exported as `type X = { readonly a: A; readonly status: S; ... }`.
- A sibling file `XCalculator.ts` exports a free function `calculateStatus(parts): S` that
  derives one of `X`'s own fields from the others.
- Callers must remember to call the calculator; nothing prevents constructing an `X` whose
  `status` field disagrees with its `parts`.

### Trigger
The same domain rule appears in multiple places (for example create + update flows), or a new
behavior requires touching several orchestration classes to keep invariants consistent.

**Also trigger when** a standalone "Calculator", "Evaluator", "Resolver", or "*Service" file in the
domain layer:
- exports a single pure function (or a stateless class with one method),
- takes one domain type (or a tuple of its fields) as input,
- returns a value that *is, or directly derives,* one of that type's own fields, and
- has no second implementation, no port, and no collaborators.

That is an entity method masquerading as a service. The behavior belongs on the entity (constructor,
factory, or method) so the type cannot be constructed in an inconsistent state.

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
