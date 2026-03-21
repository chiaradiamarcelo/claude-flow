---
name: testing
description: Use whenever writing, modifying, or reviewing tests in this project. Defines the expected style for unit tests and API controller slice tests.
allowed-tools: Read, Write, Edit, Glob, Grep, Bash
---

## Test structure (mandatory)

Every test follows **Given-When-Then**.
Separate Given-When-Then with blank lines, without comments:

- Use the minimum fixture/input data needed to prove the behavior; remove extra records that do not affect the assertion.
- When a behavior can be proven with 1-2 domain values, do not use larger challenge/reference datasets in that test.
- Prefer semantic shared constants for recurring domain values in tests instead of ad-hoc literals.
- Setup method (e.g. `@BeforeEach`) is the mandatory place for instantiating fakes, use cases, and controllers. Never initialize them inline as field declarations. Declare the field without initialization and assign it in setup.
- Never seed test data (e.g. `repository.save(...)`, `fake.add(...)`) in setup — data setup must live inside each test method to keep tests readable and self-contained.

```pseudo
class CalculateOccupancyTest:

    test returns_expected_occupancy_when_capacity_is_available:
        repository = FakeGuestRepository([lowGuest, highGuest])
        useCase = CalculateOccupancy(repository)

        result = useCase.execute(request)

        assert result.totalAssignedRooms == 2
```

## Mandatory Review

**Every new or modified test must be reviewed by the `test-reviewer` agent.**

## Naming

- Domain/unit test class: `<ClassUnderTest>Test`.
- API controller slice test class: `<ControllerName>IT`.
- **Acceptance/Scenario tests**: Always use the **AT** suffix (example: `DepositMoneyScenarioAT`).
- Test method name: snake_case behavior style.
- camelCase test method names are not allowed.
- For failure scenarios, prefer `fails_when_<condition>` over `throws_when_<condition>`.
- Prefer `returns_<status>_when_<condition>` for API tests.
- Avoid implementation details in test names.

## Logic in Tests (Forbidden)

**Never use `if`, `else`, `for`, `while`, `switch`, or similar control flow in a test body.**
Tests must remain declarative and linear.

## Testing Strategy & Efficiency

**Prefer fast, economical, and deterministic tests.**
Before adding tests that use slow or non-deterministic dependencies (e.g., reading from disk, setting up environment variables, spinning up containers, performing HTTP requests, or hitting the network), ensure you have exhausted more efficient testing options.

Nearly everything can be verified in a fast, economical way through:
- **Unit Tests**: For domain logic when combinatorial complexity makes testing through the use case impractical. Otherwise, prefer testing domain logic through the use case.
- **Narrow Integration Tests**: Specifically for adapters (Controllers, Repositories) to verify the contract between your code and the immediate framework/infrastructure boundary.

This layered approach ensures the system is thoroughly tested while keeping the feedback loop fast.

## One behavior per test

Each test verifies one behavior. If a method name needs "and", split it.

## Fakes over mocks (default)

- **Mandatory fakes for external dependencies**: You MUST use hand-written fakes for infrastructure ports (repositories, external APIs) to ensure deterministic and fast tests.
- **Mocking Use Cases in API tests**: Using a mocking library to mock the Use Case in an API controller slice test is acceptable and standard.
- **Fakes must satisfy the contract**: Fakes MUST behave like real implementations for the tested contract and pass the same contract tests.
- Fakes must implement the same port interface as production adapters.
- **Every test starts from a clean slate — always in `@BeforeEach`, never in `@AfterEach` or `@AfterAll`.**
  - **Fakes**: create fresh instances in setup. No `clear()`/`reset()` methods.
  - **Database**: when constructing the connection/context is expensive, truncate or clear tables in `@BeforeEach` instead of recreating. But the cleanup always happens **before** each test, never after.

```pseudo
class FakeGuestRepository implements GuestRepository:
    guests: List<Guest>

    constructor(guests):
        this.guests = copyOf(guests)

    findAll() -> List<Guest>:
        return copyOf(guests)
```

## API controller tests (slice standard)

For controllers, use this baseline:

- Slice test annotation targeting the controller under test
- Injected test client
- Mocked use case dependency (mocking the use case here is acceptable)
- Request via test client
- Assert HTTP status first, then payload/headers when needed
- Verify delegation to the mocked use case/dependency

Success path example:

```pseudo
test returns_200_when_single_order:
    when(useCase.allOrders()).thenReturn([
        Order("id_1", date(2024, 1, 15), 99.99, "USD", SALE)
    ])

    response = client.get("/orders")

    assert response.status == 200
    assert response.body == [{ id: "id_1", date: "2024-01-15", amount: 99.99 }]
```

Validation path example:

```pseudo
test returns_400_when_missing_required_field:
    response = client.post("/orders", body: { amount: 99.99 })

    assert response.status == 400
    verifyNoInteractions(useCase)
```

## API validation matrix (what to cover)

For create/update endpoints, include explicit tests for:

- Happy path (`201` on create, `204` on update).
- Malformed input -> `400`.
- Type parsing errors -> `400`.
- Missing required fields -> `400`.
- Domain invariant violations -> `400`.
- Resource not found for update/delete/get -> `404`.
- Unexpected infrastructure/runtime failure path where applicable -> `500`.

## Validation source awareness

When designing 4xx tests, distinguish source of failure:

- Input parsing/deserialization failures (malformed input, invalid types) -> `400`.
- Domain constructor/factory invariant violations (null/blank required values) -> `400`.

## Repository integration tests (real DB, contract-style)

- Use framework-provided data layer test annotation.
- Talk to a real database (same engine as production or compatible equivalent).
- Keep DB schema managed by migration tools.
- Use schema validation mode to catch drift.

## Contract tests for ports

- Every domain port should have a contract test.
- Fake and real adapter implementations must satisfy the same contract.

## Public API & Logical Extraction

**Default**: the use case test is the primary entry point for verifying behavior. Test domain logic — including validation, invariants, and edge cases — through the use case, not through isolated domain entity tests. Domain entity tests are the **exception**, not the norm.

Do not widen visibility only for tests.

**Exception**: when a domain class (e.g. a value object or calculator) has enough variants that testing all combinations through the use case would require excessive boilerplate, extract it into a focused class and test that class directly. This must be justified by combinatorial complexity, not convenience.

## What to test

For **use cases/services**:
- Happy path
- Empty results
- Validation and edge cases
- Error handling

For **controllers**:
- Request validation
- Response codes and payload shape
- Header behavior when relevant
- Delegation target behavior and persisted object shape

For **mappers**:
- Field mapping correctness
- Value conversion correctness

## What NOT to test

- Private methods directly.
- Trivial getters/setters with no logic.
- Framework internals.
