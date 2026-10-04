# SCENARIO-01: Successful withdrawal over HTTP from a persisted account

## Scenario

Scenario: Successful withdrawal over HTTP from a persisted account
  Given a persisted account ACC-001 with balance 200
  When a client POSTs a withdrawal of 50 to /accounts/ACC-001/withdrawals
  Then the response status is 200 and the persisted balance is 150

## Structure & Contracts

- **Domain aggregate:** `Account` (`domain/models/account/Account.kt`) — identified by `accountId: AccountId` (String value object, e.g. `ACC-001`); holds `balance`. Identity is the account id — **equality required**. Enforces invariants: amount strictly positive, withdrawal never exceeds balance (`InsufficientBalanceException` / `InvalidAmountException` domain exceptions). Mutation returns a new `Account` instance (immutable withdraw method) rather than mutating in place.
- **Write-side port:** `AccountRepository` (`domain/models/account/AccountRepository.kt`) — `save(Account)`, `findById(AccountId): Account?`. Gets `AccountRepository.contract.kt` next to it (abstract contract test); `FakeAccountRepository` (`domain/models/account/fakes/`) and the real JPA adapter (`infrastructure/AccountJpaAdapter.kt`) each extend the contract.
- **Persistence:** `AccountJpaEntity` (`infrastructure/`) — JPA entity mapped to an `accounts` table (id, balance columns), Spring Data `AccountJpaRepository : JpaRepository<AccountJpaEntity, String>` used internally by `AccountJpaAdapter`. Adapter maps `Account` ↔ `AccountJpaEntity` in dedicated mapper methods; runs against H2 in-memory for this slice. `AccountJpaAdapterIntegrationSpec` (or `.integration.spec.kt`) runs the shared contract via `@DataJpaTest`/full Spring context.
- **Use case (write side):** `WithdrawMoneyUseCase` (`application/WithdrawMoneyUseCase.kt`) — constructor-injects `AccountRepository`; orchestrates load → domain withdraw → save. This is the behavioural entry point this scenario is verified through; returns the updated `Account` (post-withdrawal balance) to the caller.
- **API:** `WithdrawMoneyController` (`api/`) — `POST /accounts/{accountId}/withdrawals`, per-action controller (single responsibility). Request body `WithdrawMoneyRequest` (`api/dto/`, format-only validation: amount present and numeric). Response `AccountResponse` (`api/dto/`, `accountId`, `balance`) — no domain entity leaked. Success → `200 OK` with the response body (update returning content, not a create). Exception mapping: `AccountNotFoundException` → `404`; `InvalidAmountException` / `InsufficientBalanceException` → `400`; unexpected failures → `500`. This scenario only exercises the success path; the 404/400 mappings are declared here for controller shape but their rows belong to later scenarios.

## Ordered Test List (FLFI · TPP · Contradiction)

### Unit — WithdrawMoneyUseCaseTest
| # | Test Name (FLFI) | TPP | Contradiction (what the code-so-far wrongly assumes) | Status |
|---|------------------|-----|------------------------------------------------------|--------|
| 1 | returns_the_remaining_balance_after_the_withdrawal | nil → constant (2) | No code returns a balance at all. | ✅ RED→GREEN — red with `expected: 150 but was: 200` while `withdraw` returned the account untouched |
| 2 | subtracts_the_amount_that_was_withdrawn_rather_than_a_fixed_one | constant → scalar (4) | The remaining balance is the same whatever amount was withdrawn. | ✅ RED→GREEN — red with `expected: 170 but was: 200` |
| 3 | subtracts_the_withdrawal_from_the_balance_the_stored_account_had | constant → scalar (4) | The starting balance is hardcoded, so a stored account with another balance is ignored. | ✅ RED→GREEN — red with `expected: 450 but was: 500` |
| 4 | saves_the_account_so_the_stored_balance_is_the_reduced_one | statement → statements (5) | The reduced balance is only returned, never saved, so reading the account back shows the old one. | ✅ RED→GREEN — red with `expected: 150 but was: 200` read back from the repository before `save` was called |

