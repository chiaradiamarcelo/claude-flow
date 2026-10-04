# SCENARIO-01: Successful withdrawal over HTTP from a persisted account

```gherkin
Scenario: Successful withdrawal over HTTP from a persisted account
  Given a persisted account ACC-001 with balance 200
  When a client POSTs a withdrawal of 50 to /accounts/ACC-001/withdrawals
  Then the response status is 200 and the persisted balance is 150
```

## Structure & Contracts

- **Domain:** `Account` aggregate root (`domain/models/account/`) — `accountId: String`, `balance: BigDecimal`; `withdraw(amount): Account` returns a new instance and enforces Rule 2 (strictly positive) and Rule 3 (no overdraft) by throwing `InvalidWithdrawalAmount` / `InsufficientFunds`; identity is `accountId`, **equality required**.
- **Domain exceptions:** `AccountNotFound`, `InsufficientFunds`, `InvalidWithdrawalAmount` (`domain/models/account/`) — pure Kotlin, no framework types.
- **Write side:** `AccountRepository` port (`domain/models/account/`) — `save(account): Account`, `findById(accountId): Account?`. Write side because the withdrawal mutates the aggregate through its consistency boundary.
- **Contract:** abstract `AccountRepositoryContractTest` (`domain/models/account/` in the test source set, file `AccountRepository.contract.kt`); `FakeAccountRepositoryTest` and `AccountJpaAdapterIT` each extend it.
- **Fake:** `FakeAccountRepository` (`domain/models/account/fakes/`, main source set so both tests and future modules reuse it).
- **Use case:** `WithdrawMoneyUseCase` (`application/`) — `withdraw(accountId, amount): Account`; loads, applies `Account.withdraw`, saves, returns the saved aggregate. Throws `AccountNotFound` when the id is unknown; lets the aggregate's own invariant exceptions propagate.
- **Infrastructure:** `AccountJpaAdapter` (`infrastructure/`) implementing the port over `AccountJpaEntity` + a Spring Data `AccountJpaRepository`; explicit field mapping both ways, no domain leakage into the entity.
- **API:** `WithdrawMoneyController` (`api/`) — `POST /accounts/{accountId}/withdrawals`, body `WithdrawMoneyRequest(amount: BigDecimal)`, success `200` with `WithdrawalResponse(accountId, balance)`. Mapping: `AccountNotFound` → `404`; `InvalidWithdrawalAmount`, `InsufficientFunds`, malformed/unparseable/missing body → `400`. Error body is the shared `{ "error": { "code", "message" } }` shape (`api/dto/ErrorResponse.kt`), produced by `@ExceptionHandler` methods on the controller.
- **End-to-end:** `WithdrawMoneyEndToEndIT` (`api/`) — `@SpringBootTest` + `MockMvc` against the real JPA adapter and H2; the only test that proves the Gherkin's "persisted balance" clause.

## Ordered Test List (FLFI · TPP · Contradiction)

### Unit — AccountTest
| # | Test Name (FLFI) | TPP | Contradiction (what the code-so-far wrongly assumes) | Status |
|---|------------------|-----|------------------------------------------------------|--------|
| 1 | accounts_with_the_same_id_are_equal | n/a | Identity is reference-based, so two loads of one account are different accounts. | ✅ RED→GREEN — red with `Unresolved reference 'Account'` |
| 2 | accounts_with_different_ids_are_not_equal | n/a | Equality could be satisfied by returning true for any pair. | ✅ RED→GREEN — red with `Unresolved reference 'Account'` |

### Unit — WithdrawMoneyUseCaseTest
| # | Test Name (FLFI) | TPP | Contradiction (what the code-so-far wrongly assumes) | Status |
|---|------------------|-----|------------------------------------------------------|--------|
| 3 | returns_the_balance_reduced_by_the_withdrawn_amount | nil → constant (2) | There is no withdrawal operation and nothing reports a balance. | ✅ RED→GREEN — red with `Unresolved reference 'withdraw'` |
| 4 | subtracts_the_withdrawn_amount_from_the_stored_balance_rather_than_fixed_values | constant → scalar (4) | The remaining balance depends on neither the stored balance nor the amount. | ✅ RED→GREEN — red with `Unresolved reference 'withdraw'` |
| 5 | persists_the_account_with_the_reduced_balance | statement → statements (5) | Computing the new balance is enough; nothing needs to be written back. | ✅ RED→GREEN — red with `Unresolved reference 'findById'` |
| 6 | fails_when_the_amount_exceeds_the_balance | unconditional → conditional (6) | Every withdrawal is allowed, so an overdraft would be persisted. | ✅ RED→GREEN — red with `Unresolved reference 'InsufficientFunds'` |
| 7 | leaves_a_zero_balance_when_the_amount_equals_the_balance | n/a | The no-overdraft guard may be written as `>=`, rejecting a full withdrawal. | ✅ RED→GREEN — red with `Unresolved reference 'withdraw'` |
| 8 | fails_when_the_amount_is_zero | unconditional → conditional (6) | Any non-overdrawing amount is a valid withdrawal, including nothing. | ✅ RED→GREEN — red with `Unresolved reference 'InvalidWithdrawalAmount'` |
| 9 | fails_when_the_amount_is_negative | unconditional → conditional (6) | A negative amount merely adds money instead of being rejected. | ✅ RED→GREEN — red with `Unresolved reference 'InvalidWithdrawalAmount'` |
| 10 | fails_when_no_account_has_the_requested_id | unconditional → conditional (6) | The repository always returns an account for any id. | ✅ RED→GREEN — red with `Unresolved reference 'AccountNotFound'` |

