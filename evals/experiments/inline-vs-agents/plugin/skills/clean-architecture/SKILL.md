---
name: clean-architecture
description: Clean Architecture conventions — Vaughn Vernon-shaped folder structure (aggregate-per-package on the write side, peer query/ folder on the read side, application/ holding UseCases not Services), dependency rules, design patterns, repository conventions, and code conventions. Invoke this skill when you need to know where layers live, what can import what, or how to structure production code.
---

## Folder structure (Vaughn Vernon-shaped)

Aggregate-centric on the write side, peer `query/` folder on the read side. Application layer holds **UseCases** (never `*Service` classes).

```
<service-or-bounded-context>/
  domain/
    models/
      <aggregate>/                          # one package per aggregate root (Vernon)
        <Aggregate>.kt                      # aggregate root
        <ValueObject>.kt                    # VOs + entities owned by the aggregate
        <DomainEvent>.kt                    # events emitted by this aggregate
        <Aggregate>Repository.kt            # WRITE-side port lives WITH its aggregate
        <Aggregate>Repository.contract.kt   # contract every adapter must pass
        fakes/
          Fake<Aggregate>Repository.kt
      <SharedValueObject>.kt                # vocabulary types used by multiple aggregates
    query/                                  # READ side, peer of models/ (NOT a /read & /write split)
      <Topic>Query.kt                       # read-side port
      <Topic>Query.contract.kt
      <Topic>View.kt                        # read model — only when the read genuinely diverges
      fakes/
        Fake<Topic>Query.kt
  application/                              # UseCases (NOT *Service)
    <Action>UseCase.kt                      # orchestrates one business action across aggregates
  infrastructure/                           # adapter implementations (write + read together)
    <Aggregate>PostgresAdapter.kt
    <Topic>QueryPostgresAdapter.kt
    config/                                 # framework wiring
  api/                                      # delivery layer
    <Resource>Controller.kt
    dto/
      <Action>Request.kt
      <Resource>Response.kt
```

### Why this shape

- **Aggregate-per-package** is Vernon's IDDD canon: an aggregate's root, its value objects, its domain events, and its Repository port live together because they share a consistency boundary and change together. Putting them in flat `entities/` / `valueObjects/` / `ports/` buckets fragments cohesive concepts.
- **Repository lives WITH the aggregate**, not in a separate `port/` folder. The Repository's job is to load and save the aggregate whole — it's part of the aggregate's contract.
- **`query/` is a peer of `models/`**, not a `read/` paired with a `write/`. The write side organizes by aggregate; the read side organizes by query topic. They're asymmetric on purpose — projections don't have aggregate boundaries.
- **`application/` holds UseCases**, not Vernon's "application services." We use the name *UseCase* because that's what the class is: one business action, one class, no service-layer indirection.
- **`infrastructure/` holds both write- and read-side adapters.** No further split — `*RepositoryAdapter` and `*QueryAdapter` can sit side by side. The naming tells you which side.

### Contract test placement

The contract spec (the abstract behavioral suite) lives **next to the port**, in the same folder as the port interface — `<Topic>Query.contract.kt` next to `<Topic>Query.kt`, `<Aggregate>Repository.contract.kt` next to the aggregate.

Each implementation's spec runs the contract:
- Fake's spec → in `fakes/` next to the fake
- Real adapter's spec → in `infrastructure/` next to the adapter (often as `*.integration.spec.kt`)

The contract file itself is excluded from direct test runs; it executes via the implementation specs.

## Dependency rule (strict)

- **Domain** has zero framework dependencies. Pure language only. No framework annotations/imports. Ports (Repository interfaces under `domain/models/<aggregate>/`, Query interfaces under `domain/query/`) are part of the domain.
- **Application** depends on `domain/` only — the aggregates and the ports defined inside it. No infrastructure or framework dependencies.
- **Infrastructure** depends on domain (to implement ports) and may depend on application (to wire it). All adapters live here.
- **API** depends on application + domain (for DTO mapping from aggregates / read models), never on infrastructure internals.
- Dependencies always point inward (api → application → domain; infrastructure points inward by implementing domain ports).
- **One aggregate package never imports from another aggregate package.** Each `domain/models/<aggregate>/` owns its root, value objects, events, and Repository. Cross-aggregate vocabulary (shared value objects, IDs that travel between aggregates) lives in `domain/models/` at the bounded-context root — *not* inside any one aggregate. Cross-aggregate orchestration belongs in a UseCase under `application/`, which takes both aggregates' Repositories as constructor dependencies. The same rule applies to read-side ports: a Query in `domain/query/` is owned by its topic, and one Query never imports from another Query's folder — if two Queries share types, promote them to `domain/query/` at the root or to `domain/models/`. Cross-importing between sibling aggregate packages is the smell: it leaks the consistency boundary and nothing in the layout warns you about it.
- **Use cases never import from another use case's folder.** When a feature is sliced into multiple use cases (e.g. `feature/use-cases/<use-case>/`), each use case owns its own `domain/`, `adapters/`, and orchestration class. If two use cases need the same port, fake, contract, or domain model, promote it to a feature-level `shared/` folder (e.g. `feature/shared/domain/ports/`, `feature/shared/domain/models/`) and have both use cases import from there. Cross-importing between sibling use cases (`../other-use-case/domain/ports/X`) is the smell — it bakes in a coupling that nothing in the architecture enforces and that future readers can't infer from the folder names.

