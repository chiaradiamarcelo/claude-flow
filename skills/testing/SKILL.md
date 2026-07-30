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
- **Avoid implementation details.** Use domain/concept language, not visual or widget details.
  - Bad: `shows_filled_red_heart_when_item_is_favourite` — "heart" is an icon shape; changing the icon breaks the test name.
  - Good: `shows_active_favourite_icon_when_item_is_favourite` — "favourite" is a stable concept.
  - Similarly avoid: specific icon names, widget types (`checkbox`, `radio button`), colours, framework class names.

## Logic in Tests (Forbidden)

**Never use `if`, `else`, `for`, `while`, `switch`, `forEach`, or similar control flow in a test body.**
Tests must remain declarative and linear. If branching appears necessary, split scenarios or redesign setup.

### Exception: exhaustive enum/variant mapping

When multiple tests would differ **only** by the enum value and its expected output (each testing one type maps to one label), collapse them into a single exhaustive-iteration test. Iterating an enum's `entries` / `values()` isn't branching — it's proof the mapping covers every variant. Adding a new variant should force the test to fail until the mapping is updated.

Use a dictionary of `{ variant → expected }` and iterate the enum's own variant list — not a subset. Include a per-variant message in the assertion so a failure identifies the offending variant.

```kotlin
private val expectedTypeLabels = mapOf(
    FestivalType.Kirchwei to R.string.type_kirchwei,
    FestivalType.Kerwa    to R.string.type_kerwa,
    // ...one row per variant...
)

@Test
fun `maps every festival type to its label resource`() {
    FestivalType.entries.forEach { type ->
        assertEquals(
            expectedTypeLabels.getValue(type),
            formatter.typeLabelResId(aFestival(type = type)),
            "Unexpected label for $type",
        )
    }
}
```

The `getValue(type)` throws if the map is missing a variant; iterating `entries` catches variants added after the test was written. Together they make coverage total and mechanical.

## One behavior per test

Each test verifies one behavior. If a test name needs "and", split it. A test name should describe a single observable behavior; multiple assertion calls (e.g., `assertThat(...)`, `expect(...)`) that each prove a different behavior — not different facets of the same outcome — is the same smell.

### Orthogonal behaviors: test dimensions independently

When two behaviors are truly **independent** (e.g., marker scale depends only on selection, marker tint depends only on favourite status), test each dimension in isolation — not every combination. A `4×4` combination matrix multiplies tests without adding coverage; two focused tests prove the same rules.

To prove a dimension is genuinely irrelevant to a behavior, you can vary the irrelevant axis *within one test* via reactive state and assert the outcome doesn't change. That's not two behaviors — it's proof that the rule holds universally along the irrelevant axis.

```kotlin
@Test
fun `selected marker is enlarged regardless of favourite status`() {
    var favouriteIds by mutableStateOf(emptySet<String>())
    composeTestRule.setContent {
        mapInteractions.Content(selectedFestival = festival1, favouriteIds = favouriteIds, ...)
    }
    composeTestRule.waitForIdle()
    assertEquals(SELECTED_SCALE, mapInteractions.markerScaleByFestivalId[festival1.id])  // non-favourite

    favouriteIds = setOf(festival1.id)
    composeTestRule.waitForIdle()
    assertEquals(SELECTED_SCALE, mapInteractions.markerScaleByFestivalId[festival1.id])  // favourite: still enlarged
}
```

One behavior (`selected → enlarged`), universally quantified over the irrelevant dimension (favourite status). The "and" rule still applies.

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

## Discovering candidate behaviours (ZOMBIES + mutation check)

This is the *discovery* step — it feeds the ordered list in the next section; it is not itself the design. Walk the **ZOMBIES** categories explicitly to surface candidates. Don't invent "interesting" cases — invent *systematic* ones. ZOMBIES answers **"did I miss a case?"** — most often a forgotten empty/Zero input or an Exception path. The *ordering* and per-row justification come next, under FLFI · TPP · Contradiction; TPP is the spine, ZOMBIES is the completeness net (they answer different questions — keep both).

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

## Ordering & justifying the list (FLFI · TPP · Contradiction)

Discovery gives you candidate behaviours; this step turns them into an **ordered** sequence where each row earns its place by forcing one minimal change in the production code. Think this way whenever you write tests — solo, or when producing a reviewable test-list plan (the `test-designer` agent renders this as a table). Three lenses, kept separate on purpose:

- **Name — FLFI (Final Label, First Implementation).** The label states the *complete business rule, including its condition, from the first write* — and is never renamed as the code grows. Name a test after the rule it pins from the caller's POV, not after the implementation step it happens to force. `adds_100_to_winnings_when_registered_on_birthday`, not `adds_100_to_winnings` patched later. The name tracks the **rule**, never the **mechanism**.
- **TPP (Transformation Priority Premise) — the ordering spine.** The code transformation this row forces. Order the list simplest-transformation-first: a row that forces a simpler transformation is a smaller, more fundamental test, and this ordering makes production code grow by minimal steps. This is what turns *coverage thinking* into *forcing-function thinking*. Don't invent transformation names or guess priorities — tag each driving row with one from the canonical list below, cited by name.
- **Contradiction.** What the code **as it stands after the previous rows** wrongly assumes, that this row proves false. This is the mutation question from discovery, made concrete and relative to the evolving code — the generative driver *and* the minimality guard: the row exists to break one current assumption, so **only the data needed to create that contradiction is justifiable**. If you can't name what the code-so-far believes that this row falsifies, the row is vacuous — drop it.

**The canonical TPP transformations** (Robert C. Martin), simplest first — higher on the list = simpler = preferred:

1. `{} → nil` — no code → code returning nil / nothing
2. `nil → constant`
3. `constant → constant+` — a constant becomes a more complex constant
4. `constant → scalar` — a constant becomes a variable or argument
5. `statement → statements` — add more unconditional code
6. `unconditional → conditional` — split the execution path (introduce an `if`)
7. `scalar → array`
8. `array → container`
9. `statement → recursion`
10. `conditional → loop` — an `if` becomes a `while` / iteration
11. `expression → function` — replace an expression with a call / algorithm
12. `variable → assignment` — change a variable's value

It's a heuristic, not a law: when a row could be made green by more than one change, prefer the higher-priority (simpler) transformation, and order rows so early ones force high-priority transformations and later ones force lower. Cite the transformation by name (a priority number, if used, is its position above). Rows that don't drive a transformation chain — contract and equality rows — are `n/a`.

**Per-row procedure** — for each candidate behaviour, in order:
1. Write the FLFI name (full rule + condition).
2. Name the contradiction: what does the code-so-far assume that this row falsifies?
3. Derive the **smallest seed** that creates that contradiction. Delete every row/field/value that doesn't change *which* contradiction is caught. Minimality is **relative to the contradiction**, not an absolute "few rows" (see *Asymmetric data* above — the seed must diverge from what a mutant would produce).
4. Tag the TPP transformation it forces; keep the list ordered simplest-first.
5. **Redundancy gate:** does an earlier row already fail under this row's contradiction? If yes, **drop it** — don't keep it "for documentation." A vacuous row is removed, not annotated.

**Isolate mechanisms.** If a behaviour doesn't depend on a mechanism (chunking, batching, caching, pagination), set that mechanism's knob to its trivial value and keep its data out of the row — then give the mechanism its **own** explicit row with the knob made visible. Never contort a behaviour test into also exercising chunking; that entanglement is the classic over-seeding smell.

**TPP is `n/a` for rows that don't drive a transformation chain** — contract tests (a *set* of consumer-facing port guarantees) and equality / `equals` rows. For these, FLFI + Contradiction carry the weight; don't manufacture a transformation tag to fill the column.

## Assertions