> Note to architect: rules 2 (strictly positive amount) and 3 (no overdraft), the `AccountNotFoundException` path, and the 400/404/500 mappings are declared in Structure & Contracts but no Gherkin scenario covers them — no rows designed here. They need their own scenarios in the specification.

### Unit — AccountTest
| # | Test Name (FLFI) | TPP | Contradiction (what the code-so-far wrongly assumes) | Status |
|---|------------------|-----|------------------------------------------------------|--------|
| 5 | accounts_with_the_same_account_id_are_equal | n/a | Two loads of ACC-001 are different objects, so every `isEqualTo(account)` assertion elsewhere is vacuous. | ✅ RED→GREEN — red on identity equality before `equals`/`hashCode` were overridden |
| 6 | accounts_with_different_account_ids_are_not_equal | n/a | Equality ignores the id, so ACC-001 and ACC-002 compare equal. | ✅ EARLY-GREEN — passed under inherited identity equality; kept because it is the only test that kills the mutant `equals(other) = other is Account` (id ignored), which row 5 alone leaves alive |

### Contract — AccountRepositoryContractTest
| # | Test Name (FLFI) | TPP | Contradiction (what the code-so-far wrongly assumes) | Status |
|---|------------------|-----|------------------------------------------------------|--------|
Executed twice: `FakeAccountRepositoryTest` and `AccountJpaAdapterIT`.

| 7 | returns_a_saved_account_with_the_id_and_balance_it_was_stored_with | n/a | The round trip preserves the account, so a dropped or wrongly mapped balance column is invisible. | ✅ RED→GREEN — compile-red until `AccountJpaAdapter` existed; mutant `toEntity` writing `BigDecimal.ZERO` was applied and killed it |
| 8 | returns_nothing_for_an_account_id_that_was_never_saved | n/a | A lookup always yields an account, so a missing id returns a blank one instead of nothing. | ✅ RED→GREEN — compile-red until `AccountJpaAdapter` existed |

### Controller — WithdrawMoneyControllerIT
| # | Test Name (FLFI) | TPP | Contradiction (what the code-so-far wrongly assumes) | Status |
|---|------------------|-----|------------------------------------------------------|--------|
| 9 | returns_200_and_the_remaining_balance_when_the_withdrawal_succeeds | n/a | No route exists at all. | ✅ RED→GREEN — compile-red: `Unresolved reference 'WithdrawMoneyController'` |
| 10 | returns_400_when_the_amount_is_missing_from_the_request | n/a | Any body is a valid withdrawal, so a bodyless request reaches the use case. | ✅ RED→GREEN — compile-red with row 9; green via deserialization of the non-null `amount`, no hand-rolled validation |
| 11 | returns_400_when_the_amount_is_not_a_number | n/a | The body always deserializes, so an unparseable amount surfaces as a server error. | ✅ RED→GREEN — compile-red with row 9 |

### Application wiring — BankApplicationTest

| # | Test Name (FLFI) | TPP | Contradiction (what the code-so-far wrongly assumes) | Status |
|---|------------------|-----|------------------------------------------------------|--------|
| 12 | context_loads | n/a | Every collaborator the new controller needs is already a bean. | ✅ UNPLANNED — pre-existing baseline test; it reddened with `No qualifying bean of type 'WithdrawMoneyUseCase'` and forced `infrastructure/config/UseCaseConfiguration` (the use case stays framework-free) |

### Deleted
- `passes_the_account_id_from_the_path_to_the_use_case` — no discriminating power over row 9, which already fails if the path id is not forwarded.
- `returns_the_remaining_balance_in_the_response_body` — same assertion surface as row 9 under a mocked use case.
- `returns_an_account_with_the_requested_account_id` (unit) — rows 1–4 already redden if the wrong account is returned.
- `returns_the_account_unchanged_when_withdrawing_zero` — a domain rule with no scenario; belongs with rule 2, not here.
