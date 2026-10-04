# SCENARIO-01: Successful withdrawal over HTTP from a persisted account

## Scenario

Scenario: Successful withdrawal over HTTP from a persisted account
  Given a persisted account ACC-001 with balance 200
  When a client POSTs a withdrawal of 50 to /accounts/ACC-001/withdrawals
  Then the response status is 200 and the persisted balance is 150

## Structure & Contracts

- **Domain aggregate:** `Account` (`domain/models/account/Account.kt`) — identified by `AccountId` (e.g. `ACC-001`); **equality required**. Holds `balance` (use `BigDecimal` for money). Exposes a `withdraw(amount)` behavior that enforces Rule 2 (amount strictly positive) and Rule 3 (no overdraft), returning a new `Account` instance with the reduced balance.
- **Domain exceptions:** `InvalidWithdrawalAmountException` and `InsufficientBalanceException` (or a shared `DomainException` hierarchy) in `domain/models/account/` — raised by `Account.withdraw`.
- **Write-side port:** `AccountRepository` (`domain/models/account/AccountRepository.kt`) — `save(Account)`, `findById(AccountId): Account?`. Gets `AccountRepository.contract.kt` next to it (abstract contract test). `FakeAccountRepository` (`domain/models/account/fakes/`) and `AccountJpaRepositoryAdapter` (`infrastructure/`) each extend the contract via their own spec.
- **Persistence:** `AccountEntity` JPA entity + Spring Data `AccountJpaRepository` (framework-internal, used only inside the adapter) in `infrastructure/`; mapper functions `Account.toEntity()` / `AccountEntity.toDomain()` colocated with the adapter. Schema created via JPA/H2 (in-memory) — no separate migration tool needed for this slice.
- **Use case (write side):** `WithdrawMoneyUseCase` (`application/WithdrawMoneyUseCase.kt`) — constructor-injects `AccountRepository`; loads the account by id, invokes `Account.withdraw(amount)`, persists via `save`, and is the behavioural entry point this scenario is verified through. Returns the updated `Account` (or a `Result`-style success/failure wrapping domain exceptions) for the controller to map.
- **API:** `WithdrawMoneyController` (`api/WithdrawMoneyController.kt`) — `POST /accounts/{accountId}/withdrawals`, request DTO `WithdrawMoneyRequest` (`api/dto/`, format-only validation: amount present and parseable as a positive-shaped number type) and response DTO `AccountResponse` (`api/dto/`, exposes `accountId`, `balance` — no domain entity returned directly). Success → `200` with the updated balance. Maps `AccountNotFoundException` → `404`, `InvalidWithdrawalAmountException`/`InsufficientBalanceException` → `400`. Controller stays thin: deserialize → call `WithdrawMoneyUseCase` → map response.

## Ordered Test List (FLFI · TPP · Contradiction)

### Unit — WithdrawMoneyUseCaseTest
| # | Test Name (FLFI) | TPP | Contradiction (what the code-so-far wrongly assumes) | Status |
|---|------------------|-----|------------------------------------------------------|--------|
| 1 | returns_the_remaining_balance_after_withdrawing_from_the_account | nil → constant (2) | No code produces or returns a balance at all. | ✅ RED→GREEN — red as `Unresolved reference 'AccountId'`/`Account`; nothing produced a balance |
| 2 | subtracts_the_withdrawn_amount_rather_than_a_fixed_one | constant → scalar (4) | The remaining balance is the same whatever amount was withdrawn. | ✅ RED→GREEN — red in the same batch-red compile; forced `balance - amount` rather than a literal 150 |
| 3 | subtracts_the_amount_from_the_balance_the_account_already_had | constant → scalar (4) | The stored account's balance is ignored; the result is computed from the amount alone. | ✅ RED→GREEN — forced the subtraction to read the loaded account's balance (seed 500 → 450) |
| 4 | saves_the_account_with_the_reduced_balance | statement → statements (5) | The reduced balance is only returned; reloading the account still shows the original balance. | ✅ RED→GREEN — forced the `accounts.save(withdrawn)` statement alongside the return |
| 5 | fails_when_the_withdrawn_amount_is_not_positive | unconditional → conditional (6) | Any amount is a withdrawal, so 0 passes and -50 grows the balance. | ✅ RED→GREEN — behavioural red against the unguarded `withdraw`: no exception thrown for amount 0 |
| 6 | fails_when_the_withdrawn_amount_exceeds_the_balance | unconditional → conditional (6) | Every withdrawal is allowed, so withdrawing 250 from 200 leaves -50. | ✅ RED→GREEN — behavioural red against the unguarded `withdraw`: 250 from 200 silently returned -50 |
| 7 | withdraws_the_whole_balance_when_the_amount_equals_it | n/a | The overdraft guard rejects amounts >= balance, so emptying the account fails. | ✅ RED→GREEN — red at batch-red compile; pins the guard as `amount > balance`, not `>=` |
| 8 | fails_when_no_account_exists_for_the_requested_id | unconditional → conditional (6) | Every id resolves to an account, so a missing id crashes instead of reporting not-found. | ✅ RED→GREEN — behavioural red: `!!` on the missing account threw NullPointerException, not AccountNotFoundException |

