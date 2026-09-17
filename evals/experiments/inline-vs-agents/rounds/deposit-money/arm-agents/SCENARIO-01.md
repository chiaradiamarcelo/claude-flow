# SCENARIO-01: Successful deposit over HTTP into a persisted account

## Scenario

Scenario: Successful deposit over HTTP into a persisted account
  Given a persisted account ACC-001 with balance 200
  When a client POSTs a deposit of 50 to /accounts/ACC-001/deposits
  Then the response status is 200 and the persisted balance is 250

## Structure & Contracts

Base package: `com.example.bank`. Greenfield slice — all artifacts below are new.

- **Domain aggregate:** `Account` (`domain/models/account/Account.kt`) — identity `AccountId` (e.g. `ACC-001`), holds `balance`; **equality required** (identity-based). Exposes a `deposit(amount)` behavior returning a new `Account` with `balance` increased by `amount`; rejects non-positive amounts by raising a domain exception (`InvalidDepositAmount`), enforcing Rule 2 at the aggregate.
- **Domain exceptions:** `AccountNotFound`, `InvalidDepositAmount` (`domain/models/account/`) — pure domain types, no framework dependency.
- **Write-side port:** `AccountRepository` (`domain/models/account/AccountRepository.kt`) — `save(Account): Account`, `findById(AccountId): Account?`. Contract test `AccountRepository.contract.kt` next to the port; `FakeAccountRepository` (`domain/models/account/fakes/`) and the JPA adapter (`infrastructure/`) each run it.
- **Persistence adapter:** `AccountRepositoryJpaAdapter` (`infrastructure/AccountRepositoryJpaAdapter.kt`) implementing `AccountRepository`, backed by a `AccountJpaEntity` (`infrastructure/AccountJpaEntity.kt`, explicit field mapping, H2 in-memory datasource already on the classpath) and a Spring Data `AccountSpringDataRepository` used only internally by the adapter. Mapping between `Account` and `AccountJpaEntity` isolated in the adapter (or a small mapper).
- **Use case (write side):** `DepositMoneyUseCase` (`application/DepositMoneyUseCase.kt`) — constructor-injects `AccountRepository`; behavioural entry point for this scenario. Loads the account by id, raises `AccountNotFound` when absent, applies `Account.deposit(amount)`, persists via `save`, and returns the updated `Account` for the controller to map.
- **API:** `DepositMoneyController` (`api/DepositMoneyController.kt`) — `POST /accounts/{accountId}/deposits` → `200` with `DepositResponse` (`api/dto/DepositResponse.kt`, containing `accountId` and `balance`) mapped from the returned `Account`; request body `DepositRequest` (`api/dto/DepositRequest.kt`, `amount`) validated for format only (numeric, present). Exception mapping: `AccountNotFound` → `404`; `InvalidDepositAmount` → `400`; unexpected failures → `500`. Controller stays thin: deserialize → call `DepositMoneyUseCase` → map response.
- **Test data seam:** since the scenario requires a *persisted* pre-existing account, the API test seeds the account through the real `AccountRepository`/adapter (or a seeding endpoint/fixture) rather than mocking persistence — this is a full vertical slice, not a controller slice test.

## Ordered Test List (FLFI · TPP · Contradiction)

### Unit — DepositMoneyUseCaseTest
| # | Test Name (FLFI) | TPP | Contradiction (what the code-so-far wrongly assumes) | Status |
|---|------------------|-----|------------------------------------------------------|--------|
| 1 | returns_the_balance_of_the_account_after_a_deposit | nil → constant (2) | No code returns a balance at all. | ✅ RED→GREEN — compile-red: `DepositMoneyUseCase`, `Account` and `AccountRepository` did not exist yet |
| 2 | increases_the_balance_by_the_amount_that_was_deposited | constant → scalar (4) | The resulting balance is the same whatever amount is deposited. | ✅ RED→GREEN — red in the same batch; kills the `return BigDecimal("2")` constant |
| 3 | adds_the_deposit_to_the_balance_the_account_already_had | constant → scalar (4) | The stored balance is ignored, so the result is just the deposited amount. | ✅ RED→GREEN — red in the same batch; kills `return amount` |
| 4 | saves_the_account_with_the_increased_balance | statement → statements (5) | The new balance is only returned, never stored, so a reload still shows the old one. | ✅ RED→GREEN — red in the same batch; forced the `accounts.save(...)` call |
| 5 | fails_when_the_deposited_amount_is_not_positive | unconditional → conditional (6) | Any amount is a deposit, so 0 is accepted and -10 shrinks the balance. | ✅ RED→GREEN — red in the same batch; forced the `InvalidDepositAmount` guard in `Account.deposit` |
| 6 | fails_when_no_account_exists_with_the_given_id | unconditional → conditional (6) | The account always exists, so a missing id crashes instead of reporting not-found. | ✅ RED→GREEN — red in the same batch; forced the `?: throw AccountNotFound` branch |