### Contract — AccountRepositoryContractTest

Run by `FakeAccountRepositoryTest` and by `AccountJpaAdapterIT`.

| # | Test Name (FLFI) | TPP | Contradiction (what the code-so-far wrongly assumes) | Status |
|---|------------------|-----|------------------------------------------------------|--------|
| 11 | returns_every_stored_field_of_an_account_that_was_saved | n/a | A round trip preserves the account, so dropping or mis-mapping the balance is invisible. | ✅ RED→GREEN — red with `Unresolved reference 'AccountJpaAdapter'` |
| 12 | returns_nothing_when_no_account_has_the_requested_id | n/a | A lookup always yields an account, so a missing id cannot be detected. | ✅ RED→GREEN — red with `Unresolved reference 'AccountJpaAdapter'` |
| 13 | returns_the_latest_balance_when_an_account_is_saved_again | n/a | Saving an existing id inserts a second row instead of replacing it. | ✅ RED→GREEN — red with `Unresolved reference 'AccountJpaAdapter'` |

### Controller — WithdrawMoneyControllerIT
| # | Test Name (FLFI) | TPP | Contradiction (what the code-so-far wrongly assumes) | Status |
|---|------------------|-----|------------------------------------------------------|--------|
| 14 | returns_200_and_the_remaining_balance_when_the_withdrawal_is_accepted | n/a | No route exists at all. | ✅ RED→GREEN — red with `Unresolved reference 'WithdrawMoneyController'` |
| 15 | withdraws_the_requested_amount_from_the_account_in_the_path | n/a | The path id and the body amount need not reach the use case. | ✅ RED→GREEN — red with `Unresolved reference 'WithdrawMoneyController'` |
| 16 | returns_400_when_the_request_body_is_malformed | n/a | Any request body can be deserialized into a withdrawal. | ✅ RED→GREEN — red with `Unresolved reference 'WithdrawMoneyController'` |
| 17 | returns_400_when_the_amount_is_missing_from_the_request_body | n/a | The amount is optional and a withdrawal can proceed without it. | ✅ RED→GREEN — red with `Unresolved reference 'WithdrawMoneyController'` |
| 18 | returns_400_when_the_amount_is_not_a_number | n/a | Any JSON value in the amount field parses as an amount. | ✅ RED→GREEN — red with `Unresolved reference 'WithdrawMoneyController'` |
| 19 | returns_400_when_the_amount_is_not_a_positive_number | n/a | A domain invariant violation escapes as an unhandled 500. | ✅ RED→GREEN — red with `Unresolved reference 'WithdrawMoneyController'` |
| 20 | returns_400_when_the_amount_exceeds_the_balance | n/a | An overdraft rejection escapes as an unhandled 500. | ✅ RED→GREEN — red with `Unresolved reference 'WithdrawMoneyController'` |
| 21 | returns_404_when_no_account_has_the_id_in_the_path | n/a | An unknown account is indistinguishable from an accepted withdrawal. | ✅ RED→GREEN — red with `Unresolved reference 'WithdrawMoneyController'` |

### End-to-end — WithdrawMoneyEndToEndIT
| # | Test Name (FLFI) | TPP | Contradiction (what the code-so-far wrongly assumes) | Status |
|---|------------------|-----|------------------------------------------------------|--------|
| 22 | reduces_the_persisted_balance_when_a_withdrawal_is_posted | n/a | The layers are each correct in isolation, so the wiring and the persisted row must be right. | ✅ RED→GREEN — red with `NoSuchBeanDefinitionException` for `WithdrawMoneyUseCase` |

### Deleted
- `subtracts_from_the_balance_the_account_was_stored_with` — row 4 varies both the stored balance and the amount, so it already fails under this row's contradiction.
- `returns_the_account_id_in_the_response` — row 14 already asserts the whole response body; no discriminating power.
- `fails_when_the_repository_throws` — no production branch exists for it; the exception propagates untouched, so the row rules out no mutant.
- `returns_500_when_persistence_fails` — no defined 500 mapping in this slice; Spring's default already covers it.