## Design

- **Entities / Value Objects**: prefer immutability when possible; enforce invariants in constructors/factories.
  - Prefer returning new instances from mutation methods over mutating internal state. When framework constraints make this impractical (e.g., ORM-managed entities), mutation is acceptable but should be documented.
  - Entities with identity must implement equality based on their identity field(s).
  - Accessor methods: avoid `get` prefix. Use `accountId()` instead of `getAccountId()`, `balance()` instead of `getBalance()`.
  - Extract validation conditionals into intent-revealing private methods (e.g., `isNegative(amount)`, `exceedsLimit(amount)`) instead of inline comparisons.
- **UseCases (not Services)**: one class per business action; orchestrate only. **Do not use interfaces for UseCases**; use the concrete class directly. The class name is `*UseCase` — never `*Service`. Vernon's "application services" are our UseCases; the rename reflects what the class actually is (one business action, not a grab-bag service object).
- **UseCases vs infrastructure orchestration**: Not every "action" is a UseCase. If the class has no domain logic — only coordinates infrastructure concerns (HTTP fetch, file I/O, caching, scheduling) — it belongs in the infrastructure/data layer, not in `application/`. A true UseCase applies business rules (filtering, validation of domain invariants, policy decisions across aggregates). Infrastructure orchestration (sync jobs, data migration, cache warming) lives in `infrastructure/` where it can freely use DTOs, serialization, and framework APIs. Placing infrastructure orchestration in `application/` forces unnecessary ports/abstractions to avoid dependency rule violations.
- **Write side vs. read side (CQRS).** A UseCase orchestrates writes (commands that change state through aggregates with consistency boundaries). **Pure reads don't need a UseCase** — the controller may inject the read-side port (`*Query`) directly. **Repository naming is reserved for write-side aggregates**; read-side ports are named **`*Query`** (one name — not Finder/Reader/Report). Repository interfaces live next to their aggregate in `domain/models/<aggregate>/`; Query interfaces live in the peer `domain/query/` folder. Only introduce a read-side UseCase when there's real logic on the way out (authorization, filtering, projection assembly). See the `cqrs` skill for the full rules, the "don't split when the read IS the aggregate" guidance, and the litmus test.
- **No domain ports for infrastructure internals**: Do not create domain port interfaces for concerns that are purely infrastructure plumbing (e.g., JSON validation before writing, cache invalidation, file format checking). A domain port should answer: "Would a domain expert recognize this as something the business needs?" If no, it does not belong in the domain. However, data-layer interfaces are appropriate when the real implementation depends on a framework (SharedPreferences, HTTP, filesystem) and tests need a fake to avoid that dependency. Those interfaces live next to their consumers in the data layer, not in domain. Their fakes still need contract tests — if tests rely on a fake behaving correctly, that fake must be proven equivalent to the real implementation.
- **DTOs**: default to `api/dto/`; for small records with no behavior used by only one controller, keep them nested inside that controller.
- **Mappers**: isolate translations across layers.
- Use **ubiquitous language** from the current business domain; avoid generic names like `item`, `data`, `process`.

## Adapter infrastructure conventions (Repository + Query)

- Implement an explicit adapter class per port. A `*RepositoryAdapter` (write side) exposes aggregate-shaped methods: `save`, `findById`, `delete`. A `*QueryAdapter` (read side) exposes projection-shaped methods: `findAll`, `findBy*`, `count`, `list*`. Don't mix the two on one adapter.
- Keep framework-specific persistence interfaces internal to the adapter; use them as persistence primitives, not as domain API.
- Persist via dedicated persistence entities with explicit field mapping.
- Convert at boundaries: domain → persistence entity in adapter, persistence entity → domain (or read model) in a mapper method.
- Keep business invariants in domain (the aggregate), not in persistence entities or read models.
- Keep adapter methods thin and intention-revealing; avoid leaking infrastructure internals.
- Validate schema compatibility in integration tests using migration tools and schema validation mode.
- **Every interface with a fake MUST have a contract test** — whether it's a domain port (Repository / Query) or a data-layer interface. If tests depend on a fake behaving like the real implementation, both must pass the same abstract contract test.
- **Test adapters through their public interface.** An adapter may internally compose several classes (HTTP client, JSON parser, file writer). Test the adapter through its public API — the port interface it implements — not by testing each internal collaborator independently. Extract and test an internal class separately only when combinatorial explosion makes testing through the public interface impractical. Internal classes that are only tested independently must remain `private` or `internal` — never promoted to domain ports just to make them testable.

## Code conventions

- No `I` prefix for interfaces.
- Prefer constructor injection over field injection.
- Keep domain and application framework-agnostic.
- Prefer explicit return types and clear method names.
- Use appropriate precision types for money/precision-sensitive values.
- Extract repeated constants into named constants.
- For input models, use `*Request` naming instead of `*Command`.
