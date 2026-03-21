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
    contract/        # Contract tests for domain ports
    fakes/           # Fake implementations for tests
    domain/          # Tests for domain entities (e.g., value object equality)
  api/
    controller/      # API layer tests
  infrastructure/
    repository/      # Integration tests for real adapters
```

## Dependency rule (strict)

- **Domain** has zero framework dependencies. Pure language only. No framework annotations/imports.
- **Application** depends only on domain and ports defined within `application/port/`. No infrastructure or framework dependencies.
- **Infrastructure** depends on domain and application to implement ports.
- **API** depends on application (and shared DTO mapping), never on infrastructure internals.
- Dependencies always point inward.

## Design

- **Entities / Value Objects**: immutable where possible; enforce invariants in constructors/factories.
- **Use cases**: one class per business action; orchestrate only. **Do not use interfaces for Use Cases**; use the concrete class directly.
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

## Code conventions

- No `I` prefix for interfaces.
- Prefer constructor injection over field injection.
- Keep domain and application framework-agnostic.
- Prefer explicit return types and clear method names.
- Use appropriate precision types for money/precision-sensitive values.
- Extract repeated constants into named constants.
- For input models, use `*Request` naming instead of `*Command`.