- Prefer the project's assertion library for consistent style.
- For comparisons, prefer `assertThat(actual).isEqualTo(expected)` style or equivalent.
- **Precision-sensitive values**: MUST use comparison methods that ignore scale/representation differences.
- **Pick numbers that produce exact assertions.** When you control the test fixture, design it so percentages and ratios resolve to integers (1/2 = 50, 2/100 = 2, 1/4 = 25) and assert with exact equality. Approximate/tolerance matchers (`toBeCloseTo`, `isCloseTo`, `within`) are for values the *production code* legitimately makes fuzzy (currency rounding, trigonometry, accumulated multiplications). A tolerance assertion over a fixture you chose to be fractional (e.g. `1/3 * 100` with ε) is a smell — change the seed so the math resolves cleanly.
- Flag mixed assertion styles when a single style can keep tests consistent.
- Avoid magic numbers; use named constants/fixtures where meaning matters.
- **No redundant intermediate assertions**: do not assert a precondition that is already tested implicitly by the next assertion. For example, asserting an Optional/Maybe is present before accessing its value is redundant if the next line asserts a property of the unwrapped value — the test will fail anyway if the value is absent.
- **Subset matchers are NOT equality.** Matchers like `arrayContaining([...])` / `objectContaining({...})` in Jest, `hasItems(...)` in Hamcrest, `Mockito.argThat`, etc. pass when the asserted items are *included* in the actual value — extras slip through. To assert "exactly these items in any order" on a collection, pair the subset matcher with a length/size check, or sort both sides and use deep equality.
- **Sealed-hierarchy assertion helpers**: when a test helper asserts a value is a specific variant of a sealed hierarchy (Kotlin sealed class, TypeScript discriminated union, Rust enum, Java sealed class) and returns the typed result, use exhaustive dispatch — never a truthy check plus an unsafe cast. Exhaustive dispatch gives compiler-enforced coverage; when the hierarchy gains a new variant, the helper fails at compile time instead of throwing at runtime.

```kotlin
// Good — exhaustive `when` gives compile-time coverage
private fun assertSuccess(state: UiState): UiState.Success = when (state) {
    is UiState.Success -> state
    is UiState.Loading -> throw AssertionError("Expected Success but was Loading")
    is UiState.Error   -> throw AssertionError("Expected Success but was Error(${state.reason})")
}

// Bad — unsafe downcast; a new variant would compile fine but crash at runtime
private fun assertSuccess(state: UiState): UiState.Success {
    assertTrue(state is UiState.Success)
    return state as UiState.Success
}
```

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

### Fixture builders — enforcement

Once a builder exists for a domain/DTO type, direct construction of that type in tests is a **violation**, not a style preference. The same applies to specifying fields that don't matter to the behavior:

- **Flag as a violation**: any direct construction of a domain type in tests (`Festival(...)`, `Order(...)`) when a builder exists. Tests must call the builder (`aFestival(...)`, `anOrder(...)`) and rely on its defaults.
- **Flag as a violation**: any test that passes a field to the builder when that field is not read by the behavior under test. Only fields essential to the assertion should be specified.
- **Flag as a warning** and recommend creating a builder when a domain/DTO type is directly constructed across multiple test files.

```kotlin
// Bad — direct construction; every irrelevant field couples the test to the domain shape.
val festival = Festival(
    id = "today-active", name = "Today Active Festival",
    town = "Testtown", landkreis = "Testkreis",
    dates = DateRange(LocalDate.of(2025, 8, 10), LocalDate.of(2025, 8, 20)),
    location = Location(49.45, 11.07),
    description = "", sourceUrls = emptyList(),
)

// Good — only the fields the behavior actually needs.
val festival = aFestival(dates = DateRange(today, today.plusDays(10)))
```

