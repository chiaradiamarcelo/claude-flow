# SCENARIO-01: Successful withdrawal over HTTP from a persisted account

```gherkin
Scenario: Successful withdrawal over HTTP from a persisted account
  Given a persisted account ACC-001 with balance 200
  When a client POSTs a withdrawal of 50 to /accounts/ACC-001/withdrawals
  Then the response status is 200 and the persisted balance is 150
```

## Structure & Contracts

- **Domain:** `Account` aggregate root (`domain/models/account/Account.kt`) — `accountId`, `balance: BigDecimal`, `withdraw(amount): Account` returning a new instance; **equality required** (identity = `accountId`). Enforces Rule 2 (strictly positive amount) and Rule 3 (no overdraft).
- **Domain:** `AccountId` value object (`domain/models/account/AccountId.kt`) — wraps the `ACC-001` string.
- **Domain failures:** `InvalidWithdrawalAmountException`, `InsufficientFundsException` (`domain/models/account/`), `AccountNotFoundException` (`domain/models/account/`) — thrown by the aggregate / use case, never returned over the wire.
- **Write side:** `AccountRepository` port (`domain/models/account/AccountRepository.kt`) — `save(account): Account`, `findById(accountId): Account?`. Write side: balance changes cross the aggregate's consistency boundary, so a use case is required.
- **Contract:** abstract `AccountRepositoryContract` (test source set, `domain/models/account/`) — the fake (`domain/models/account/fakes/FakeAccountRepository.kt`, test source set) and the JPA adapter each extend it.
- **Use case:** `WithdrawMoneyUseCase` (`application/WithdrawMoneyUseCase.kt`) — the behavioural entry point; `withdraw(accountId: AccountId, amount: BigDecimal): Account` returning the saved account.
- **Infrastructure:** `AccountJpaAdapter` (`infrastructure/AccountJpaAdapter.kt`) implementing the port over an internal Spring Data interface + `AccountJpaEntity`; explicit field mapping both ways. Its contract run is `AccountJpaAdapterIT` (`@DataJpaTest` against in-memory H2).
- **API:** `POST /accounts/{accountId}/withdrawals` (`api/WithdrawMoneyController.kt`), body `{ "amount": 50 }` → `200` with `{ "accountId": "ACC-001", "balance": 150 }`. One controller per business action.
- **API DTOs:** `WithdrawalRequest(amount: BigDecimal)`, `WithdrawalResponse(accountId, balance)`, `ErrorResponse(code, message)` (`api/dto/`). Format validation only (parseable number, field present); the positivity rule stays in the domain.
- **API error mapping:** `@RestControllerAdvice` (`api/WithdrawalExceptionHandler.kt`) — `AccountNotFoundException` → `404`, `InvalidWithdrawalAmountException` → `400`, `InsufficientFundsException` → `400`; malformed / missing-field bodies → `400`.

## Ordered Test List (FLFI · TPP · Contradiction)

### Unit — WithdrawMoneyUseCaseTest
| # | Test Name (FLFI) | TPP | Contradiction (what the code-so-far wrongly assumes) | Status |
|---|------------------|-----|------------------------------------------------------|--------|
| 1 | returns_the_remaining_balance_when_the_withdrawal_is_accepted | nil → constant (2) | No code reduces or reports a balance at all. | ✅ RED→GREEN — red with `Unresolved reference 'Account'` before the aggregate existed |
| 2 | subtracts_the_amount_that_was_withdrawn_rather_than_a_fixed_one | constant → scalar (4) | The remaining balance is the same whatever amount was withdrawn. | ✅ RED→GREEN — red in the same batch; pins `balance - amount` against a hardcoded 150 |
| 3 | subtracts_from_the_balance_the_account_was_stored_with | constant → scalar (4) | The starting balance is the same whatever the stored account holds. | ✅ RED→GREEN — red in the same batch; pins the stored balance as the minuend |
| 4 | saves_the_reduced_balance_so_a_later_read_returns_it | statement → statements (5) | The reduction exists only in the returned value and is never persisted. | ✅ RED→GREEN — red in the same batch; forced the `accounts.save(...)` call |
| 5 | fails_when_the_amount_exceeds_the_balance | unconditional → conditional (6) | Any amount is withdrawable, so an overdraft would succeed. | ✅ RED→GREEN — red in the same batch; forced the `exceedsBalance` guard |
| 6 | leaves_the_balance_untouched_when_the_amount_exceeds_the_balance | statement → statements (5) | Rejecting the withdrawal is enough; the store may already hold the reduced balance. | ✅ RED→GREEN — red in the same batch; pins the guard as happening before the save |
| 7 | fails_when_the_amount_is_zero | unconditional → conditional (6) | A non-positive amount is a legitimate withdrawal. | ✅ RED→GREEN — red in the same batch; forced the `isNotPositive` guard |
| 8 | fails_when_the_amount_is_negative | unconditional → conditional (6) | Only zero is excluded, so a negative amount would credit the account. | ✅ RED→GREEN — red in the same batch; pins `<=` against `==` in the guard |
| 9 | fails_when_the_account_does_not_exist | unconditional → conditional (6) | Every requested account id resolves to a stored account. | ✅ RED→GREEN — red in the same batch; forced the `?: throw AccountNotFoundException` |

