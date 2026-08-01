# Reviewer findings — round 2 (deposit) STRICT arm (10: 6 test + 4 refactor)

## test-reviewer (6)
- **VIOLATION** repeated `Account(id, balance)` construction across 4 test files; extract a fixture builder `anAccount(...)`.
- **WARNING** `DepositMoneyControllerIT` — no "missing required field" 400 case (only non-numeric type-parse covered).
- **WARNING** `DepositMoneyUseCaseTest:43` — invariant tested only at the zero boundary, no dedicated negative-amount case.
- **SUGGESTION** repeated `BigDecimal("200"/"50"/"250")` literals; extract named constants.
- **SUGGESTION** fixture-builder recommendation reinforced by the controller IT.
- **NOTE (not a defect)** contract test correctly avoids vacuous full-object `isEqualTo` (identity-only equality).

## refactor-advisor (4)
- **WARNING** `Account.kt` — constructor accepts negative balance; enforce a non-negative invariant in the constructor/factory.
- **SUGGESTION** primitive obsession on `accountId: String`; extract an `AccountId` value object.
- **SUGGESTION** primitive obsession on `BigDecimal` money; introduce a `Money` value object.
- **SUGGESTION** `ApiExceptionHandler` catch-all — confirm it doesn't swallow a type that should map to its own status later.