Rules the builder must satisfy:
- Provides a default value for **every** field, so callers can omit anything irrelevant.
- Lives with the tests it serves (e.g., a `Fixtures.kt` in the test source set).
- Is the single point of maintenance when the underlying type gains a field.

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
- **Every implementation satisfies the contract**: the fake and the real adapter are equals — each independently passes the same contract suite, which specifies the behavior the consumer depends on. The fake isn't "made to mirror the real"; both conform to the contract.
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
- **Name slices `<Component><Feature>Test`** (or the stack's equivalent) so the file names describe what each slice covers — e.g., `FestivalMapLocationTest.kt`, `FestivalMapFilterTest.kt`, `FestivalMapPermissionsTest.kt`. A folder full of `FestivalMapTest1`, `FestivalMapTest2` conveys nothing; a folder of `<Component><Feature>Test` files reads as a table of contents.
- **Slices still target the public API.** Splitting a file is a *grouping* decision, not a mandate to test private functions or internal collaborators. Each slice still exercises the component through its main entry point (Screen, ViewModel, controller, use case) — the split just narrows the *set of behaviors* each file covers, not the *depth* at which they're tested.
- **Shared setup**: when multiple slices need the same setup, extract it to a helper function or a base class — but **prioritize readability over DRY in tests**. A tiny duplication in setup that keeps each test self-contained is worth more than a clever base class that saves five lines but forces the reader to jump around to understand what any single test does. In tests, WET (write everything twice) is often cheaper than DRY.

## Repository integration tests (real DB, contract-style)

- Use the stack's narrow data-layer test setup (e.g., Spring's `@DataJpaTest`, Prisma's test database, SQLAlchemy test session).
- Talk to a real database (same engine as production or compatible equivalent).
- Keep DB schema managed by migration tools.
- Configure the ORM/data layer to validate the schema against migrations (catch drift) rather than auto-generating it.
- Verify CRUD contract scenarios: save/read, list-empty/list-populated, update, delete-existing, delete-missing idempotence.

## Contract tests for ports

- Every domain port should have a contract test.
- Fake and real adapter implementations must satisfy the same contract.
- **Pin the full projection with one full-object assertion.** A read repository/query's contract is "given this input, return *this* object" — the returned shape and values ARE its behavior. So the contract suite must include **exactly one** test (just one — not every case; see the slice/full split below) that seeds a fully-populated row (every column a distinctive non-default value) and asserts the **entire** returned object with deep equality (`isEqualTo(wholeObject)` / `toEqual({...})`), run against both the fake and the real adapter. Without it, a query that later drops a column from its projection, maps it from the wrong source column, or returns null instead of the real value stays green on key-only assertions while production data is silently wrong — and the fake can drift to a half-fictional shape the real adapter never returns. This is the projection's mutation guard (flip any field → red) and the only thing that keeps the fake honest across the whole shape.
- **Keep the slice/full split.** Behavior tests (filtering, lookup, ordering, edge cases) assert only the field(s) they are about (e.g. `map { it.id }`); ONE dedicated test pins the full object. Don't make every test a full-object assertion — adding a legitimate column would redden them all for no behavioral reason. The rule is "one full-object test per read port," not "every test asserts everything."
- Write the full-object test's expected value as an explicit literal; don't derive it from the seed, or you just re-implement the production mapping inside the test.

```kotlin
// The ONE full-object test — pins the whole projection. Both the fake and the
// real adapter run it via the shared contract.
@Test
fun returns_every_stored_field_for_an_id() {
    seed(listOf(row(USER_ID, email = "a@b.co", plan = "pro", active = true, seats = 5))) // every column set

    val found = repository.findById(USER_ID)

    assertThat(found).isEqualTo(User(USER_ID, "a@b.co", "pro", active = true, seats = 5))
}

// Every other test asserts only the slice it is about — never the whole object.
@Test
fun excludes_inactive_accounts() {
    seed(listOf(row(USER_ID, active = true), row(OTHER_ID, active = false)))

    val found = repository.activeAccounts()

    assertThat(found.map { it.id }).containsExactly(USER_ID)
}
```

## Public API & Logical Extraction

**Default**: the use case test is the primary entry point for verifying behavior. Test domain logic — including validation, invariants, and edge cases — through the use case, not through isolated domain entity tests. Domain entity tests are the **exception**, not the norm.

Do not widen visibility only for tests.

**Do not add production API surface that only tests consume.** A return value, parameter, or method that exists solely so a test can assert on it — while production ignores it — is test-induced design damage. Drop it and assert the observable outcome instead: read the state back through the public interface. Example: a repository `update`/`markRefreshed` the caller invokes fire-and-forget should return nothing, not an affected-row count that exists only for `assert(count == 1)`; assert the row's new state via a read method (`findById(...)`). The count is an implementation artifact; the persisted state is the behavior.

**Exception**: when a domain class (e.g. a value object or calculator) has enough variants that testing all combinations through the use case would require excessive boilerplate, extract it into a focused class and test that class directly. This must be justified by combinatorial complexity, not convenience.

**When you extract, extract with a public surface — not by widening visibility.** If a piece of logic warrants its own tests, it warrants its own public API in its own context. Do **not** make an existing internal helper `internal`/`package-private` just to reach it from tests. Move it into a new class/module whose public API is the thing you want to test.

**Tests of the extracted class stay behavior-oriented.** Even though the extraction was structural, the tests of the extracted class must describe behavior from the perspective of its direct client — not implementation steps. `computes_the_score_when_all_criteria_pass` is a behavior; `iterates_over_criteria_list_in_order` is an implementation detail. If you can only describe what the extracted class does by narrating its steps, it wasn't ready to be extracted.

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
