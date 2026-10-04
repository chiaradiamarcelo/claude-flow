# SCENARIO-01: Successful withdrawal over HTTP from a persisted account

```gherkin
Scenario: Successful withdrawal over HTTP from a persisted account
  Given a persisted account ACC-001 with balance 200
  When a client POSTs a withdrawal of 50 to /accounts/ACC-001/withdrawals
  Then the response status is 200 and the persisted balance is 150
```

## Structure & Contracts

- **Domain:** `Account` aggregate root (`domain/models/account/`) — `id: String`, `balance: BigDecimal`; **equality required** (identity = `id`). `withdraw(amount): Account` returns a new instance and enforces Rule 2 (strictly positive) and Rule 3 (not exceeding balance).
- **Domain failures** (`domain/models/account/`): `InvalidWithdrawalAmountException`, `InsufficientFundsException` (both raised by the aggregate), `AccountNotFoundException` (raised by the use case).
- **Write side:** `AccountRepository` port (`domain/models/account/`) — `save(Account): Account`, `findById(String): Account?`. Write side, so `*Repository` and a use case are both required; there is no divergent read shape, so no `*Query` (cqrs Rule 5).
- **Contract test:** abstract `AccountRepositoryContractTest` in the test source set, package `domain.models.account`. `FakeAccountRepositoryTest` and `AccountJpaAdapterIT` each extend it.
- **Fake:** `FakeAccountRepository` (test source set, `domain/models/account/fakes/`) — in-memory map, same port. Kept out of `src/main` so test doubles are not shipped.
- **Use case:** `WithdrawMoneyUseCase` (`application/`) — `withdraw(accountId: String, amount: BigDecimal): Account`; loads the aggregate, delegates the rules to it, saves, returns the updated aggregate. Behavioural entry point for the domain rows.
- **Persistence:** `AccountJpaEntity` + Spring Data `AccountJpaRepository` (both internal to infrastructure) + `AccountJpaAdapter : AccountRepository` (`infrastructure/`). Explicit field mapping; H2 via the existing `application.properties`.
- **API:** `WithdrawMoneyController` (`api/`) — `POST /accounts/{accountId}/withdrawals`, body `{"amount": <number>}`, success `200` with `{"accountId": ..., "balance": ...}` (not a create of an addressable resource, so `200` rather than `201`). DTOs `WithdrawalRequest` / `WithdrawalResponse` in `api/dto/`.
- **Status mapping** via `ApiExceptionHandler` (`api/`), error body `{"error": {"code": ..., "message": ...}}`: `InvalidWithdrawalAmountException` → `400`, `InsufficientFundsException` → `400`, `AccountNotFoundException` → `404`, malformed/unparseable/missing `amount` → `400`, any other exception → `500`.
- **Vertical proof:** `WithdrawMoneyIT` (`@SpringBootTest` + MockMvc, real H2) — one end-to-end row proving controller → use case → JPA adapter are wired, which no single-layer test can show.

## Ordered Test List (FLFI · TPP · Contradiction)

### Unit — WithdrawMoneyUseCaseTest
| # | Test Name (FLFI) | TPP | Contradiction (what the code-so-far wrongly assumes) | Status |
|---|------------------|-----|------------------------------------------------------|--------|
| 1 | reduces_the_persisted_balance_by_the_withdrawn_amount | nil → constant (2) | Nothing ever writes a new balance; the stored account stays untouched. | ✅ RED→GREEN — red with expected 150 but the stored balance was still 200 |
| 2 | subtracts_the_amount_that_was_requested_rather_than_a_fixed_one | constant → scalar (4) | The new balance is the same whatever amount is withdrawn. | ✅ RED→GREEN — red with expected 170 but the stored balance was still 200 |
| 3 | subtracts_from_the_balance_the_account_was_stored_with | constant → scalar (4) | The starting balance is always the one used by the earlier rows. | ✅ RED→GREEN — red with expected 50 but the stored balance was still 80 |
| 4 | returns_the_account_carrying_the_balance_left_after_the_withdrawal | statement → statements (5) | The caller has no way to learn the new balance. | ✅ RED→GREEN — red with expected 150 but the returned account still carried 200 |
| 5 | fails_when_the_amount_exceeds_the_balance | unconditional → conditional (6) | Every requested amount is affordable. | ✅ RED→GREEN — red because nothing was thrown for an amount above the balance |
| 6 | leaves_the_persisted_balance_untouched_when_the_amount_exceeds_it | n/a | Rejecting is enough; the balance may already have been written before the check. | ✅ EARLY-GREEN — the skeleton never wrote at all; kept because moving `accounts.save` above the rule check in the use case turns it red |
| 7 | allows_a_withdrawal_of_the_whole_balance | n/a | Equalling the balance counts as exceeding it. | ✅ RED→GREEN — red with expected 0 but the stored balance was still 200 |
| 8 | fails_when_the_amount_is_zero | unconditional → conditional (6) | Any amount that fits within the balance is a valid withdrawal. | ✅ RED→GREEN — red because nothing was thrown for an amount of zero |
| 9 | fails_when_the_amount_is_negative | n/a | Only zero is an invalid amount; a negative amount fits the balance so it passes. | ✅ RED→GREEN — red because nothing was thrown for a negative amount |
| 10 | fails_when_no_account_is_stored_for_the_id | unconditional → conditional (6) | Every id handed to the use case resolves to a stored account. | ✅ RED→GREEN — red with a NullPointerException instead of AccountNotFoundException |

