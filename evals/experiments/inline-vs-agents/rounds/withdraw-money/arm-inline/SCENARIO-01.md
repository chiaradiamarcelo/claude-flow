# SCENARIO-01: Successful withdrawal over HTTP from a persisted account

```gherkin
Scenario: Successful withdrawal over HTTP from a persisted account
  Given a persisted account ACC-001 with balance 200
  When a client POSTs a withdrawal of 50 to /accounts/ACC-001/withdrawals
  Then the response status is 200 and the persisted balance is 150
```

## Structure & Contracts

- **Domain:** `Account` aggregate root (`domain/models/account/`) — `id`, `balance` (`BigDecimal`); `withdraw(amount)` returns a new `Account`; **equality required** (identity = id).
- **Domain failures:** `WithdrawalAmountNotPositive`, `InsufficientFunds` (`domain/models/account/`) — raised by `Account.withdraw`, so every entry point hits the same invariant.
- **Write side:** `AccountRepository` port (`domain/models/account/`) — `save(account)`, `findById(id): Account?`. Write side because the withdrawal mutates the aggregate, so a use case is required.
- **Contract:** `AccountRepositoryContract` abstract test (test source set, same package) — `FakeAccountRepository` (`domain/models/account/fakes/`) and the JPA adapter each extend it. Its full-projection row asserts `id` **and** `balance`, because `Account` equality is identity-only and would otherwise hide a dropped balance.
- **Use case:** `WithdrawMoneyUseCase` (`application/`) — `withdraw(accountId, amount): Account`; throws `AccountNotFound` (`application/`) for an unknown id; lets the domain failures propagate. The behavioural entry point this scenario is verified through.
- **Infrastructure:** `AccountJpaAdapter` (`infrastructure/`) implements the port over a `AccountEntity` + Spring Data interface kept internal to the adapter; explicit field mapping both ways.
- **API:** `POST /accounts/{accountId}/withdrawals`, body `{"amount": 50}` → `200` with `{"accountId": "...", "balance": 150}`. One controller per business action: `WithdrawMoneyController` (`api/`), DTOs in `api/dto/`.
- **Status mapping** (`ApiExceptionHandler`, `@RestControllerAdvice` in `api/`): `AccountNotFound` → `404`; `WithdrawalAmountNotPositive` / `InsufficientFunds` → `400`. Malformed body, missing `amount`, non-numeric `amount` → `400` via the non-nullable Kotlin request DTO (Jackson parse failure), no hand-rolled checks.

## Ordered Test List (FLFI · TPP · Contradiction)

### Unit — WithdrawMoneyUseCaseTest

| # | Test Name (FLFI) | TPP | Contradiction (what the code-so-far wrongly assumes) | Status |
|---|------------------|-----|------------------------------------------------------|--------|
| 1 | returns_the_balance_left_after_the_withdrawal | nil → constant (2) | No code produces a balance at all. | ✅ RED→GREEN — red as an unresolved reference to WithdrawMoneyUseCase, then 150 |
| 2 | subtracts_the_amount_that_was_withdrawn_rather_than_a_fixed_one | constant → scalar (4) | The balance left is the same whatever amount is withdrawn. | ✅ RED→GREEN — same batch red; a hard-coded 150 would fail this row at 170 |
| 3 | saves_the_account_with_the_reduced_balance | statement → statements (5) | The reduced balance exists only in the reply and is never stored. | ✅ RED→GREEN — same batch red; asserts the stored account, not the returned one |
| 4 | fails_when_no_account_is_stored_with_the_given_id | unconditional → conditional (6) | Every account id resolves to a stored account. | ✅ RED→GREEN — same batch red; AccountNotFound raised for an unstored id |
| 5 | fails_when_the_amount_exceeds_the_balance | unconditional → conditional (6) | Any amount may be taken from any balance. | ✅ RED→GREEN — same batch red; InsufficientFunds raised for 250 over a balance of 200 |
| 6 | allows_a_withdrawal_of_the_whole_balance | unconditional → conditional (6) | The balance itself is already too much to withdraw. | ✅ RED→GREEN — same batch red; kept as the boundary guard — the mutant `amount >= balance` reddens it |
| 7 | fails_when_the_amount_is_negative | unconditional → conditional (6) | Any amount is a legitimate withdrawal. | ✅ RED→GREEN — same batch red; WithdrawalAmountNotPositive raised for -10 |
| 8 | fails_when_the_amount_is_zero | unconditional → conditional (6) | Only a strictly negative amount is illegitimate. | ✅ RED→GREEN — same batch red; the mutant `amount < ZERO` reddens it |

