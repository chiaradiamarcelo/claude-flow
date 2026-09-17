## Ad-hoc Review Report

### Target
`src`

### Triggered reviewers
- **arch-reviewer** (`**/src/main/**`): all 13 `src/main` files
- **refactor-advisor** (`**/src/main/**`): all 13 `src/main` files
- **test-reviewer** (`**/src/test/**`, `**/*Test.*`, `**/*IT.*`): all 9 `src/test` files
- **api-reviewer** (`**/api/**`, `**/dto/**`): `api/WithdrawMoneyController.kt`, `api/dto/AccountResponse.kt`, `api/dto/WithdrawMoneyRequest.kt`, `test/.../api/WithdrawMoneyControllerIT.kt`

### Skipped reviewers
- **ui-test-reviewer**: no `*.test.tsx`/`*.test.jsx`
- **android-ui-test-reviewer**: no `androidTest/` sources
- **android-presentation-reviewer**: no `presentation/` sources

No `.claude/pipeline.json` — frontmatter triggers used as-is, no skill injection.

### VIOLATIONS (must fix)
- **[api-reviewer]** `api/WithdrawMoneyController.kt` — No domain-exception→HTTP mapping at the boundary. `WithdrawMoneyUseCase.withdraw` uses `checkNotNull(...)` for a missing account, throwing a bare `IllegalStateException` that nothing translates. A request for a non-existent account bubbles out as Spring's default error (500, raw message leaked) instead of 404. No `@ExceptionHandler`/`@ControllerAdvice` exists anywhere under `api/`.
- **[api-reviewer]** `api/WithdrawMoneyController.kt` — Same root cause: "resource doesn't exist" must map to `404`; today it resolves to an unhandled exception.

### WARNINGS (should fix)
- **[refactor-advisor]** `domain/models/account/Account.kt:14` — `withdraw` enforces no invariant: overdrawing silently yields a negative balance, and a negative amount silently credits the account. Needs guard clauses + a domain exception (e.g. `InsufficientFundsException`).
- **[refactor-advisor]** `domain/models/account/AccountId.kt:3` — Value object wraps a raw `String` with no validation; `AccountId("")` is constructible.
- **[refactor-advisor]** `application/WithdrawMoneyUseCase.kt:11` — Generic `IllegalStateException` for missing account instead of a typed domain error mapped to 404 (same defect the api-reviewer raised as a violation).
- **[api-reviewer]** `WithdrawMoneyController.kt:16-20` — `200 OK` for a creation-shaped `POST /accounts/{id}/withdrawals`; no `201` + `Location`.
- **[api-reviewer]** `WithdrawMoneyController.kt:16-20` — No idempotency strategy on a non-idempotent, retryable `POST` (timeout + retry ⇒ duplicate debit).
- **[test-reviewer]** `AccountTest.kt:9` — Both equality tests hold balance constant at 200, so a mutant whose `equals` also compared `balance` would pass. Need a same-id/different-balance case to pin identity equality.
- **[test-reviewer]** `WithdrawMoneyUseCaseTest.kt:21` — Happy path only; no insufficient-balance or non-existent-account coverage.
- **[test-reviewer / api-reviewer]** `WithdrawMoneyControllerIT.kt:26` — Only 200 + two malformed-input 400s. Missing: 400 for domain invariant violation (negative/zero amount), 404 for unknown account, 500 for unexpected failure.
- **[test-reviewer]** `AccountRepository.contract.kt:6` — Contract never proves `save` overwrites an existing record for the same `AccountId`; an insert-only adapter would pass undetected.

### SUGGESTIONS
- **[refactor-advisor]** `api/dto/WithdrawMoneyRequest.kt:6` — Primitive obsession on `amount: BigDecimal`; a `Money`/`WithdrawalAmount` value object would put the positivity rule in one place.
- **[api-reviewer]** A dedicated `WithdrawalResponse` (amount, resulting balance, timestamp) instead of reusing `AccountResponse`, pairing naturally with `201` + `Location`.
- **[test-reviewer]** `WithdrawMoneyControllerIT.kt:28` — The literal `50` appears untied in both the stub args and the raw JSON body; extract a shared constant.
- **[test-reviewer]** `AccountJpaAdapter.integration.spec.kt:19` — File name doesn't match class `AccountJpaAdapterIT`; rename to `AccountJpaAdapterIT.kt`.

### GOOD PRACTICES
- **[arch-reviewer]** Clean PASS: dependency rule and aggregate-per-package layout respected throughout; domain is framework-free, application depends only on domain, JPA concerns isolated in `infrastructure` and mapped at the boundary, controller never reaches into infrastructure.
- **[api-reviewer]** Thin single-purpose controller (deserialize → delegate → map); correct resource-oriented URL `/accounts/{accountId}/withdrawals`; no domain leakage in responses; validation scope correctly minimal at the DTO; constructor injection.
- **[test-reviewer]** Correct GWT spacing, fakes over mocks, a shared repository contract run against both fake and JPA adapter, clean before-each hygiene.

### Verdict: **FAIL**
Two VIOLATIONS, both the same defect: the missing-account path has no typed domain exception and no HTTP mapping, so it surfaces as a 500 with a leaked message instead of a 404. Fixing that in the use case + a `@ControllerAdvice`, plus the `Account.withdraw` invariant, clears the highest-value warnings too.