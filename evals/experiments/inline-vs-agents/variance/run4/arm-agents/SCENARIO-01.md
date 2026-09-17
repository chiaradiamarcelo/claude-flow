# SCENARIO-01: Successful withdrawal over HTTP from a persisted account

## Scenario

Scenario: Successful withdrawal over HTTP from a persisted account
  Given a persisted account ACC-001 with balance 200
  When a client POSTs a withdrawal of 50 to /accounts/ACC-001/withdrawals
  Then the response status is 200 and the persisted balance is 150

## Structure & Contracts

- **Domain (write side):** `Account` aggregate root (`com.example.bank.domain.models.account.Account`) — identity is `AccountId` (value class wrapping a `String`, e.g. `ACC-001`); **equality required**. Holds `balance` (`BigDecimal`). Exposes a `withdraw(amount: BigDecimal): Account` returning a new `Account` instance with reduced balance, enforcing Rule 2 (amount strictly positive) and Rule 3 (no overdraft) as domain invariants raised as domain exceptions: `NonPositiveWithdrawalAmount`, `InsufficientBalance`.
- **Port:** `AccountRepository` (`domain/models/account/AccountRepository.kt`) — `save(account: Account): Account`, `findById(id: AccountId): Account?`. Gets `AccountRepository.contract.kt` (same folder) — an abstract contract test; `FakeAccountRepository` (`domain/models/account/fakes/`) and `AccountJpaRepositoryAdapter` (`infrastructure/`) each run it via their own spec.
- **Persistence:** `AccountJpaEntity` (`infrastructure/persistence/`) — JPA entity mapping `id` (String, PK) and `balance` (BigDecimal); `AccountSpringDataJpaRepository : JpaRepository<AccountJpaEntity, String>` used internally by the adapter, never exposed outside `infrastructure/`. Adapter converts `Account` ↔ `AccountJpaEntity` via a mapper method. In-memory H2 (already configured) backs the adapter for this slice; no explicit migration needed (Hibernate `ddl-auto` or a schema.sql may be used — infra detail, not part of the contract).
- **UseCase (write side, orchestrates the aggregate):** `WithdrawMoneyUseCase` (`application/`) — constructor takes `AccountRepository`; method loads the account by id, calls `account.withdraw(amount)`, persists via `save`, and returns the updated `Account` (the shape the controller maps to the response). Raises a domain exception (`AccountNotFound`) when `findById` returns null — this is the behavioural entry point this scenario is verified through.
- **API:** `WithdrawMoneyController` (`api/`) — `POST /accounts/{id}/withdrawals`, request body `WithdrawMoneyRequest(amount: BigDecimal)` (`api/dto/`), response `WithdrawMoneyResponse(accountId: String, balance: BigDecimal)` (`api/dto/`) mapped from the returned `Account`, never the domain entity itself. Maps: success → `200 OK`; `AccountNotFound` → `404`; `NonPositiveWithdrawalAmount` / `InsufficientBalance` / malformed body → `400`; unexpected failure → `500`.

## Ordered Test List (FLFI · TPP · Contradiction)

### Unit — WithdrawMoneyUseCaseTest
| # | Test Name (FLFI) | TPP | Contradiction (what the code-so-far wrongly assumes) | Status |
|---|------------------|-----|------------------------------------------------------|--------|
| 1 | returns_the_balance_left_after_the_withdrawal | nil → constant (2) | No code returns a balance at all. | ✅ RED→GREEN — red as a compile failure (`Account`, `WithdrawMoneyUseCase` unresolved), green once `withdraw` returned the reduced balance |
| 2 | subtracts_the_amount_that_was_withdrawn_rather_than_a_fixed_one | constant → scalar (4) | The remaining balance is the same whatever amount was withdrawn. | ✅ RED→GREEN — same batch-red compile failure; withdrawing 30 from 200 forced the amount to become an argument |
| 3 | subtracts_from_the_balance_the_account_already_had | constant → scalar (4) | The stored balance is ignored; the result depends only on the amount. | ✅ RED→GREEN — same batch-red; 500 − 50 forced the stored balance to be read |
| 4 | saves_the_account_with_the_reduced_balance | statement → statements (5) | The new balance is returned but never written back, so a re-read still shows 200. | ✅ RED→GREEN — same batch-red; forced the `save` call after `withdraw` |
| 5 | fails_when_the_withdrawn_amount_is_not_positive | unconditional → conditional (6) | Any amount is a withdrawal, so 0 and -10 are accepted and -10 grows the balance. | ✅ RED→GREEN — same batch-red; seeded with 0 so the `< ZERO` mutant is also killed |
| 6 | fails_when_the_withdrawn_amount_exceeds_the_available_balance | unconditional → conditional (6) | Any amount fits, so withdrawing 250 from 200 leaves -50. | ✅ RED→GREEN — same batch-red; forced the overdraft guard |
| 7 | allows_withdrawing_the_whole_available_balance | n/a | The overdraft guard rejects amount == balance (`>=` instead of `>`). | ✅ RED→GREEN — same batch-red; pins `>` against the `>=` mutant |
| 8 | fails_when_no_account_exists_with_the_given_id | unconditional → conditional (6) | Every id resolves to an account, so a missing one blows up or withdraws from nothing. | ✅ RED→GREEN — same batch-red; forced the `?: throw AccountNotFound` branch |

