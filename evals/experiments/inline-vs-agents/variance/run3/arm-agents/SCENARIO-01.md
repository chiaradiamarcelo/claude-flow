# SCENARIO-01: Successful withdrawal over HTTP from a persisted account

## Scenario

Scenario: Successful withdrawal over HTTP from a persisted account
  Given a persisted account ACC-001 with balance 200
  When a client POSTs a withdrawal of 50 to /accounts/ACC-001/withdrawals
  Then the response status is 200 and the persisted balance is 150

## Structure & Contracts

- **Domain aggregate:** `Account` (`domain/models/account/Account.kt`) — identity `AccountId` (value class wrapping the `ACC-001`-style id); **equality required**. Holds `balance: BigDecimal`. Exposes a `withdraw(amount: BigDecimal): Account` returning a new `Account` with the reduced balance (immutable mutation); enforces Rule 2 (amount strictly positive) and Rule 3 (no overdraft) as invariants, throwing domain exceptions `NonPositiveWithdrawalAmount` and `InsufficientBalance`.
- **Write side:** `AccountRepository` port (`domain/models/account/AccountRepository.kt`) — `save(account: Account): Account`, `findById(id: AccountId): Account?`. Gets `AccountRepository.contract.kt` (same folder) as the abstract contract test; `FakeAccountRepository` (`domain/models/account/fakes/`) and the real JPA adapter (`infrastructure/AccountJpaAdapter.kt`) each run it via their own spec.
- **Persistence:** `AccountEntity` (JPA `@Entity`, `infrastructure/persistence/AccountEntity.kt`) with `id: String` (mapped from `AccountId`), `balance: BigDecimal`; `AccountJpaRepository : JpaRepository<AccountEntity, String>` (Spring Data, internal to the adapter). `AccountJpaAdapter` implements `AccountRepository`, converts `Account` ↔ `AccountEntity` via a mapper method. Schema created via Hibernate `ddl-auto` against H2 for this slice (no separate migration tool in use yet).
- **Use case (write side, required — mutates the aggregate and enforces invariants):** `WithdrawMoneyUseCase` (`application/WithdrawMoneyUseCase.kt`), constructor-injected with `AccountRepository`. Entry point this scenario is verified through: loads the `Account` by id, calls `account.withdraw(amount)`, saves the result, and returns the updated `Account` (or throws `AccountNotFound` if `findById` returns null — needed for the 404 path even though this scenario itself only exercises the success path).
- **API:** `WithdrawMoneyController` (`api/WithdrawMoneyController.kt`) — `POST /accounts/{accountId}/withdrawals`. Request DTO `WithdrawalRequest(amount: BigDecimal)` (`api/dto/`); format-only validation (amount present/parseable). Response: `200 OK` with `WithdrawalResponse(accountId: String, balance: BigDecimal)` (`api/dto/`) reflecting the persisted balance. Maps `AccountNotFound` → `404`, `NonPositiveWithdrawalAmount`/`InsufficientBalance` → `400`. Controller injects `WithdrawMoneyUseCase` only; no business logic in the controller.
- **Wiring:** Spring `@Component`/`@Service`/`@RestController` annotations confined to `infrastructure/` and `api/`; `application/` and `domain/` stay framework-agnostic (no JPA/Spring imports).

## Ordered Test List (FLFI · TPP · Contradiction)

### Unit — WithdrawMoneyUseCaseTest
| # | Test Name (FLFI) | TPP | Contradiction (what the code-so-far wrongly assumes) | Status |
|---|------------------|-----|------------------------------------------------------|--------|
| 1 | returns_the_balance_left_after_the_withdrawal | nil → constant (2) | No code produces an account or a balance at all. | ✅ RED→GREEN — red as `Unresolved reference 'Account'` / `WithdrawMoneyUseCase`; nothing produced a balance yet |
| 2 | subtracts_the_amount_that_was_withdrawn_rather_than_a_fixed_one | constant → scalar (4) | The balance left is the same whatever amount is withdrawn. | ✅ RED→GREEN — red in the same batch; withdrawing 30 from 200 forced the amount to become an argument |
| 3 | subtracts_from_the_balance_the_stored_account_already_had | constant → scalar (4) | The starting balance is hardcoded, so the stored account is never read. | ✅ RED→GREEN — red in the same batch; the 80 seed forced the balance to come from the stored account |
| 4 | saves_the_account_with_the_reduced_balance | statement → statements (5) | The reduced balance is returned but never written back, so it is lost. | ✅ RED→GREEN — red in the same batch; forced the `accounts.save(...)` statement |
| 5 | fails_when_the_withdrawn_amount_is_greater_than_the_balance | unconditional → conditional (6) | Any amount can be withdrawn, so 150 from 100 yields a negative balance. | ✅ RED→GREEN — red in the same batch; forced the overdraft guard in `Account.withdraw` |
| 6 | allows_withdrawing_the_whole_balance | n/a | The overdraft guard uses `>=`, so emptying an account is wrongly rejected. | ✅ RED→GREEN — red in the same batch; pins the guard at `amount > balance`, killing the `>=` mutant |
| 7 | fails_when_the_withdrawn_amount_is_negative | unconditional → conditional (6) | A negative amount is a withdrawal, so it silently increases the balance. | ✅ RED→GREEN — red in the same batch; forced the positivity guard |
| 8 | fails_when_the_withdrawn_amount_is_zero | n/a | The positivity guard uses `< 0`, so a zero withdrawal is accepted as a no-op. | ✅ RED→GREEN — red in the same batch; pins the guard at `amount <= 0`, killing the `< 0` mutant |
| 9 | fails_when_no_account_exists_with_the_given_id | unconditional → conditional (6) | An account is always found, so a missing id blows up instead of reporting not-found. | ✅ RED→GREEN — red in the same batch; forced `AccountNotFound` on a null lookup |