### Unit — AccountTest
| # | Test Name (FLFI) | TPP | Contradiction (what the code-so-far wrongly assumes) | Status |
|---|------------------|-----|------------------------------------------------------|--------|
| 11 | two_accounts_with_the_same_id_are_equal | n/a | Identity is not what makes two accounts the same, so every assertion comparing accounts is unreliable. | ✅ RED→GREEN — red because the skeleton had no equality, so two instances differed |
| 12 | two_accounts_with_different_ids_are_not_equal | n/a | Any two accounts compare equal, so equality proves nothing. | ✅ EARLY-GREEN — reference equality already separated them; kept because equality on `balance` instead of `id` turns it red |

### Contract — AccountRepositoryContractTest
| # | Test Name (FLFI) | TPP | Contradiction (what the code-so-far wrongly assumes) | Status |
|---|------------------|-----|------------------------------------------------------|--------|
| 13 | returns_an_account_with_every_field_it_was_saved_with | n/a | The round trip preserves the account, so dropping or mis-mapping a field is invisible. | ✅ RED→GREEN — red on the missing AccountJpaAdapter, then green for the fake and for H2 |
| 14 | returns_nothing_when_no_account_was_saved_for_the_id | n/a | A lookup always has something to return. | ✅ RED→GREEN — red on the missing AccountJpaAdapter, then green for the fake and for H2 |
| 15 | returns_the_latest_balance_when_the_same_account_is_saved_again | n/a | The first stored version of an account is the one a lookup sees. | ✅ RED→GREEN — red on the missing AccountJpaAdapter, then green for the fake and for H2 |

### Controller — WithdrawMoneyControllerIT
| # | Test Name (FLFI) | TPP | Contradiction (what the code-so-far wrongly assumes) | Status |
|---|------------------|-----|------------------------------------------------------|--------|
| 16 | returns_200_and_the_balance_left_when_the_withdrawal_is_accepted | n/a | No route exists at all. | ✅ RED→GREEN — red on the missing WithdrawMoneyController |
| 17 | withdraws_the_posted_amount_from_the_account_named_in_the_path | n/a | The route can answer without passing the path id and the body amount to the use case. | ✅ RED→GREEN — red on the missing WithdrawMoneyController |
| 18 | returns_400_when_the_body_is_malformed_json | n/a | Anything that reaches the route is a parseable request. | ✅ RED→GREEN — red on the missing WithdrawMoneyController |
| 19 | returns_400_when_the_amount_is_not_a_number | n/a | A well-formed body always carries a numeric amount. | ✅ RED→GREEN — red on the missing WithdrawMoneyController |
| 20 | returns_400_when_the_amount_is_missing | n/a | A parseable body always contains the amount field. | ✅ RED→GREEN — red on the missing WithdrawMoneyController |
| 21 | returns_400_when_the_amount_is_not_positive | n/a | The domain never rejects an amount, so nothing maps that rejection to a status. | ✅ RED→GREEN — red on the missing WithdrawMoneyController |
| 22 | returns_400_when_the_amount_exceeds_the_balance | n/a | An unaffordable withdrawal is indistinguishable from an accepted one at the boundary. | ✅ RED→GREEN — red on the missing WithdrawMoneyController |
| 23 | returns_404_when_the_account_does_not_exist | n/a | Every account named in a path exists, so a missing one falls through as a server error. | ✅ RED→GREEN — red on the missing WithdrawMoneyController |
| 24 | returns_500_when_the_withdrawal_fails_unexpectedly | n/a | Only domain failures can come out of the use case. | ✅ RED→GREEN — red on the missing WithdrawMoneyController |

### End-to-end — WithdrawMoneyIT
| # | Test Name (FLFI) | TPP | Contradiction (what the code-so-far wrongly assumes) | Status |
|---|------------------|-----|------------------------------------------------------|--------|
| 25 | reduces_the_balance_persisted_in_the_database_when_a_withdrawal_is_posted | n/a | Each layer is correct in isolation, so the application context wires and maps them correctly end to end. | ✅ EARLY-GREEN — every layer was already in place when it first ran; kept because renaming the route to /withdrawal turns it red, which no single-layer test notices |

### Deleted
- `saves_the_account_after_a_successful_withdrawal` — row 1 already reads the balance back through the port, so a missing `save` fails it; no discriminating power.
- `returns_the_error_body_shape_on_a_rejected_withdrawal` — rows 21–23 assert the body alongside the status; a separate shape row rules out no further mutant.
- `fails_when_the_account_id_is_blank` — no business rule in the specification forbids it, and the not-found path (row 10) already covers an id with no account.
