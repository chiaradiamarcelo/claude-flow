# Reviewer findings — BATCH arm (7 total)

## test-reviewer (4)
- **WARNING** `AccountTest.kt` / `WithdrawMoneyUseCaseTest.kt` — domain invariants tested on the entity, not through the use case; the use case never asserts it surfaces `InsufficientFundsException` / `InvalidWithdrawalAmountException`.
- **WARNING** `WithdrawMoneyControllerIT.kt` — no malformed-input / parse-error 400 case (only missing-field + domain-invariant covered).
- **SUGGESTION** `WithdrawMoneyControllerIT.kt` — repeated `{"amount":50}` request-body literal across 4 tests; extract a named constant.
- **SUGGESTION** `AccountRepositoryContractTest.kt` — the full-object `isEqualTo` assertion doesn't pin `balance` (identity-only equality); the explicit `balance()` assertion carries it — worth a comment/restructure.

## refactor-advisor (3)
- **WARNING** `Account.kt` — public constructor accepts any `accountId` (incl. blank) and any `balance` (incl. negative); add an `init`/factory invariant.
- **SUGGESTION** `Account.kt` (+ port, use case, controller, adapter) — primitive obsession on `accountId: String`; extract an `AccountId` value object.
- **SUGGESTION** `Account.kt` — primitive obsession on `BigDecimal` money; introduce a `Money` / `WithdrawalAmount` value object.

---
**Note:** these findings are essentially identical to the strict arm's — both trace to the
*shared plan* (no malformed-JSON test row; use-case invariant coverage delegated to the entity;
`Account` constructor invariant not specified), not to the execution discipline.