### Unit — AccountTest
| # | Test Name (FLFI) | TPP | Contradiction (what the code-so-far wrongly assumes) | Status |
|---|------------------|-----|------------------------------------------------------|--------|
| 10 | accounts_with_the_same_id_are_equal | n/a | Identity plays no part in equality, so two views of one account compare unequal. | ✅ RED→GREEN — `equals`/`hashCode` had been written ahead of their test, so both were deleted and re-driven; red with `expected: Account@… but was: Account@…` |
| 11 | accounts_with_different_ids_are_not_equal | n/a | Equality ignores the id, so any two accounts compare equal. | ✅ EARLY-GREEN — green under reference equality on the batch-red run, kept as the guard on the `other is Account` half: dropping `other.accountId == accountId` makes it fail |

### Contract — AccountRepositoryContract (run by FakeAccountRepositoryTest and AccountJpaAdapterIT)
| # | Test Name (FLFI) | TPP | Contradiction (what the code-so-far wrongly assumes) | Status |
|---|------------------|-----|------------------------------------------------------|--------|
| 12 | returns_every_stored_field_of_a_saved_account | n/a | The round trip preserves the account, so a dropped or mis-mapped field is invisible. | ✅ RED→GREEN — red with `Unresolved reference 'AccountJpaAdapter'` before the adapter existed |
| 13 | returns_nothing_for_an_id_that_was_never_saved | n/a | A lookup always finds an account. | ✅ RED→GREEN — after the adapter compiled it still failed (`expected: null but was: Account@…`): the `@DataJpaTest` slice was not rolling rows back, so a preceding test's account leaked. Fixed with a before-each `deleteAll()` |
| 14 | returns_the_latest_balance_after_the_same_account_is_saved_again | n/a | Saving inserts a second copy instead of replacing the stored account. | ✅ RED→GREEN — red with `Unresolved reference 'AccountJpaAdapter'` before the adapter existed |
| 15 | returns_the_account_asked_for_rather_than_another_stored_one | n/a | Lookup ignores the id and returns whatever was stored. | ✅ RED→GREEN — red with `Unresolved reference 'AccountJpaAdapter'` before the adapter existed |

### Controller — WithdrawMoneyControllerIT
| # | Test Name (FLFI) | TPP | Contradiction (what the code-so-far wrongly assumes) | Status |
|---|------------------|-----|------------------------------------------------------|--------|
| 16 | returns_200_and_the_remaining_balance_when_the_withdrawal_is_accepted | n/a | No route exists at all. | ✅ RED→GREEN — red with `Unresolved reference 'WithdrawMoneyController'` before the route existed |
| 17 | withdraws_the_requested_amount_from_the_account_in_the_path | n/a | The path id and the body amount need not reach the use case. | ✅ RED→GREEN — red in the same batch; pins the `AccountId(accountId)` / `request.amount` wiring |
| 18 | returns_400_when_the_body_is_not_valid_json | n/a | Any request body can be deserialized. | ✅ RED→GREEN — red in the same batch |
| 19 | returns_400_when_the_amount_is_missing | n/a | The amount field is always present. | ✅ RED→GREEN — red in the same batch; pins the non-nullable `amount` on the request DTO |
| 20 | returns_400_when_the_amount_is_not_a_number | n/a | The amount field always parses as a number. | ✅ RED→GREEN — red in the same batch |
| 21 | returns_400_when_the_amount_is_not_positive | n/a | A domain invariant violation is an unhandled server error. | ✅ RED→GREEN — red in the same batch; forced the `InvalidWithdrawalAmountException` → 400 mapping |
| 22 | returns_400_when_the_amount_exceeds_the_balance | n/a | An overdraft attempt is an unhandled server error. | ✅ RED→GREEN — red in the same batch; forced the `InsufficientFundsException` → 400 mapping |
| 23 | returns_404_when_the_account_does_not_exist | n/a | A missing account is an unhandled server error. | ✅ RED→GREEN — red in the same batch; forced the `AccountNotFoundException` → 404 mapping |

### Deleted
- `persists_the_reduced_balance_over_http` (end-to-end) — no discriminating power over rows 4, 12 and 16 once the adapter runs the contract.
- `returns_the_account_id_in_the_response` — row 16 already pins the whole response body.
