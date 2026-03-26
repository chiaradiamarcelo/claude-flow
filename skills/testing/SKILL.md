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
- Test method name: snake_case behavior style.
- camelCase test method names are not allowed.
- For failure scenarios, prefer `fails_when_<condition>` over `throws_when_<condition>`.
- Prefer `returns_<status>_when_<condition>` for API tests.
- Avoid implementation details in test names.

## Logic in Tests (Forbidden)

**Never use `if`, `else`, `for`, `while`, `switch`, `forEach`, or similar control flow in a test body.**
Tests must remain declarative and linear. If branching appears necessary, split scenarios or redesign setup.

## One behavior per test

Each test verifies one behavior. If a method name needs "and", split it.

## Assertions

- Prefer the project's assertion library for consistent style.
- For comparisons, prefer `assertThat(actual).isEqualTo(expected)` style or equivalent.
- **Precision-sensitive values**: MUST use comparison methods that ignore scale/representation differences.
- Flag mixed assertion styles when a single style can keep tests consistent.
- Avoid magic numbers; use named constants/fixtures where meaning matters.
- **No redundant intermediate assertions**: do not assert a precondition that is already tested implicitly by the next assertion. For example, asserting `isPresent()` before accessing `.get()` is redundant if the next line asserts a property of the unwrapped value — the test will fail anyway if the value is absent.

## Test data minimality

- Each test should use the smallest input/fixture set that still proves the behavior.
- Oversized datasets when fewer values/records would assert the same rule are a violation.
- Large reference/challenge datasets are a violation unless the scenario explicitly validates that exact dataset.
- Repeated raw domain literals should use shared constants when values recur across tests.

## Repeated construction = extract a helper

- When the same constructor call (domain object, formatter, factory, ViewModel, or UI state) appears identically in 3+ test methods or across 2+ test files, it must be extracted into a shared fixture builder or test helper.
- This applies to production object construction in tests (e.g., `FestivalCardFormatter(...)`, `HomeSectionsFactory(...)`, `toSuccess(...)`) — not just domain fixtures.
- The helper absorbs incidental parameters (like test fakes) so tests only specify what matters for their scenario.
- When a new parameter is added to a shared constructor, update the helper — never patch individual call sites.

## Test data visibility

- **All test data referenced in assertions must be visible in the test body.** Class-level fields that build test data (e.g., `private val remoteJson = aFestivalJson(...)`) and are used implicitly by tests are a violation. The reader should not need to scroll to class fields to understand what a test asserts. Pass data explicitly via the setup helper or use named constants.
- **Don't test return types that are internal signals.** If a return type (e.g., `SyncResult.Success`) is only consumed internally — not by presentation or UI — don't write tests that only assert on it. The behavioral tests (e.g., "festivals updated") already prove success.
- **"Unchanged" assertions must use distinct before/after values.** When a test asserts "data unchanged after operation," the local and remote data must have visibly different identifiers. If both happen to have the same ID, the test passes vacuously even if the wrong data is returned.

## Test behavior, not library boundaries

- **When a library implements your product behavior, the behavior is still yours to test.** The library is an implementation detail, not an excuse to skip testing. "Show a fallback when the image fails to load" is product behavior whether Coil, Glide, or hand-written code implements it.
- **If a behavior is hard to test, restructure the code for testability first.** Most "untestable" behaviors are a design signal, not a tooling limitation.
- **Delete vacuous tests.** A test that passes regardless of whether the code is correct is worse than no test — it gives false confidence. If you can't make a test fail by removing the behavior, delete it.

## Testing Strategy & Efficiency

**Prefer fast, economical, and deterministic tests.**
Before adding tests that use slow or non-deterministic dependencies (e.g., reading from disk, setting up environment variables, spinning up containers, performing HTTP requests, or hitting the network), ensure you have exhausted more efficient testing options.

Nearly everything can be verified in a fast, economical way through:
- **Unit Tests**: For domain logic when combinatorial complexity makes testing through the use case impractical. Otherwise, prefer testing domain logic through the use case.
- **Narrow Integration Tests**: Specifically for adapters (Controllers, Repositories) to verify the contract between your code and the immediate framework/infrastructure boundary.

This layered approach ensures the system is thoroughly tested while keeping the feedback loop fast.

## Fakes over mocks (default)