> Note to architect: the status mapping cites `AccountNotFoundException` but the domain exceptions list does not declare it. Row 8 is designed against an `AccountNotFoundException` (or equivalent not-found failure) signalled by the use case when `findById` yields nothing.
>
> Resolved: `AccountNotFoundException` is declared in `domain/models/account/AccountExceptions.kt` beside the other two, and thrown by `WithdrawMoneyUseCase` when `findById` returns null. It sits in the domain rather than the application layer because "no such account" is domain vocabulary, and because the 404 mapping in `DomainExceptionHandler` needs a type the api layer is allowed to import.

### Unit — AccountTest
| # | Test Name (FLFI) | TPP | Contradiction (what the code-so-far wrongly assumes) | Status |
|---|------------------|-----|------------------------------------------------------|--------|
| 9 | treats_two_accounts_with_the_same_id_as_equal | n/a | Equality is reference-based, so a reloaded account never equals the expected one. | ✅ RED→GREEN — red with `expected: Account@… but was: Account@…` before `equals`/`hashCode` were defined on the id |
| 10 | treats_two_accounts_with_different_ids_as_not_equal | n/a | Equality ignores the id, so any two accounts compare equal. | ✅ EARLY-GREEN — passed on the batch-red run because the default equality is reference-based. Kept: the mutant `other is Account` (equality that ignores the id, the obvious over-broad `equals`) turns it red while row 9 stays green |

### Contract — AccountRepositoryContractTest

Executed twice — by `FakeAccountRepositoryTest` and by `AccountJpaRepositoryAdapterIT`.

| # | Test Name (FLFI) | TPP | Contradiction (what the code-so-far wrongly assumes) | Status |
|---|------------------|-----|------------------------------------------------------|--------|
| 11 | returns_a_saved_account_with_every_field_it_was_stored_with | n/a | The round trip preserves the account, so a dropped or mis-mapped balance column is invisible. | ✅ RED→GREEN — red as `Unresolved reference 'AccountJpaRepositoryAdapter'`; drove the entity, the column mapping and both mappers. Asserts the fields, not `isEqualTo(account)`, because `Account` equality is id-only |
| 12 | returns_nothing_when_no_account_was_saved_with_that_id | n/a | A lookup always yields an account. | ✅ RED→GREEN — red twice: first at compile, then against the adapter with `expected: null but was: Account@…`, which exposed the leaked-state defect recorded in SCENARIO-01.record.md |
| 13 | returns_the_latest_balance_when_the_same_account_is_saved_again | n/a | Saving an existing id inserts a second account instead of replacing the stored one. | ✅ RED→GREEN — red at compile; pins `save` as a merge on the assigned id rather than an insert |

### Controller — WithdrawMoneyControllerIT
| # | Test Name (FLFI) | TPP | Contradiction (what the code-so-far wrongly assumes) | Status |
|---|------------------|-----|------------------------------------------------------|--------|
| 14 | returns_200_and_the_remaining_balance_when_the_withdrawal_is_accepted | n/a | No route exists at all. | ✅ RED→GREEN — red as `Unresolved reference 'WithdrawMoneyController'`; drove the route, both DTOs and the `Account → AccountResponse` mapper |
| 15 | returns_400_when_the_request_body_is_malformed | n/a | Any request body deserializes into a withdrawal. | ✅ RED→GREEN — red in the same batch-red compile; satisfied by Spring's `HttpMessageNotReadableException` handling once the route existed |
| 16 | returns_400_when_the_amount_is_missing | n/a | The amount is optional, so a body without it reaches the use case. | ✅ RED→GREEN — red in the same batch-red compile; pins `amount` as a non-nullable `BigDecimal`. The mutant `amount: BigDecimal?` makes it 500, not 400 |
| 17 | returns_400_when_the_withdrawn_amount_is_rejected_as_invalid | n/a | `InvalidWithdrawalAmountException` is unmapped and surfaces as 500. | ✅ RED→GREEN — red at compile; drove `DomainExceptionHandler.withdrawalRejected` |
| 18 | returns_400_when_the_balance_is_insufficient | n/a | `InsufficientBalanceException` is unmapped and surfaces as 500. | ✅ RED→GREEN — red at compile; drove the second exception type on the same 400 handler |
| 19 | returns_404_when_no_account_exists_for_the_requested_id | n/a | Every path id names an existing account, so not-found surfaces as 500. | ✅ RED→GREEN — red at compile; drove `DomainExceptionHandler.accountNotFound` and confirms 404 is distinct from the 400 mapping |

### Deleted
- `returns_400_when_the_amount_is_not_a_number` — same deserialization path and outcome as row 15; no discriminating power.
- `returns_the_account_id_in_the_response` — no discriminating power over row 14 under a mocked use case.
- `fails_when_the_withdrawn_amount_is_negative` — folded into row 5; the non-positive rule covers 0 and negatives with one guard.
- `returns_500_when_the_repository_fails` — no unexpected-failure mapping is defined in the structure.
