# SCENARIO-01: Successful withdrawal over HTTP from a persisted account

```gherkin
Scenario: Successful withdrawal over HTTP from a persisted account
  Given a persisted account ACC-001 with balance 200
  When a client POSTs a withdrawal of 50 to /accounts/ACC-001/withdrawals
  Then the response status is 200 and the persisted balance is 150
```

## Structure & Contracts

- **Domain vocabulary:** `Money` (`domain/models/`) — wraps `BigDecimal`; scale-insensitive equality (H2 returns `150.00`, the domain computes `150`); `minus`, `isLessThan`, `isPositive`.
- **Domain:** `AccountId` (`domain/models/account/`) — wraps the account id string; no guard, since no row demands one.
- **Domain:** `BankAccount` aggregate (`domain/models/account/`) — `accountId()`, `balance()`, `withdraw(Money): BankAccount` returning a new instance; enforces Rule 2 (strictly positive) and Rule 3 (no overdraft); identity is `AccountId`, **equality required**.
- **Domain exceptions** (`domain/models/account/`) — `InvalidWithdrawalAmount`, `InsufficientFunds` raised by the aggregate; `AccountNotFound` raised by the use case.
- **Write side:** `BankAccountRepository` port (`domain/models/account/`) — `save(BankAccount)`, `findById(AccountId): BankAccount?`. Abstract contract `BankAccountRepositoryContract` in the same package under the test source set; `FakeBankAccountRepository` (`domain/models/account/fakes/`, test source set) and `BankAccountJpaAdapter` (`infrastructure/`) each extend it.
- **Use case:** `WithdrawMoneyUseCase` (`application/`) — `withdraw(AccountId, Money): BankAccount`; loads, withdraws, saves, returns the updated aggregate. Write side, so a use case is required.
- **Infrastructure:** `BankAccountJpaAdapter` (`infrastructure/`) over an `AccountJpaEntity` + an `AccountJpaStore` Spring Data interface; explicit field mapping both ways; `save` is an upsert on the account id (the withdrawal writes over an existing row).
- **Infrastructure:** `UseCaseConfiguration` (`infrastructure/config/`) — declares the `WithdrawMoneyUseCase` bean, so `application/` stays free of framework annotations.
- **API:** `WithdrawMoneyController` (`api/`) — `POST /accounts/{accountId}/withdrawals`, body `{ "amount": 50 }` (`dto/WithdrawalRequest`), `200` with `dto/BalanceResponse { accountId, balance }`. One controller per business action.
- **API:** `DomainExceptionHandler` (`api/`, `@RestControllerAdvice`) — `AccountNotFound` → `404`, `InsufficientFunds` → `400`, `InvalidWithdrawalAmount` → `400`; the body is the framework's RFC 7807 `ProblemDetail`, which keeps one envelope across our mappings and the deserialization `400`s without shipping a bespoke error DTO no row pins. Malformed / unparseable / missing `amount` → `400` from deserialization.
- **Acceptance:** `WithdrawMoneyAcceptanceIT` (`api/`, test source set) — `@SpringBootTest` + MockMvc over the real H2 datasource; the only test that proves controller → use case → JPA adapter are wired.

## Ordered Test List (FLFI · TPP · Contradiction)

### Unit — MoneyTest
| # | Test Name (FLFI) | TPP | Contradiction (what the code-so-far wrongly assumes) | Status |
|---|------------------|-----|------------------------------------------------------|--------|
| 1 | amounts_that_differ_only_in_trailing_zeros_are_equal | n/a | Two amounts are equal only when their BigDecimal scale also matches. | ✅ RED→GREEN — red on an unresolved `Money` before the value object existed |

### Unit — BankAccountTest
| # | Test Name (FLFI) | TPP | Contradiction (what the code-so-far wrongly assumes) | Status |
|---|------------------|-----|------------------------------------------------------|--------|
| 2 | accounts_with_the_same_id_are_equal | n/a | Two loads of one account are distinct objects, so identity does not define equality. | ✅ RED→GREEN — red on an unresolved `BankAccount` |
| 3 | accounts_with_different_ids_are_not_equal | n/a | Equality ignores the id, so any two accounts are interchangeable. | ✅ RED→GREEN — red on an unresolved `BankAccount` |

### Unit — WithdrawMoneyUseCaseTest
| # | Test Name (FLFI) | TPP | Contradiction (what the code-so-far wrongly assumes) | Status |
|---|------------------|-----|------------------------------------------------------|--------|
| 4 | returns_the_balance_reduced_by_the_withdrawn_amount | nil → constant (2) | Nothing computes a balance after a withdrawal at all. | ✅ RED→GREEN — batch-red on an unresolved `WithdrawMoneyUseCase` |
| 5 | subtracts_the_amount_that_was_withdrawn_rather_than_a_fixed_one | constant → scalar (4) | The resulting balance is the same whatever amount is withdrawn. | ✅ RED→GREEN — batch-red; kills a fixed `150` return |
| 6 | reduces_the_balance_of_the_account_that_was_asked_for | constant → scalar (4) | Every id resolves to the same account, so the id need not be read. | ✅ RED→GREEN — batch-red; kills ignoring the requested id |
| 7 | saves_the_account_with_the_reduced_balance | statement → statements (5) | Returning the new balance is enough; nothing has to be persisted. | ✅ RED→GREEN — batch-red; kills dropping the `save` |
| 8 | fails_when_the_withdrawal_exceeds_the_balance | unconditional → conditional (6) | Any amount may be withdrawn regardless of the balance. | ✅ RED→GREEN — batch-red; forced the no-overdraft guard |
| 9 | allows_withdrawing_the_entire_balance | n/a | The no-overdraft guard also rejects a withdrawal exactly equal to the balance. | ✅ RED→GREEN — batch-red; kills `isLessThan` → `isLessThanOrEqualTo` in the guard |
| 10 | does_not_save_the_account_when_the_withdrawal_exceeds_the_balance | n/a | A rejected withdrawal may still have written the account before failing. | ✅ RED→GREEN — batch-red; kills saving before the guard runs |
| 11 | fails_when_the_withdrawn_amount_is_zero | unconditional → conditional (6) | Zero and negative amounts are legitimate withdrawals. | ✅ RED→GREEN — batch-red; forced the positive-amount guard |
| 12 | fails_when_the_account_does_not_exist | unconditional → conditional (6) | Every requested id has a stored account behind it. | ✅ RED→GREEN — batch-red; forced the `AccountNotFound` branch |

