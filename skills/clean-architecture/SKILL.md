---
name: clean-architecture
description: Clean Architecture conventions — folder structure, dependency rules, design patterns, repository conventions, and code conventions. Invoke this skill when you need to know where layers live, what can import what, or how to structure production code.
---

## Folder structure

```
src/main/
  application/
    domain/          # Core entities and value objects
    usecase/         # Application use case orchestration
    port/            # Output port interfaces (repositories, external APIs)
  infrastructure/
    repository/      # Port implementations (adapters)
    config/          # Framework configuration and wiring
  api/
    controller/      # API controllers
    dto/             # Request/response DTOs
    mapper/          # DTO <-> domain/application mapping

src/test/
  application/
    usecase/         # Use case unit tests
    contract/        # Abstract contract tests for domain ports
    fakes/           # Fake implementations + their contract test subclasses
    domain/          # Tests for domain entities (only when combinatorial explosion justifies it)
  api/
    controller/      # API layer tests
  infrastructure/
    repository/      # Integration tests for real adapters + adapter contract test subclasses
```

### Contract test placement rule

Abstract contract tests live in `contract/`. Contract test *implementations* live next to their corresponding implementation:
- Fake's contract test → `fakes/` (next to the fake)
- Adapter's contract test → `infrastructure/repository/` (next to the adapter)

## Dependency rule (strict)

- **Domain** has zero framework dependencies. Pure language only. No framework annotations/imports.
- **Application** depends only on domain and ports defined within `application/port/`. No infrastructure or framework dependencies.
- **Infrastructure** depends on domain and application to implement ports.
- **API** depends on application (and shared DTO mapping), never on infrastructure internals.
- Dependencies always point inward.

## Design

- **Entities / Value Objects**: prefer immutability when possible; enforce invariants in constructors/factories.
  - Prefer returning new instances from mutation methods over mutating internal state. When framework constraints make this impractical (e.g., ORM-managed entities), mutation is acceptable but should be documented.
  - Entities with identity must implement equality based on their identity field(s).
  - Accessor methods: avoid `get` prefix. Use `accountId()` instead of `getAccountId()`, `balance()` instead of `getBalance()`.
  - Extract validation conditionals into intent-revealing private methods (e.g., `isNegative(amount)`, `exceedsLimit(amount)`) instead of inline comparisons.
- **Use cases**: one class per business action; orchestrate only. **Do not use interfaces for Use Cases**; use the concrete class directly.
- **Use cases vs infrastructure orchestration**: Not every "action" is a use case. If the class has no domain logic — only coordinates infrastructure concerns (HTTP fetch, file I/O, caching, scheduling) — it belongs in the infrastructure/data layer, not in domain/usecase. A true use case applies business rules (filtering, validation of domain invariants, policy decisions). Infrastructure orchestration (sync jobs, data migration, cache warming) lives in the data/infrastructure layer where it can freely use DTOs, serialization, and framework APIs. Placing infrastructure orchestration in the domain forces unnecessary ports/abstractions to avoid dependency rule violations.
- **No domain ports for infrastructure internals**: Do not create domain port interfaces for concerns that are purely infrastructure plumbing (e.g., JSON validation before writing, cache invalidation, file format checking). A domain port should answer: "Would a domain expert recognize this as something the business needs?" If no, it does not belong in the domain. However, data-layer interfaces are appropriate when the real implementation depends on a framework (SharedPreferences, HTTP, filesystem) and tests need a fake to avoid that dependency. Those interfaces live next to their consumers in the data layer, not in domain. Their fakes still need contract tests — if tests rely on a fake behaving correctly, that fake must be proven equivalent to the real implementation.
- **DTOs**: default to `api/dto/`; for small records with no behavior used by only one controller, keep them nested inside that controller.
- **Mappers**: isolate translations across layers.
- Use **ubiquitous language** from the current business domain; avoid generic names like `item`, `data`, `process`.

## Repository infrastructure conventions

- Implement an explicit adapter class to expose domain-oriented methods (`save`, `findAll`, `findById`, `delete`).
- Keep framework-specific repository interfaces internal to the adapter; use them as persistence primitives, not as domain API.
- Persist via dedicated persistence entities with explicit field mapping.
- Convert at boundaries: domain -> persistence entity in adapter, persistence entity -> domain in mapper method.
- Keep business invariants in domain, not in persistence entities.
- Keep adapter methods thin and intention-revealing; avoid leaking infrastructure internals.
- Validate schema compatibility in integration tests using migration tools and schema validation mode.
- **Every interface with a fake MUST have a contract test** — whether it's a domain port or a data-layer interface. If tests depend on a fake behaving like the real implementation, both must pass the same abstract contract test. This applies to domain ports (e.g., `FestivalRepository`) and data-layer interfaces alike (e.g., `SyncMetadataStore`).
- **Test adapters through their public interface.** An adapter may internally compose several classes (e.g., a sync job uses an HTTP client, a JSON parser, a file writer). Test the adapter through its public API — the port interface it implements — not by testing each internal collaborator independently. Extract and test an internal class separately only when combinatorial explosion makes testing through the public interface impractical. Internal classes that are only tested independently must remain `private` or `internal` — never promoted to domain ports just to make them testable.

## Code conventions

- No `I` prefix for interfaces.
- Prefer constructor injection over field injection.
- Keep domain and application framework-agnostic.
- Prefer explicit return types and clear method names.
- Use appropriate precision types for money/precision-sensitive values.
- Extract repeated constants into named constants.
- For input models, use `*Request` naming instead of `*Command`.
