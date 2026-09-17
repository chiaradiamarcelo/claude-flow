## Ad-hoc Review Report

### Target
`src`

### Triggered reviewers
- **arch-reviewer**: 17 files under `src/main/**`
- **refactor-advisor**: 17 files under `src/main/**`
- **test-reviewer**: 9 files under `src/test/**`
- **api-reviewer**: 5 files under `src/main/kotlin/.../api/**` + `src/test/kotlin/.../api/DepositMoneyControllerIT.kt`

### Skipped reviewers
- **ui-test-reviewer**: no files matched (`**/*.test.tsx`, `**/*.test.jsx`)
- **android-ui-test-reviewer**: no files matched (`**/androidTest/**`, `**/androidInstrumentedTest/**`)
- **android-presentation-reviewer**: no files matched (`**/presentation/**`)

### VIOLATIONS (must fix)
- **test-reviewer** — `src/test/kotlin/com/example/bank/domain/models/account/AccountFixtures.kt:9`: `anAccount`'s `id` parameter defaults to `ACCOUNT_ID`, so tests that act/assert against `ACCOUNT_ID` never state the id in their Given — it's silently supplied by the fixture default instead of being explicit.
- **test-reviewer** — `src/test/kotlin/com/example/bank/application/DepositMoneyUseCaseTest.kt:28`: `accounts.save(anAccount(balance = BigDecimal.ZERO))` omits the account id while the When acts on `ACCOUNT_ID` directly, so the link between seeded account and id under test is invisible. Affects lines 28, 37, 46, 55.

### WARNINGS (should fix)
- **refactor-advisor** — `AccountId.kt:3`: `AccountId(value: String)` accepts any string including blank/empty, with no constructor invariant. An empty path segment produces a technically-valid but invalid-domain `AccountId`. Add a `require()` check.
- **api-reviewer** — `DepositMoneyController.kt:16`: `POST /accounts/{accountId}/deposits` is a non-idempotent financial mutation with no idempotency-key strategy, so a client retry can double-credit the account.
- **api-reviewer** — `DepositMoneyController.kt:16`: URL models `deposits` as a created collection resource, but the handler returns `200 OK` with account state rather than `201 Created` + `Location`.
- **test-reviewer** — `DepositMoneyUseCaseTest.kt:26`: `returns_the_balance_of_the_account_after_a_deposit` and `increases_the_balance_by_the_amount_that_was_deposited` prove the same rule twice, differing only in the literal amount (2 vs 4).
- **test-reviewer** — `DepositMoneyControllerIT.kt:45`: only the "missing required field" 400 case is covered; no malformed/parse-error 400 (non-numeric `amount`, unparsable JSON).

### SUGGESTIONS
- **arch-reviewer** — `AccountJpaEntity.kt:11`: mutable `var` fields are an accepted ORM exception, but the exception should carry a short comment explaining why (Hibernate-managed state).
- **api-reviewer** — `ApiExceptionHandler.kt:21`: `invalidDepositAmount`/`accountNotFound` forward raw domain exception `.message` verbatim to clients, coupling public error text to internal domain wording.
- **test-reviewer** — `DepositMoneyControllerIT.kt:30`: deposit amount `50` is repeated across three tests; extract a named constant.

### GOOD PRACTICES
- Dependency rule and layer placement respected throughout: pure domain, orchestration-only UseCase, thin JPA adapter, correct dto/api boundaries (arch-reviewer, all 17 files).
- Immutable `Account` enforcing its own invariant via a named `isNotPositive` predicate; identity-based equality; `*UseCase` not `*Service`; adapter converts at the boundary; no stray comments (refactor-advisor).
- Correct fake/mock split, a shared repository contract run against both the fake and the JPA adapter, dedicated equality test for `Account` (test-reviewer).
- Controller/DTO/exception-handler triad is thin and maps domain state and exceptions cleanly (api-reviewer).

### Verdict: FAIL
Two VIOLATIONS from test-reviewer, both on the same root cause — the `anAccount` fixture's defaulted `id` hiding the Given→When link in `DepositMoneyUseCaseTest`.