### Contract — BankAccountRepositoryContract
| # | Test Name (FLFI) | TPP | Contradiction (what the code-so-far wrongly assumes) | Status |
|---|------------------|-----|------------------------------------------------------|--------|
| 13 | returns_the_account_with_every_field_it_was_saved_with | n/a | A round trip preserves the account, so dropping or mis-mapping a field is invisible. | ✅ EARLY-GREEN — the fake predates the contract; killed by the mutant `save {}` (verified red) |
| 14 | returns_nothing_when_no_account_has_the_given_id | n/a | A lookup always finds something, so a missing account need not be reported. | ✅ RED→GREEN — green against the fake (mutant `findById … ?: anAccount(id)` verified red), then genuinely red against the JPA adapter |
| 15 | replaces_the_stored_account_when_an_account_with_the_same_id_is_saved | n/a | Saving always inserts, so a second save of one id leaves the old balance readable. | ✅ EARLY-GREEN — killed by the mutant `save {}` (verified red) |

### Contract runner — FakeBankAccountRepositoryTest
| # | Test Name (FLFI) | TPP | Contradiction (what the code-so-far wrongly assumes) | Status |
|---|------------------|-----|------------------------------------------------------|--------|
| 16 | (runs rows 13-15 against the fake) | n/a | The fake used by every unit test conforms to the port's contract. | ✅ EARLY-GREEN — the fake was written with the use-case batch; the two mutants above prove the runner discriminates |

### Controller — WithdrawMoneyControllerIT
| # | Test Name (FLFI) | TPP | Contradiction (what the code-so-far wrongly assumes) | Status |
|---|------------------|-----|------------------------------------------------------|--------|
| 17 | returns_200_and_the_new_balance_when_the_withdrawal_is_accepted | n/a | No route exists at all. | ✅ RED→GREEN — batch-red on an unresolved `WithdrawMoneyController` |
| 18 | withdraws_the_amount_from_the_account_named_in_the_path | n/a | The path id and the body amount need not reach the use case. | ✅ RED→GREEN — batch-red; states the delegation contract the project's API test conventions require |
| 19 | returns_400_when_the_request_body_is_malformed | n/a | Any request body can be deserialized into a withdrawal. | ✅ RED→GREEN — batch-red |
| 20 | returns_400_when_the_amount_is_missing | n/a | A body without an amount still describes a withdrawal. | ✅ RED→GREEN — batch-red |
| 21 | returns_400_when_the_amount_is_not_a_number | n/a | A non-numeric amount can be parsed into money. | ✅ RED→GREEN — batch-red |
| 22 | returns_400_when_the_withdrawal_exceeds_the_balance | n/a | An overdraft failure is an unexpected server fault. | ✅ RED→GREEN — batch-red; forced the `InsufficientFunds` mapping |
| 23 | returns_400_when_the_amount_is_not_positive | n/a | A non-positive-amount failure is an unexpected server fault. | ✅ RED→GREEN — batch-red; forced the `InvalidWithdrawalAmount` mapping |
| 24 | returns_404_when_the_account_does_not_exist | n/a | A missing account is an unexpected server fault. | ✅ RED→GREEN — batch-red; forced the `AccountNotFound` mapping |

### Contract runner — BankAccountJpaAdapterIT
| # | Test Name (FLFI) | TPP | Contradiction (what the code-so-far wrongly assumes) | Status |
|---|------------------|-----|------------------------------------------------------|--------|
| 25 | (runs rows 13-15 against the real adapter on H2) | n/a | The JPA adapter conforms to the same contract the fake does. | ✅ RED→GREEN — red with `expected: null but was: BankAccount@…` on row 14: rows leaked between test methods |

### Acceptance — WithdrawMoneyAcceptanceIT
| # | Test Name (FLFI) | TPP | Contradiction (what the code-so-far wrongly assumes) | Status |
|---|------------------|-----|------------------------------------------------------|--------|
| 26 | reduces_the_persisted_balance_when_a_withdrawal_is_posted | n/a | Controller, use case and JPA adapter are wired to each other. | ✅ RED→GREEN — red with `NoSuchBeanDefinitionException: WithdrawMoneyUseCase`; forced `UseCaseConfiguration` |

### Deleted
- `returns_the_account_id_in_the_response` — no discriminating power over row 17, which asserts the whole response body.
- `fails_when_the_withdrawn_amount_is_negative` — row 11 (zero) is the boundary; the negative case cannot fail while zero passes.
- `rejects_a_blank_account_id` — the path variable can never be blank on a matched route, and no row needs the guard.
- `returns_500_when_the_repository_fails` — no 500 mapping is defined for this scenario.