### Unit — AccountTest
| # | Test Name (FLFI) | TPP | Contradiction (what the code-so-far wrongly assumes) | Status |
|---|------------------|-----|------------------------------------------------------|--------|
| 7 | accounts_with_the_same_id_are_equal_even_when_their_balances_differ | n/a | Equality compares balances too, so the same account before and after a deposit looks different. | ✅ RED→GREEN — red on identity comparison before `equals`/`hashCode` were overridden |
| 8 | accounts_with_different_ids_are_not_equal | n/a | Equality ignores the id, so any two accounts compare equal. | ✅ EARLY-GREEN — passed under the default reference equality; kept because it is the only row that kills the `other is Account` mutant (equality that ignores the id) |

### Contract — AccountRepositoryContract
Run by `FakeAccountRepositoryTest` and by `AccountRepositoryJpaAdapterTest`.

| # | Test Name (FLFI) | TPP | Contradiction (what the code-so-far wrongly assumes) | Status |
|---|------------------|-----|------------------------------------------------------|--------|
| 9 | returns_a_saved_account_with_every_field_it_was_stored_with | n/a | The round trip preserves the account, so a dropped or mis-mapped balance is invisible. | ✅ RED→GREEN — compile-red: no `AccountJpaEntity`/adapter existed; green once id and balance were explicitly mapped. Already green for the fake |
| 10 | returns_nothing_when_no_account_was_saved_with_that_id | n/a | A lookup always yields an account, so unknown ids return a phantom or blow up. | ✅ RED→GREEN — compile-red in the same batch; green once `findById` mapped the empty Optional to null. Already green for the fake |
| 11 | returns_the_latest_balance_when_the_same_account_is_saved_again | n/a | Saving an existing id inserts a second account, so the old balance is still readable. | ✅ RED→GREEN — compile-red in the same batch; green once the assigned id made `save` a merge. Already green for the fake |

### Controller — DepositMoneyControllerIT
> Note to architect: these rows are a controller slice with a mocked `DepositMoneyUseCase`, not the full vertical seeded through the real adapter described in the structure. Persistence is proven by rows 9-11 running against `AccountRepositoryJpaAdapter`; seeding a real DB here would add no discriminating power at the controller level.

| # | Test Name (FLFI) | TPP | Contradiction (what the code-so-far wrongly assumes) | Status |
|---|------------------|-----|------------------------------------------------------|--------|
| 12 | returns_200_and_the_new_balance_when_the_deposit_is_accepted | n/a | No route exists at all. | ✅ RED→GREEN — compile-red: `DepositMoneyController` did not exist |
| 13 | returns_400_when_the_deposit_amount_is_missing | n/a | Any request body is a valid deposit, so a bodyless request reaches the use case. | ✅ RED→GREEN — compile-red in the same batch; green from the non-nullable `amount` on `DepositRequest` plus the `HttpMessageNotReadableException` handler |
| 14 | returns_400_when_the_amount_is_rejected_as_not_positive | n/a | `InvalidDepositAmount` is unmapped, so a domain rejection surfaces as 500. | ✅ RED→GREEN — compile-red in the same batch; forced the `InvalidDepositAmount → 400` mapping |
| 15 | returns_404_when_no_account_exists_with_the_given_id | n/a | `AccountNotFound` is unmapped, so a missing account surfaces as 500. | ✅ RED→GREEN — compile-red in the same batch; forced the `AccountNotFound → 404` mapping |
| 16 | returns_500_when_the_deposit_fails_unexpectedly | n/a | An unexpected failure escapes the handler instead of becoming a 500 response. | ✅ RED→GREEN — compile-red in the same batch; forced the catch-all handler that turns an escaping exception into a 500 body |

### Deleted
- `returns_400_when_the_deposit_amount_is_not_a_number` — same deserialization path and outcome as row 13; no discriminating power.
- `returns_the_account_id_in_the_response` — no discriminating power over row 12 under a mocked use case.
- `fails_when_the_deposited_amount_is_negative` — row 5 already fails under this contradiction (non-positive covers it).
- `returns_the_saved_account_from_save` — asserting `save`'s return adds nothing over row 9's read-back.
