# Reviewer findings — STRICT arm (8 total)

## test-reviewer (5)
- **WARNING** `WithdrawMoneyControllerIT.kt` — no malformed-input / type-parsing 400 case (only missing-field + domain-invariant covered).
- **WARNING** `WithdrawMoneyControllerIT.kt` — repeated `mockMvc.perform(post(...))` block across all 6 tests; extract a request-builder helper.
- **WARNING** `WithdrawMoneyUseCaseTest.kt` — use case never exercises `InsufficientFundsException` / `InvalidWithdrawalAmountException` propagation; invariants proven only on the bare entity without combinatorial justification.
- **SUGGESTION** `WithdrawMoneyUseCaseTest.kt` — `withdraws_..._and_returns_...` has an "and" in the name though it asserts one fact.
- **SUGGESTION** `WithdrawMoneyControllerIT.kt` — repeated `{"amount":50}` literal; derive from the shared constant.

## refactor-advisor (3)
- **WARNING** `Account.kt` — constructor accepts any balance (incl. negative); enforce a non-negative invariant in the constructor/factory.
- **SUGGESTION** `Account.kt` / `AccountRepository.kt` / `WithdrawMoneyUseCase.kt` / `WithdrawalResponse.kt` — primitive obsession on `accountId: String`; extract an `AccountId` value object.
- **SUGGESTION** `Account.kt` — primitive obsession on `BigDecimal` money; consider a `Money` value object.
