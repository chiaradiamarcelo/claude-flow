## Ad-hoc Review Report

### Target
`src` (24 files)

### Triggered reviewers
- **arch-reviewer** (`**/src/main/**`): 15 main files
- **refactor-advisor** (`**/src/main/**`): 15 main files
- **test-reviewer** (`**/src/test/**`, `**/*Test.*`, `**/*IT.*`): 9 test files
- **api-reviewer** (`**/api/**`, `**/dto/**`): 5 api/dto main files + `WithdrawMoneyControllerIT.kt`

### Skipped reviewers
- **ui-test-reviewer**: no `*.test.tsx/jsx` files
- **android-ui-test-reviewer**: no `androidTest/` sources
- **android-presentation-reviewer**: no `presentation/` package

### VIOLATIONS (must fix)
- **[api-reviewer]** `src/main/kotlin/com/example/bank/api/WithdrawMoneyController.kt:20` — URL/status mismatch: `POST /accounts/{accountId}/withdrawals` is a POST-to-collection (resource creation) but returns the default `200 OK` with no created-withdrawal id or `Location` header. Either return `201 Created` with a `Location`, or model the endpoint as an action rather than a collection.

### WARNINGS (should fix)
- **[refactor-advisor]** `domain/models/account/Account.kt:5` — no constructor invariant on `balance`. `withdraw()` guards the overdraft, but `AccountJpaAdapter.toAccount` (`AccountJpaAdapter.kt:37`) rebuilds `Account` straight from stored data, so a negative balance is representable. Guard in `init`/a factory.
- **[api-reviewer]** `WithdrawMoneyController.kt:16` — no idempotency strategy on a retryable money-moving POST (no `Idempotency-Key`, no client-supplied withdrawal id). A retry after timeout can double-withdraw.
- **[test-reviewer]** `WithdrawMoneyControllerIT.kt:21` — the controller slice never exercises `WithdrawalAmountNotPositive → 400`; that path is only covered at the use-case level.
- **[test-reviewer]** `AccountJpaAdapterIT.kt:9` — `@DataJpaTest` runs against a schema from `ddl-auto=create-drop` with no migration tool in the build, so the adapter contract test cannot catch schema drift.

### SUGGESTIONS
- **[refactor-advisor]** `Account.kt:6` — primitive obsession on `id: String`, threaded through repository, use case, exceptions, and `@PathVariable`. Extract an `AccountId` value class.
- **[refactor-advisor]** `Account.kt:14` — same for `amount: BigDecimal`; a `Money`/`WithdrawalAmount` value object would make a non-positive amount unrepresentable at construction.
- **[api-reviewer]** `dto/WithdrawalResponse.kt:5` — the response describes account state (`accountId`, `balance`) rather than the withdrawal the URL says was created.
- **[test-reviewer]** `WithdrawMoneyUseCaseTest.kt:28` — `amount(200)` repeated verbatim across tests and in `AccountRepositoryContract`; extract a named constant.

### GOOD PRACTICES
- **[arch-reviewer]** All 15 main files respect the dependency rule: domain is framework-free, the use case depends only on domain, `api/` depends only on application + domain, and infrastructure implements/wires the port without leaking.
- **[test-reviewer]** Clean GWT separation, fakes over mocks, and a shared `AccountRepositoryContract` satisfied by both the fake and the real JPA adapter, plus a dedicated equality test.
- **[api-reviewer]** Thin single-action controller, format-only DTO validation, consistent error shape, no domain leakage into responses.

### Verdict: FAIL
One violation (status-code/URL semantics in `WithdrawMoneyController`). The four warnings and four suggestions are reported for you to triage — they do not by themselves fail the review.