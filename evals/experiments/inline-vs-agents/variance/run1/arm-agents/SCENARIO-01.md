# SCENARIO-01: Successful withdrawal over HTTP from a persisted account

## Scenario

Scenario: Successful withdrawal over HTTP from a persisted account
  Given a persisted account ACC-001 with balance 200
  When a client POSTs a withdrawal of 50 to /accounts/ACC-001/withdrawals
  Then the response status is 200 and the persisted balance is 150

## Structure & Contracts

- **Domain aggregate:** `Account` (`domain/models/account/Account.kt`) — identified by `accountId` (e.g. `ACC-001`); **equality required**. Owns `balance` and a `withdraw(amount)` behaviour enforcing Rule 2 (amount strictly positive) and Rule 3 (no overdraft); returns a new `Account` instance reflecting Rule 4.
- **Write-side port:** `AccountRepository` (`domain/models/account/AccountRepository.kt`) — `save(account)`, `findById(accountId)`. Gets `AccountRepository.contract.kt` next to it; `FakeAccountRepository` (`domain/models/account/fakes/`) and `AccountRepositoryJpaAdapter` (`infrastructure/`) each run the contract via their own spec.
- **Persistence:** `AccountEntity` JPA entity + Spring Data `AccountJpaRepository` internal to the adapter (`infrastructure/`), mapped to/from `Account` in the adapter. Schema via a migration/`schema.sql` or `ddl-auto` against H2, matching `AccountEntity` fields (`accountId`, `balance`).
- **Use case (write side):** `WithdrawMoneyUseCase` (`application/`) — takes `AccountRepository`, loads the account by id, applies `Account.withdraw(amount)`, saves the result. This scenario's behavioural entry point; returns the updated `Account` (or a Result wrapping it) for the controller to map.
- **API:** `WithdrawMoneyController` — `POST /accounts/{accountId}/withdrawals` → `200 OK` with a `WithdrawalResponse` body reflecting the new balance. Request DTO `WithdrawalRequest` (`api/dto/`) carries the raw `amount`; format-only validation at this layer (numeric, present). Domain invariant violations (non-positive amount, overdraft) and missing account surface via domain exceptions mapped at the controller/exception-filter boundary — out of scope for this scenario's happy path but the mapping point must exist for later scenarios to attach to.

## Ordered Test List (FLFI · TPP · Contradiction)

### Unit — WithdrawMoneyUseCaseTest

> Note to architect: the failure channel is unnamed — `Account.withdraw` rejecting a non-positive amount, rejecting an overdraft, and a missing account id need three distinguishable outcomes (distinct exception types or a Result variant each). Rows 5–7 are designed against distinct named failures.

| # | Test Name (FLFI) | TPP | Contradiction (what the code-so-far wrongly assumes) | Status |
|---|------------------|-----|------------------------------------------------------|--------|
| 1 | returns_the_balance_left_after_the_withdrawal | nil → constant (2) | Nothing computes or returns a balance for a withdrawal. | ✅ RED→GREEN — red as unresolved `WithdrawMoneyUseCase`/`Account` before any of them existed |
| 2 | subtracts_the_amount_that_was_withdrawn_rather_than_a_fixed_one | constant → scalar (4) | The remaining balance is the same whatever amount was withdrawn. | ✅ RED→GREEN — red in the same compile-failure batch; forced `amount` into the subtraction |
| 3 | subtracts_from_the_balance_the_stored_account_already_had | constant → scalar (4) | The stored balance is ignored; two accounts with different balances give the same result. | ✅ RED→GREEN — red in the same batch; forced the loaded account's `balance` into the subtraction |
| 4 | saves_the_account_with_the_reduced_balance | statement → statements (5) | The new balance is only returned; reloading the account still shows the old balance. | ✅ RED→GREEN — red in the same batch; forced the `accounts.save(...)` call |
| 5 | fails_when_the_withdrawn_amount_is_not_positive | unconditional → conditional (6) | Any amount is a withdrawal, so 0 changes nothing and -50 grows the balance. | ✅ RED→GREEN — red as unresolved `InvalidWithdrawalAmountException` |
| 6 | fails_when_the_withdrawn_amount_exceeds_the_balance | unconditional → conditional (6) | Every amount is affordable; 250 from 200 succeeds and leaves a negative balance. | ✅ RED→GREEN — red as unresolved `InsufficientFundsException` |
| 7 | fails_when_no_account_exists_with_the_given_id | unconditional → conditional (6) | The lookup always yields an account, so an unknown id is never rejected. | ✅ RED→GREEN — red as unresolved `AccountNotFoundException` |