### Unit — AccountTest
| # | Test Name (FLFI) | TPP | Contradiction (what the code-so-far wrongly assumes) | Status |
|---|------------------|-----|------------------------------------------------------|--------|
| 10 | two_accounts_with_the_same_id_are_equal | n/a | Accounts compare by reference or by balance, so the same account after a withdrawal is "a different one". | ✅ RED→GREEN — red with `AssertionFailedError` while `Account` still compared by reference |
| 11 | two_accounts_with_different_ids_are_not_equal | n/a | Equality ignores the id, so any two accounts with the same balance are the same account. | ✅ EARLY-GREEN — reference equality already made it pass; kept because it kills the `equals(other) = other is Account` mutant, verified by applying that mutant and seeing this test alone go red |

### Contract — AccountRepositoryContractTest

Run by `FakeAccountRepositoryTest` (fakes/) and `AccountJpaAdapterIT` (infrastructure/); each row below executes once per implementation.

| # | Test Name (FLFI) | TPP | Contradiction (what the code-so-far wrongly assumes) | Status |
|---|------------------|-----|------------------------------------------------------|--------|
| 12 | returns_a_saved_account_with_every_field_it_was_stored_with | n/a | The round trip preserves the account, so a dropped or mis-mapped balance column is invisible. | ✅ RED→GREEN — red as `Unresolved reference 'AccountJpaAdapter'`, then on the real adapter until the entity mapping existed |
| 13 | returns_nothing_when_no_account_was_saved_with_that_id | n/a | Every lookup finds something, so an unknown id yields an empty or invented account. | ✅ RED→GREEN — red in the same batch until `findById` mapped the empty Optional to null |
| 14 | returns_the_latest_balance_when_the_same_account_is_saved_again | n/a | Saving an existing id inserts a second row, so the withdrawal never overwrites the old balance. | ✅ RED→GREEN — red in the same batch; pins that a second save of the same id updates rather than inserts |

### Controller — WithdrawMoneyControllerIT

Resolved: the mapping lives in a shared `@RestControllerAdvice` (`api/DomainExceptionHandler.kt`), which `@WebMvcTest` includes in the slice by default — no `@Import` needed.

| # | Test Name (FLFI) | TPP | Contradiction (what the code-so-far wrongly assumes) | Status |
|---|------------------|-----|------------------------------------------------------|--------|
| 15 | returns_200_and_the_new_balance_when_the_withdrawal_is_accepted | n/a | No route exists at `POST /accounts/{accountId}/withdrawals`. | ✅ RED→GREEN — red as `Unresolved reference 'WithdrawMoneyController'`; no route existed |
| 16 | returns_400_when_the_request_body_is_malformed | n/a | Every request body parses, so unparseable JSON surfaces as a 500. | ✅ RED→GREEN — red in the same batch; green on Spring's `HttpMessageNotReadableException` → 400, with the use case untouched |
| 17 | returns_400_when_the_amount_is_missing | n/a | A well-formed body is a valid withdrawal, so a missing amount reaches the use case. | ✅ RED→GREEN — red in the same batch; the non-nullable `amount` on the request DTO keeps the call out of the use case |
| 18 | returns_404_when_no_account_exists_with_the_given_id | n/a | `AccountNotFound` is unmapped, so a missing account surfaces as a 500. | ✅ RED→GREEN — red in the same batch; forced the `AccountNotFound` handler on the advice |
| 19 | returns_400_when_the_withdrawal_exceeds_the_balance | n/a | `InsufficientBalance` is unmapped, so an overdraft surfaces as a 500. | ✅ RED→GREEN — red in the same batch; forced the `InsufficientBalance` handler |
| 20 | returns_400_when_the_withdrawn_amount_is_not_positive | n/a | `NonPositiveWithdrawalAmount` is unmapped, so a zero/negative amount surfaces as a 500. | ✅ RED→GREEN — red in the same batch; forced the `NonPositiveWithdrawalAmount` handler |

### Deleted
- `does_not_save_the_account_when_the_withdrawal_is_rejected` — no implementation passes rows 5/7 while still saving.
- `returns_400_when_the_amount_is_not_a_number` — same deserialization path as row 16, no discriminating power.
- `returns_the_account_id_in_the_response` — a facet of row 15's outcome, not a separate behaviour.
- `withdrawing_reduces_the_persisted_balance_end_to_end` — rows 4, 12 and 14 already pin persistence; adds no discriminating power at any level.