### Unit — AccountTest

| # | Test Name (FLFI) | TPP | Contradiction (what the code-so-far wrongly assumes) | Status |
|---|------------------|-----|------------------------------------------------------|--------|
| 9 | two_accounts_with_the_same_id_are_equal | n/a | Two loads of one account are different objects. | ✅ RED→GREEN — equals was removed and redriven; red with "expected ACC-001 to be equal to ACC-001" on object identity |
| 10 | two_accounts_with_different_ids_are_not_equal | n/a | Identity plays no part in telling accounts apart. | ✅ EARLY-GREEN — green without equals; kept because the mutant `equals = true` reddens it |

### Contract — AccountRepositoryContract

| # | Test Name (FLFI) | TPP | Contradiction (what the code-so-far wrongly assumes) | Status |
|---|------------------|-----|------------------------------------------------------|--------|
| 11 | returns_every_stored_field_of_a_saved_account | n/a | The round trip preserves the account, so a dropped balance is invisible. | ✅ RED→GREEN — red as an unresolved reference to AccountJpaAdapter; asserts id and balance because Account equality is identity-only |
| 12 | returns_nothing_when_no_account_was_stored_with_that_id | n/a | Every id asked for has a stored account behind it. | ✅ RED→GREEN — same batch red; Optional.empty maps to null |
| 13 | returns_the_latest_balance_when_the_same_account_is_saved_again | n/a | An account is stored once and never written over. | ✅ RED→GREEN — same batch red; the second save overwrites rather than inserting |

### Contract impls — FakeAccountRepositoryTest, AccountJpaAdapterIT

| # | Test Name (FLFI) | TPP | Contradiction (what the code-so-far wrongly assumes) | Status |
|---|------------------|-----|------------------------------------------------------|--------|
| 14 | the fake satisfies AccountRepositoryContract | n/a | The fake may behave unlike the stored-for-real adapter the tests stand in for. | ✅ EARLY-GREEN — the fake predates the contract; kept because the mutant "save ignores a repeat id" reddens row 13 for it |
| 15 | the JPA adapter satisfies AccountRepositoryContract | n/a | Mapping to and from the database preserves the account. | ✅ RED→GREEN — adapter did not exist; also forced adding the spring-boot-data-jpa-test slice module |

### Controller — WithdrawMoneyControllerIT

| # | Test Name (FLFI) | TPP | Contradiction (what the code-so-far wrongly assumes) | Status |
|---|------------------|-----|------------------------------------------------------|--------|
| 16 | returns_200_and_the_balance_left_when_the_withdrawal_is_accepted | n/a | No route exists at all. | ✅ RED→GREEN — red as an unresolved reference to WithdrawMoneyController |
| 17 | withdraws_the_requested_amount_from_the_account_named_in_the_path | n/a | The path id and the body amount need not reach the use case. | ✅ RED→GREEN — same batch red; pins that the path id and body amount both reach the use case |
| 18 | returns_400_when_the_request_body_is_malformed | n/a | Every request body parses. | ✅ RED→GREEN — same batch red; Jackson parse failure maps to 400 |
| 19 | returns_400_when_the_amount_is_missing | n/a | A body that parses carries an amount. | ✅ RED→GREEN — same batch red; the non-nullable Kotlin DTO field rejects a missing amount |
| 20 | returns_400_when_the_amount_is_not_a_number | n/a | Whatever is sent as the amount is a number. | ✅ RED→GREEN — same batch red; "fifty" is not coercible to BigDecimal |
| 21 | returns_400_when_the_amount_exceeds_the_balance | n/a | A domain rule breach is an unexpected server fault. | ✅ RED→GREEN — same batch red; ApiExceptionHandler maps InsufficientFunds to 400, not 500 |
| 22 | returns_404_when_no_account_is_stored_with_the_given_id | n/a | An unknown account is an unexpected server fault. | ✅ RED→GREEN — same batch red; ApiExceptionHandler maps AccountNotFound to 404 |

### Deleted

- `returns_the_account_id_in_the_response` — no discriminating power over row 16, which pins the whole payload.
- `fails_when_the_account_id_is_blank` — the spec defines no such rule; row 4 already covers ids with no account behind them.
- `persists_the_balance_end_to_end_over_http` — rows 3, 15 and 16 cover each seam; a full-stack duplicate adds cost, not discrimination.