### Unit — AccountTest

| # | Test Name (FLFI) | TPP | Contradiction (what the code-so-far wrongly assumes) | Status |
|---|------------------|-----|------------------------------------------------------|--------|
| 8 | is_equal_to_another_account_with_the_same_id | n/a | Accounts compare by reference, so a reloaded account never equals the expected one. | ✅ RED→GREEN — red with `AssertionFailedError` against reference equality before `equals`/`hashCode` existed |
| 9 | is_not_equal_to_an_account_with_a_different_id | n/a | Equality ignores the id, so two different accounts compare as the same one. | ✅ EARLY-GREEN — reference equality already made it pass; kept because it is the only test that kills the mutant `equals` comparing `balance` instead of `accountId` (both accounts hold 200) |

### Contract — AccountRepositoryContractTest

Suite lives in `AccountRepository.contract.kt` as `AccountRepositoryContract`; run twice, by `FakeAccountRepositoryTest` and by `AccountRepositoryJpaAdapterIT`. Each row's status below describes the JPA runner; against the fake all three were `EARLY-GREEN` (the fake was written in the use-case batch), and they are kept because they are what holds the fake and the adapter behaviourally interchangeable.

| # | Test Name (FLFI) | TPP | Contradiction (what the code-so-far wrongly assumes) | Status |
|---|------------------|-----|------------------------------------------------------|--------|
| 10 | returns_a_saved_account_with_every_field_it_was_stored_with | n/a | The round trip preserves the account, so a dropped or mis-mapped balance column is invisible. | ✅ RED→GREEN — red as unresolved `AccountRepositoryJpaAdapter`; green after the adapter; re-reddened on demand by mapping `balance` to ZERO |
| 11 | returns_nothing_when_no_account_was_saved_with_that_id | n/a | A lookup always finds something; an unknown id yields a blank account instead of nothing. | ✅ RED→GREEN — red as unresolved adapter; green once `findById` returned null for an absent row |
| 12 | returns_the_latest_balance_when_the_same_account_is_saved_again | n/a | Saving always inserts, so a withdrawal leaves the original balance readable. | ✅ RED→GREEN — red as unresolved adapter; also caught the ZERO-mapping mutant |

### Controller — WithdrawMoneyControllerIT

> Note to architect: no error payload shape is defined for the 400/404 responses; rows 14–17 assert status only until one is specified.

| # | Test Name (FLFI) | TPP | Contradiction (what the code-so-far wrongly assumes) | Status |
|---|------------------|-----|------------------------------------------------------|--------|
| 13 | returns_200_and_the_remaining_balance_when_the_withdrawal_succeeds | n/a | No route exists at `POST /accounts/{accountId}/withdrawals`. | ✅ RED→GREEN — red as unresolved `WithdrawMoneyController` before the route existed |
| 14 | returns_400_when_the_request_body_is_malformed | n/a | Any body parses, so unparseable input reaches the use case or surfaces as 500. | ✅ RED→GREEN — red in the same batch; green from Jackson's parse failure, no business annotation involved |
| 15 | returns_400_when_the_amount_is_missing | n/a | A body without an amount is a valid withdrawal request. | ✅ RED→GREEN — red in the same batch; green from `WithdrawalRequest.amount` being non-nullable |
| 16 | returns_400_when_the_withdrawal_is_rejected_by_a_domain_rule | n/a | Domain rule failures are unmapped and escape as 500. | ✅ RED→GREEN — red in the same batch; forced `DomainExceptionHandler` to map `WithdrawalRuleViolationException` |
| 17 | returns_404_when_no_account_exists_with_the_given_id | n/a | The account always exists, so the missing-account failure is unmapped. | ✅ RED→GREEN — red in the same batch; forced the separate `AccountNotFoundException` mapping |

### Deleted
- `returns_400_when_the_amount_is_not_a_number` — same parse-failure path as row 14; no discriminating power.
- `returns_400_when_the_amount_exceeds_the_balance` — overdraft is a domain outcome already pinned by rows 6 and 16.
- `returns_the_account_id_in_the_response` — indistinguishable from row 13 under a mocked use case.
- `returns_the_new_account_instance_without_mutating_the_original` — no mutation any row's contradiction can expose.