- **Mandatory fakes for external dependencies**: You MUST use hand-written fakes for infrastructure ports (repositories, external APIs) to ensure deterministic and fast tests.
- **No Use Case Interfaces**: Use Cases should be concrete classes. Using an interface for a Use Case is a violation.
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

## Response sequencing for external call fakes

- **A single fake should support response sequencing** — configure a list of responses that play back in order. Do not create separate fake classes for success, error, timeout, partial failure, etc. One fake class per port, with response variants as a sealed class.
- Multiple fake classes for the same port (e.g., `ThrowingRemoteSource`, `FailingDownloadRemoteSource`, `SpyRemoteSource`) are a violation — unify into one configurable fake with a `Response` sealed class and built-in call counting.
- **Auto-advance**: each call consumes the next response. Last response repeats if the sequence is exhausted. No manual `advance()` calls.

## API controller tests (slice standard)

For controllers, use this baseline:

- Slice test annotation targeting the controller under test
- Injected test client
- Mocked use case dependency (mocking the use case here is acceptable)
- Request via test client
- Assert HTTP status first, then payload/headers when needed
- Verify delegation to the mocked use case/dependency
- For create endpoints, check `Location` header behavior when applicable

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

## Async/reactive tests

- Use deterministic waiting and assertion style (no sleeps).
- Ensure async tests assert outcomes, not intermediate incidental timing.

## Test file size & grouping

- Test files exceeding ~300-400 lines covering unrelated features should be split by feature.
- Keep tests at public API boundaries.

## Repository integration tests (real DB, contract-style)

- Use framework-provided data layer test annotation.
- Talk to a real database (same engine as production or compatible equivalent).
- Keep DB schema managed by migration tools.
- Use schema validation mode to catch drift.
- Verify CRUD contract scenarios: save/read, list-empty/list-populated, update, delete-existing, delete-missing idempotence.

## Contract tests for ports

- Every domain port should have a contract test.
- Fake and real adapter implementations must satisfy the same contract.

## Public API & Logical Extraction

**Default**: the use case test is the primary entry point for verifying behavior. Test domain logic — including validation, invariants, and edge cases — through the use case, not through isolated domain entity tests. Domain entity tests are the **exception**, not the norm.

Do not widen visibility only for tests.

**Exception**: when a domain class (e.g. a value object or calculator) has enough variants that testing all combinations through the use case would require excessive boilerplate, extract it into a focused class and test that class directly. This must be justified by combinatorial complexity, not convenience.

**Equality**: domain entities with identity must always have equality tested in a dedicated test (e.g., `BankAccountTest`). This is an exception to the "test through the use case" rule — other assertions across the test suite (e.g., `assertThat(repo.findById(id)).isEqualTo(expectedEntity)`) silently depend on equality working correctly. Always test: same identity = equal, different identity = not equal.

## Test adapters through their public interface

- **Adapters must be tested through the port they implement**, not by testing each internal collaborator independently. If an adapter composes an HTTP client, a JSON parser, a file writer, and a validator, test the adapter as a whole through its port contract.
- **Do not create fakes/mocks for an adapter's internal collaborators** when those collaborators are not domain ports. For example, if a sync job internally validates JSON before writing, the validation should be exercised through the sync job's tests — not through a separate `FakeJsonValidator` injected from outside.
- **Assert on observable outcomes, not internal state.** When testing that an operation preserved or changed data, assert through the public interface (e.g., `repository.festivals()` returns the same list) — not by peeking at internal storage (e.g., `localStorage.read()` returns the same JSON). Internal storage is an implementation detail that could change without affecting behavior.
- **Prefer behavioral consequence over collaborator state.** When a test injects a collaborator (e.g., a metadata store, a version store), prefer asserting on the behavioral consequence rather than the collaborator's internal state. For example, instead of `assertEquals(PAST_INTERVAL, metadataStore.lastCheckedAt())` to prove "timestamp wasn't saved on failure," test that an immediate retry succeeds — that's the actual consequence the user cares about.
- **Extract and test independently only for combinatorial explosion.** When testing through the public interface would require an impractical number of test cases to cover all combinations, extract the complex internal logic into its own class with its own tests. But that class stays `internal`/`private` — it is not promoted to a domain port.
- **Rare exception: injecting fakes for error paths that are impossible to trigger through the public interface** (e.g., simulating a disk-full error, a corrupted file handle, or an OOM crash). These cases are rare and must be explicitly justified.

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
