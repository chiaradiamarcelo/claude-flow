# Reviewer findings — round 2 (deposit) BATCH arm (8: 4 test + 4 refactor)

## test-reviewer (4)
- **WARNING** `DepositMoneyControllerIT` — no "missing required field" 400 case (only non-numeric type-parse covered).
- **WARNING** repeated `Account(id, balance)` construction across 4 test files with no fixture builder; extract `anAccount(...)`.
- **SUGGESTION** recurring raw literals (`BigDecimal("200"/"250")`, `"ACC-001"`); give the builder sensible defaults.
- **SUGGESTION** `returns_200_and_the_updated_balance_...` uses "and" in the name (status + payload).

## refactor-advisor (4)
- **WARNING** `Account.kt` — constructor accepts negative balance; add a `require(balance >= ZERO)` invariant.
- **SUGGESTION** primitive obsession on `accountId: String`; consider an `AccountId` value class.
- **SUGGESTION** `ApiExceptionHandler` — uses fully-qualified `HttpStatus` inline instead of importing the type.
- **SUGGESTION** `ApiExceptionHandler` catch-all swallows the exception with no logging.

---
**Note:** as in round 1, the two arms' findings overlap heavily and trace to the *shared plan*
(missing-field 400 not in the test list; `Account` constructor invariant not specified;
primitive `accountId`/`amount`), not to the execution discipline.
