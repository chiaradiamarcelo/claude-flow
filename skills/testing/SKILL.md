---
name: testing
description: Use whenever writing, modifying, or reviewing tests in this project. Defines the expected style for unit tests and API controller (slice / narrow integration) tests. Stack-agnostic — examples are in Kotlin, but principles apply to any language/framework.
allowed-tools: Read, Write, Edit, Glob, Grep, Bash
---

## Test structure (mandatory)

Every test follows **Given-When-Then**.
Separate Given-When-Then with blank lines, without comments:

- **Given/When/Then must trace cleanly.** Every value the When or Then references must be explicit in the Given. When the test queries or asserts by a specific id, domain, status code, etc., the setup must put that value on the seeded data — don't rely on a factory default. If a value matters to the assertion, make it a *required* parameter of the test-data factory; don't bury it as an optional override or a hidden default. The reader should be able to trace each value in the assertions back to the seed without guessing.

```kotlin
// Bad — DOMAIN is silently the default of `row(...)`, the test reads as if domain doesn't matter
seed(listOf(row(USER_ID, crawler = "gptbot")))
val found = result.find { it.domain == DOMAIN }

// Good — DOMAIN is explicit in both the seed and the assertion
seed(listOf(row(USER_ID, DOMAIN, crawler = "gptbot")))
val found = result.find { it.domain == DOMAIN }
```

- Use the minimum fixture/input data needed to prove the behavior; remove extra records that do not affect the assertion.
- When a behavior can be proven with 1-2 domain values, do not use larger challenge/reference datasets in that test.
- Prefer semantic shared constants for recurring domain values in tests instead of ad-hoc literals.
- The before-each setup hook (e.g. `@BeforeEach` in JUnit, `beforeEach` in Jest/Vitest) is the mandatory place for instantiating fakes, use cases, and controllers that **every test in the suite uses identically**. Never initialize them inline as field declarations. Declare the field without initialization and assign it in setup.
- Never seed test data (e.g. `repository.save(...)`, `fake.add(...)`) in setup — data setup must live inside each test method to keep tests readable and self-contained.
- **Prefer enriching the fake over building inline mocks.** When a test needs a port to fail (or behave differently) for one scenario, do NOT build a bespoke mock object inside the test. Instead, give the project's existing fake a small convenience method (e.g. `failWith(failure)`) and call it inline in the test method. The fake stays in setup (it is a shared stateless dependency); the `failWith(...)` call is test-specific data setup and follows the same rule as `repository.save(...)` — it lives inside the test method, never in setup.

```kotlin
// In the fake:
class FakeFooRepository : FooRepository {
    private var nextFailure: FooLookupFailure? = null

    fun failWith(failure: FooLookupFailure) {
        this.nextFailure = failure
    }

    override fun find(id: Long): Result<Foo, FooLookupFailure> {
        nextFailure?.let { return Fail(it) }
        // ...normal behavior
    }
}

// In the test:
@Test
fun returns_failure_when_the_lookup_fails() {
    fooRepository.failWith(FooLookupFailure(USER_ID))

    val result = useCase.run(USER_ID)

    assertThat(result).isFailureOf(FooLookupFailure::class)
}
```

```kotlin
class CalculateOccupancyTest {

    @Test
    fun returns_expected_occupancy_when_capacity_is_available() {
        val repository = FakeGuestRepository(listOf(lowGuest, highGuest))
        val useCase = CalculateOccupancy(repository)

        val result = useCase.execute(request)

        assertThat(result.totalAssignedRooms).isEqualTo(2)
    }
}
```

## Mandatory Review

**Every new or modified test must be reviewed by the `test-reviewer` agent.**

## Naming

