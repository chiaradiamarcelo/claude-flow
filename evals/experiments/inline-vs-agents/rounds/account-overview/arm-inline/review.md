## Ad-hoc Review Report

### Target
`src`

### Triggered reviewers
- **arch-reviewer**: `src/main/**` (9 Kotlin files + `application.properties`)
- **refactor-advisor**: `src/main/**` (same 10 files)
- **test-reviewer**: `src/test/**` (7 test/fake files)
- **api-reviewer**: `**/api/**` (`AccountOverviewController.kt`, `AccountOverviewResponse.kt`, `AccountOverviewControllerIT.kt`)

### Skipped reviewers
- **ui-test-reviewer**: no `*.test.tsx`/`*.test.jsx` files
- **android-ui-test-reviewer**: no `androidTest/**` sources
- **android-presentation-reviewer**: no `presentation/**` package

### VIOLATIONS (must fix)
_None._

### WARNINGS (should fix)
- **refactor-advisor** — `src/main/kotlin/com/example/bank/domain/query/AccountOverview.kt:5`: `tier` is fully derived from `balance` via `MembershipTier.forBalance`, yet the public constructor takes both independently, so `AccountOverview("a1", BigDecimal("5000"), MembershipTier.STANDARD)` is constructible and self-contradictory. Both call sites (`AccountOverviewQueryJpaAdapter.toOverview`, `FakeAccountOverviewQuery.seed`) duplicate the `forBalance` call to stay consistent by convention. Make the constructor private and expose `AccountOverview.of(accountId, balance)`.
- **refactor-advisor** — `MembershipTier.kt:5`: `PREMIUM_THRESHOLD = BigDecimal("1000")` is a hard-coded business policy; a tier cutoff changes without a code change and should be injected/configurable.
- **api-reviewer** — `AccountOverviewController.kt:19`: bare `ResponseStatusException(HttpStatus.NOT_FOUND)` with no reason/body yields Spring's default error shape rather than a consistent project error DTO.
- **arch-reviewer** — `AccountOverviewResponse.kt:5`: response DTO sits loose in `api/` instead of `api/dto/` or nested inside the controller.
- **test-reviewer** — `AccountOverviewControllerIT.kt:15`: no test covers the 500 unexpected-runtime-failure path; `FakeAccountOverviewQuery` has no failure-injection hook (e.g. `failWith(...)`), so the scenario can't be exercised at all.

### SUGGESTIONS
- **api-reviewer** — centralize 404 mapping via an `@ExceptionHandler` translating a domain "not found" signal, so all controllers share one error contract.
- **refactor-advisor** — `AccountOverviewController.kt:17`: primitive obsession; `accountId: String` threads unchecked through every layer. An `AccountId` value class would give the concept a name and one validation site.
- **refactor-advisor** — `AccountRecord.kt:11`: identity-bearing JPA entity with no `equals`/`hashCode` based on `accountId`.
- **test-reviewer** — `BigDecimal("1500.00")` repeats verbatim in `AccountOverviewControllerIT.kt:28` and `AccountOverviewQueryContractTest.kt:18`, near the boundaries in `MembershipTierTest`; a shared named constant (e.g. `PREMIUM_BALANCE`) would make the tier derivation traceable.

### GOOD PRACTICES
- Read slice is structurally clean: pure domain model and `*Query` port in `domain/query`, no needless UseCase for a pure read, JPA adapter confined to `infrastructure` with Spring Data primitives kept internal (arch-reviewer).
- Controller is genuinely thin — single read action, explicit domain→DTO mapping, no business logic, correct REST path and status codes (api-reviewer).
- Tests show clean GWT structure, correct contract-test/fake pairing, minimal seeds, and a sensible full-object vs. slice assertion split (test-reviewer).

### Verdict: PASS
No VIOLATION-severity findings. Each reviewer returned a `FAIL` status flag, but every item they raised is a warning or suggestion — the missing 500-path test and the derivable-`tier` constructor are the two worth acting on first.