### Unit — AccountTest
| # | Test Name (FLFI) | TPP | Contradiction (what the code-so-far wrongly assumes) | Status |
|---|------------------|-----|------------------------------------------------------|--------|
| 9 | is_equal_to_another_account_with_the_same_id | n/a | Identity is reference-based, so two loads of ACC-001 are different accounts. | ✅ RED→GREEN — red with `expected: Account@… to be equal to Account@…` before id-based `equals`/`hashCode` existed |
| 10 | is_not_equal_to_an_account_with_a_different_id | n/a | Equality ignores the id, so ACC-001 and ACC-002 compare equal. | ✅ EARLY-GREEN — passed under reference equality; kept because it kills the `other is Account` mutant (equality that ignores the id) |

### Contract — AccountRepositoryContractTest
| # | Test Name (FLFI) | TPP | Contradiction (what the code-so-far wrongly assumes) | Status |
|---|------------------|-----|------------------------------------------------------|--------|
| 11 | returns_a_saved_account_with_every_field_it_was_stored_with | n/a | The round trip preserves the account, so a dropped or mis-mapped balance is invisible. | ✅ RED→GREEN — red as a compile failure (`AccountJpaRepositoryAdapter` unresolved) for both implementations |
| 12 | returns_nothing_when_no_account_was_saved_with_that_id | n/a | A lookup always yields an account, so a missing id fabricates or throws. | ✅ RED→GREEN — same batch-red; run by `FakeAccountRepositoryTest` and `AccountJpaRepositoryAdapterIT` |
| 13 | returns_the_latest_balance_when_the_same_account_is_saved_again | n/a | Saving inserts a second row, so a re-read still returns the pre-withdrawal balance. | ✅ RED→GREEN — same batch-red; proves `save` merges rather than inserts a second row |

### Controller — WithdrawMoneyControllerIT
| # | Test Name (FLFI) | TPP | Contradiction (what the code-so-far wrongly assumes) | Status |
|---|------------------|-----|------------------------------------------------------|--------|
| 14 | returns_200_and_the_remaining_balance_when_the_withdrawal_is_accepted | n/a | No route exists at all. | ✅ RED→GREEN — red as a compile failure (`WithdrawMoneyController` unresolved) for the whole batch |
| 15 | passes_the_account_id_from_the_path_and_the_amount_from_the_body_to_the_use_case | n/a | The request values never reach the use case; any path/body withdraws the same thing. | ✅ RED→GREEN — same batch-red; uses ACC-002/30 so a hard-coded ACC-001/50 mutant fails verification |
| 16 | returns_404_when_no_account_exists_with_the_given_id | n/a | AccountNotFound is unmapped, so a missing account surfaces as 500. | ✅ RED→GREEN — same batch-red; forced the `AccountNotFound` handler |
| 17 | returns_400_when_the_withdrawn_amount_is_not_positive | n/a | NonPositiveWithdrawalAmount is unmapped, so a rejected amount surfaces as 500. | ✅ RED→GREEN — same batch-red; forced the `NonPositiveWithdrawalAmount` handler |
| 18 | returns_400_when_the_withdrawn_amount_exceeds_the_available_balance | n/a | InsufficientBalance is unmapped, so an overdraft attempt surfaces as 500. | ✅ RED→GREEN — same batch-red; forced the `InsufficientBalance` handler |
| 19 | returns_400_when_the_amount_is_missing_from_the_request_body | n/a | Any request body is a valid withdrawal, so a bodiless call reaches the use case. | ✅ RED→GREEN — same batch-red; forced the `HttpMessageNotReadableException` handler, which the catch-all would otherwise have turned into a 500 |
| 20 | returns_500_when_the_withdrawal_fails_unexpectedly | n/a | Every failure is a client error, so an infrastructure fault is reported as 4xx. | ✅ RED→GREEN — same batch-red; forced the catch-all handler |

> Note to architect: no seam is declared that exercises HTTP and JPA together, so the scenario's "persisted balance is 150" is only proven by composition (rows 4 + 11 + 13 + 14). If a full-stack acceptance test is wanted, a `WithdrawMoneyAcceptanceIT` (`@SpringBootTest` + H2) needs to be added to the structure.

### Acceptance — WithdrawMoneyAcceptanceIT

| # | Test Name (FLFI) | TPP | Contradiction (what the code-so-far wrongly assumes) | Status |
|---|------------------|-----|------------------------------------------------------|--------|
| 21 | persists_the_reduced_balance_when_a_withdrawal_is_posted | n/a | HTTP and JPA are wired together, so a missing bean or an unwired adapter is invisible to the slice tests. | ✅ UNPLANNED — honours the note above; supports the scenario's "persisted balance is 150" end to end. Red with `NoSuchBeanDefinitionException` for `WithdrawMoneyUseCase` before `UseCaseConfiguration` existed |

### Deleted
- `returns_the_account_id_unchanged_after_the_withdrawal` — no discriminating power over row 1's returned account.
- `returns_400_when_the_request_body_is_not_valid_json` — same parse-failure path as row 19 under the controller slice.
- `returns_400_when_the_amount_is_not_a_number` — same parse-failure path as row 19 under the controller slice.
- `returns_the_remaining_balance_in_the_response_payload` — no discriminating power over row 14.