- Domain/unit test class/file: `<ClassUnderTest>Test` (or the stack's equivalent — e.g., `<ClassUnderTest>.test.ts`).
- API controller integration/slice test class/file: `<ControllerName>IT` (or the stack's equivalent for narrow integration tests).
- Test method/case name: snake_case behavior style. Where the language disallows or strongly discourages snake_case identifiers (e.g., JS/TS `it("...")`), use the equivalent natural-language string form.
- camelCase test method names are not allowed.
- For failure scenarios, prefer `fails_when_<condition>` over `throws_when_<condition>`.
- **Use plain business language, not invented jargon.** Avoid verbs the domain doesn't already use (`credits`, `honors`, `respects`, `enrolls`). Prefer plain English a domain expert would say: `ignores_…`, `returns_…`, `saves_…`, `rejects_…`. If a verb makes the reader pause to translate, replace it. Example: `ignores_sightings_from_other_users` reads better than `only_credits_sightings_belonging_to_the_requested_user`.
- Prefer `returns_<status>_when_<condition>` for API tests.
- **Name the behavior, not the mechanism.** A test name should communicate something useful to whoever reads it — the observable outcome or condition from the caller's point of view — not the internal implementation that happens to produce it. The reader rarely cares *how* the work is done.
  - **Exception: when the mechanism IS a behavior you care about, name it.** A cache is an implementation detail from the outside — but if caching is a guarantee you must uphold (e.g. `does_not_refetch_on_second_call`), then it's behavior worth naming and testing. The test is whether the mechanism is a contract the reader relies on, or just incidental plumbing.
  - **Example (incidental → drop it):** `when_aggregation_fails` / `fails_when_the_cached_urls_query_throws` — the aggregation step and the table name are internal mechanics that tell the reader nothing about the contract. The contract is simply that a failing run is reported as a failure: `when_the_job_fails` / `propagates_the_error`.

## Logic in Tests (Forbidden)

**Never use `if`, `else`, `for`, `while`, `switch`, `forEach`, or similar control flow in a test body.**
Tests must remain declarative and linear. If branching appears necessary, split scenarios or redesign setup.

## One behavior per test

Each test verifies one behavior. If a test name needs "and", split it. A test name should describe a single observable behavior; multiple assertion calls (e.g., `assertThat(...)`, `expect(...)`) that each prove a different behavior — not different facets of the same outcome — is the same smell.

- **Watch the seed shape, not just the assertions.** A test can name one rule but exercise two if the seed is shaped for both. Example: a test named "returns distinct user IDs" with three rows for user A and one for user B exercises both *deduplication* (rule 1: multiple rows per user collapse to one) and *multi-user enumeration* (rule 2: each distinct user appears) — the single `hasSize(2)` / `toHaveLength(2)` assertion is doing work for both rules. Split: one test seeds two rows for one user (proves dedup, expects a single-element list); the other seeds one row for each of two users (proves enumeration, expects both IDs). Detection heuristic: if removing one *type* of seed variation (the duplicate row, or the second user) still proves the rule the name claims, the removed variation was testing a different rule — split.

```kotlin
// Bad — one test, two rules. The hasSize(2) does work for both dedup AND enumeration.
@Test
fun returns_distinct_user_ids_of_users_with_non_deleted_domains() {
    seed(listOf(
        row(USER_A, deletionRequestedAt = null),
        row(USER_A, deletionRequestedAt = null),
        row(USER_A, deletionRequestedAt = null), // over-specified — 2 rows is enough for dedup
        row(USER_B, deletionRequestedAt = null),
    ))

    val userIds = finder.findAll()

    assertThat(userIds).hasSize(2)
    assertThat(userIds).containsExactlyInAnyOrder(USER_A, USER_B)
}
```

```kotlin
// Good — split. Each test seeds the minimum for the single rule it names.

@Test
fun returns_a_user_id_only_once_when_the_user_has_multiple_non_deleted_domains() {
    seed(listOf(
        row(USER_A, deletionRequestedAt = null),
        row(USER_A, deletionRequestedAt = null),
    ))

    val userIds = finder.findAll()

    assertThat(userIds).containsExactly(USER_A)
}

@Test
fun returns_one_user_id_for_each_user_with_at_least_one_non_deleted_domain() {
    seed(listOf(
        row(USER_A, deletionRequestedAt = null),
        row(USER_B, deletionRequestedAt = null),
    ))

    val userIds = finder.findAll()

    assertThat(userIds).containsExactlyInAnyOrder(USER_A, USER_B)
}
```

## Designing the test list (ZOMBIES + mutation check)

Before writing tests for a behavior, walk the **ZOMBIES** categories explicitly. Don't invent "interesting" cases — invent *systematic* ones. The categories are designed to force progressively more complex production code, and the early ones are usually the strongest discriminators for catching inversions, off-by-ones, and missing filters.

- **Z**ero — empty / null / no-result input
- **O**ne — exactly one item (catches inversions and missing filters)
- **M**any — N>1 items: all-same, all-different, mixed
- **B**oundary — min/max, off-by-one, time-window edges
- **I**nterface — the contract shape (types, fields, optional/required)
- **E**xceptions — failures, errors, infrastructure faults
- **S**imple — keep each scenario minimal; resist "interesting" combinations

For every test in the list, ask the **mutation question**:

> "If I flip an operator (`>` ↔ `<`, `=== 1` ↔ `=== 0`, `&&` ↔ `||`) or remove a filter clause in the production code, would this test catch it?"

If you can't name a mutation the test rules out, the test is vacuous — redesign or delete.

### Asymmetric data for discriminating filters

A test on a filtering or aggregating function must use data that distinguishes the correct implementation from likely mutants. Symmetric data (e.g. one matching row and one non-matching row, asserting `count == 1`) is a smell — both the correct predicate and its inversion give the same result. Pick counts that diverge.

```kotlin
// Bad — 1 matching + 1 non-matching with predicate `flagged = 1`: count is 1 either way.
// Mutation `flagged = 0` also yields 1. Test catches no mutation.
seed(listOf(row(flagged = true), row(flagged = false)))
assertThat(query.count()).isEqualTo(1)

// Good — 2 matching + 1 non-matching: correct predicate yields 2, mutation yields 1.
seed(listOf(row(flagged = true), row(flagged = true), row(flagged = false)))
assertThat(query.count()).isEqualTo(2)
```

References: James Grenning, ["TDD Guided by Zombies"](https://blog.wingman-sw.com/tdd-guided-by-zombies).

## Assertions

- Prefer the project's assertion library for consistent style.
- For comparisons, prefer `assertThat(actual).isEqualTo(expected)` style or equivalent.
- **Precision-sensitive values**: MUST use comparison methods that ignore scale/representation differences.
- **Pick numbers that produce exact assertions.** When you control the test fixture, design it so percentages and ratios resolve to integers (1/2 = 50, 2/100 = 2, 1/4 = 25) and assert with exact equality. Approximate/tolerance matchers (`toBeCloseTo`, `isCloseTo`, `within`) are for values the *production code* legitimately makes fuzzy (currency rounding, trigonometry, accumulated multiplications). A tolerance assertion over a fixture you chose to be fractional (e.g. `1/3 * 100` with ε) is a smell — change the seed so the math resolves cleanly.
- Flag mixed assertion styles when a single style can keep tests consistent.
- Avoid magic numbers; use named constants/fixtures where meaning matters.
- **No redundant intermediate assertions**: do not assert a precondition that is already tested implicitly by the next assertion. For example, asserting an Optional/Maybe is present before accessing its value is redundant if the next line asserts a property of the unwrapped value — the test will fail anyway if the value is absent.
- **Subset matchers are NOT equality.** Matchers like `arrayContaining([...])` / `objectContaining({...})` in Jest, `hasItems(...)` in Hamcrest, `Mockito.argThat`, etc. pass when the asserted items are *included* in the actual value — extras slip through. To assert "exactly these items in any order" on a collection, pair the subset matcher with a length/size check, or sort both sides and use deep equality.

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
- **Prepare the seam before changing signatures.** When you are about to add a parameter to a constructor, method, or data class that is already called in multiple places (especially tests), scan the call sites first. If 3+ sites use identical construction, extract the helper *before* changing the signature — not after. One edit in the helper, not shotgun surgery across dozens of files. "Make the change easy (this might be hard), then make the easy change." — Kent Beck

## Test data visibility

- **All test data referenced in assertions must be visible in the test body.** Class-level / module-level fields that build test data (e.g., `private val remoteJson = aFestivalJson(...)` in Kotlin, `const remoteJson = aFestivalJson(...)` at the top of a Jest spec) and are used implicitly by tests are a violation. The reader should not need to scroll to class fields to understand what a test asserts. Pass data explicitly via the setup helper or use named constants.
- **Don't test return types that are internal signals.** If a return type (e.g., `SyncResult.Success`) is only consumed internally — not by presentation or UI — don't write tests that only assert on it. The behavioral tests (e.g., "festivals updated") already prove success.
- **"Unchanged" assertions must use distinct before/after values.** When a test asserts "data unchanged after operation," the local and remote data must have visibly different identifiers. If both happen to have the same ID, the test passes vacuously even if the wrong data is returned.

## Test behavior, not library boundaries

- **When a library implements your product behavior, the behavior is still yours to test.** The library is an implementation detail, not an excuse to skip testing. "Show a fallback when the image fails to load" is product behavior whether an image-loading library or hand-written code implements it.
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
- **Mocking Use Cases in API tests**: Using a mocking library to mock the Use Case in an API controller (slice / narrow integration) test is acceptable and standard.
- **Fakes must satisfy the contract**: Fakes MUST behave like real implementations for the tested contract and pass the same contract tests.
- Fakes must implement the same port interface as production adapters.
- **Every test starts from a clean slate — always in the before-each hook, never in the after-each / after-all hooks.**
  - **Fakes**: create fresh instances in setup. No `clear()`/`reset()` methods.
  - **Database**: when constructing the connection/context is expensive, truncate or clear tables in the before-each hook instead of recreating. But the cleanup always happens **before** each test, never after.

```kotlin
class FakeGuestRepository(initialGuests: List<Guest>) : GuestRepository {
    private val guests: List<Guest> = initialGuests.toList()

    override fun findAll(): List<Guest> = guests.toList()
}
```

## Response sequencing for external call fakes

- **A single fake should support response sequencing** — configure a list of responses that play back in order. Do not create separate fake classes for success, error, timeout, partial failure, etc. One fake class per port, with response variants as a discriminated union (Kotlin/Scala `sealed class`, TypeScript discriminated union, or the stack's equivalent).
- Multiple fake classes for the same port (e.g., `ThrowingRemoteSource`, `FailingDownloadRemoteSource`, `SpyRemoteSource`) are a violation — unify into one configurable fake with a `Response` variant type and built-in call counting.
- **Auto-advance**: each call consumes the next response. Last response repeats if the sequence is exhausted. No manual `advance()` calls.

## API controller tests (slice standard)

For controllers, use this baseline:

- Narrow integration / slice test setup targeting only the controller under test (e.g., Spring's `@WebMvcTest`, NestJS testing module, FastAPI `TestClient`).
- Injected test HTTP client.
- Mocked use case dependency (mocking the use case here is acceptable).
- Request via the test client.
- Assert HTTP status first, then payload/headers when needed.
- Verify delegation to the mocked use case/dependency.
- For create endpoints, check `Location` header behavior when applicable.

Success path example:

```kotlin
@Test
fun returns_200_when_single_order() {
    whenever(useCase.allOrders()).thenReturn(listOf(
        Order("id_1", LocalDate.of(2024, 1, 15), 99.99, "USD", SALE)
    ))

    val response = client.get("/orders")

    assertThat(response.status).isEqualTo(200)
    assertThat(response.body).isEqualTo(listOf(
        mapOf("id" to "id_1", "date" to "2024-01-15", "amount" to 99.99)
    ))
}
```

Validation path example:

```kotlin
@Test
fun returns_400_when_missing_required_field() {
    val response = client.post("/orders", body = mapOf("amount" to 99.99))

    assertThat(response.status).isEqualTo(400)
    verifyNoInteractions(useCase)
}
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

- Use the stack's narrow data-layer test setup (e.g., Spring's `@DataJpaTest`, Prisma's test database, SQLAlchemy test session).
- Talk to a real database (same engine as production or compatible equivalent).
- Keep DB schema managed by migration tools.
- Configure the ORM/data layer to validate the schema against migrations (catch drift) rather than auto-generating it.
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
- **Extract and test independently only for combinatorial explosion.** When testing through the public interface would require an impractical number of test cases to cover all combinations, extract the complex internal logic into its own class with its own tests. But that class stays at non-public visibility (Kotlin `internal`, Java package-private, TypeScript module-private) — it is not promoted to a domain port.
- **Rare exception: injecting fakes for error paths that are impossible to trigger through the public interface** (e.g., simulating a disk-full error, a corrupted file handle, or an OOM crash). These cases are rare and must be explicitly justified.

## What to test

For **UseCases**:
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
