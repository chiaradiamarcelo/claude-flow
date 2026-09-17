# SCENARIO-01: Successful deposit over HTTP into a persisted account

```gherkin
Scenario: Successful deposit over HTTP into a persisted account
  Given a persisted account ACC-001 with balance 200
  When a client POSTs a deposit of 50 to /accounts/ACC-001/deposits
  Then the response status is 200 and the persisted balance is 250
```

## Structure & Contracts

- **Domain:** `Account` aggregate root (`domain/models/account/`) — `accountId(): AccountId`, `balance(): BigDecimal`, `deposit(amount): Account` returning a new instance; has identity, **equality required** (id-based).
- **Domain:** `AccountId` value object (`domain/models/account/`) — wraps the account id string; equality by value.
- **Domain:** `DepositAmountNotPositive` and `AccountNotFound` domain exceptions (`domain/models/account/`) — raised where the rule lives, mapped to HTTP at the boundary.
- **Write side:** `AccountRepository` port (`domain/models/account/`, next to its aggregate) — `save(account)`, `findById(accountId): Account?`. Read is a primary-key load of the aggregate the port writes, so **no `*Query` and no read model** (cqrs Rule 5).
- **Contract:** abstract `AccountRepositoryContractTest` (test source set, `domain/models/account/`) — run by `FakeAccountRepositoryTest` (`domain/models/account/fakes/`) and by `AccountJpaAdapterIT` (`infrastructure/`). `Account` equality is id-based, so the full-round-trip row asserts id **and** balance explicitly.
- **Fake:** `FakeAccountRepository` (test source set, `domain/models/account/fakes/`) — in-memory map, no `clear()`.
- **Use case:** `DepositMoneyUseCase` (`application/`) — `execute(accountId, amount): Account`; the behavioural entry point this scenario is verified through. Rejects non-positive amounts, raises `AccountNotFound` for an unknown id, saves the credited account, returns it.
- **Infrastructure:** `AccountJpaAdapter` (`infrastructure/`) implements `AccountRepository` over a JPA entity `AccountRecord` and an internal Spring Data interface; explicit field mapping both ways. Schema via `ddl-auto` against in-memory H2 (already configured).
- **API:** `DepositMoneyController` (`api/`) — `POST /accounts/{accountId}/deposits`, body `{ "amount": <number> }` → `200` with `{ "accountId": ..., "balance": ... }`. One controller per business action.
- **API:** `ApiExceptionHandler` (`api/`) — `@RestControllerAdvice` mapping `DepositAmountNotPositive` → `400`, unreadable/malformed body and missing `amount` → `400`, `AccountNotFound` → `404`. Error body `{ "error": { "code": ..., "message": ... } }` for every endpoint.
- **API dto:** `DepositRequest` (`amount: BigDecimal?` — nullable so a missing field is a `400`, not a framework 500) and `AccountBalanceResponse` (`api/dto/`).

## Ordered Test List (FLFI · TPP · Contradiction)

### Unit — DepositMoneyUseCaseTest
| # | Test Name (FLFI) | TPP | Contradiction (what the code-so-far wrongly assumes) | Status |
|---|------------------|-----|------------------------------------------------------|--------|
| 1 | returns_the_new_balance_when_an_amount_is_deposited_into_an_existing_account | nil → constant (2) | No code produces a balance at all. | ✅ RED→GREEN — red with unresolved reference to DepositMoneyUseCase before any production code existed |
| 2 | adds_the_amount_that_was_deposited_rather_than_a_fixed_one | constant → scalar (4) | The new balance is the same whatever amount is deposited. | ✅ RED→GREEN — red in the same batch; green once the deposited amount became a scalar |
| 3 | adds_the_amount_to_the_balance_the_account_already_had | constant → scalar (4) | The stored account's own balance plays no part in the result. | ✅ RED→GREEN — red in the same batch; green once the stored balance became the starting point |
| 4 | saves_the_account_with_the_increased_balance_when_the_deposit_is_accepted | statement → statements (5) | The new balance only has to be returned, never persisted. | ✅ RED→GREEN — red in the same batch; green once the credited account was saved back |
| 5 | fails_when_the_deposit_amount_is_negative | unconditional → conditional (6) | Every amount is a valid deposit. | ✅ RED→GREEN — red in the same batch; green once deposit() guarded the amount |
| 6 | fails_when_the_deposit_amount_is_zero | constant → constant+ (3) | Only a strictly negative amount is an invalid deposit. | ✅ RED→GREEN — red in the same batch; green once the guard became <= zero rather than < zero |
| 7 | fails_when_no_account_has_the_requested_id | unconditional → conditional (6) | The repository always has an account for the requested id. | ✅ RED→GREEN — red in the same batch; green once a missing account raised AccountNotFound |

### Unit — AccountTest
| # | Test Name (FLFI) | TPP | Contradiction (what the code-so-far wrongly assumes) | Status |
|---|------------------|-----|------------------------------------------------------|--------|
| 8 | treats_two_accounts_with_the_same_id_as_equal | n/a | Identity-based equality holds, so every `isEqualTo(account)` elsewhere is trustworthy. | ✅ RED→GREEN — red with 'expected: Account@… but was: Account@…' under default identity equality |
| 9 | treats_two_accounts_with_different_ids_as_not_equal | n/a | Equality could be a blanket `true` and nothing would notice. | ✅ EARLY-GREEN — default identity equality already satisfied it; kept because a blanket `equals = true` mutant reddens it and nothing else would |

### Contract — AccountRepositoryContractTest
| # | Test Name (FLFI) | TPP | Contradiction (what the code-so-far wrongly assumes) | Status |
|---|------------------|-----|------------------------------------------------------|--------|
| 10 | returns_a_saved_account_with_the_id_and_balance_it_was_stored_with | n/a | The round trip preserves the account, so losing the balance is invisible. | ✅ RED→GREEN — red via AccountJpaAdapterIT (no adapter); already green via the fake |
| 11 | returns_nothing_when_no_account_has_the_id | n/a | A lookup for an unknown id can return anything at all. | ✅ RED→GREEN — red via AccountJpaAdapterIT (no adapter); already green via the fake |
| 12 | replaces_the_stored_balance_when_the_same_account_is_saved_again | n/a | Saving an id that already exists can insert a second copy. | ✅ RED→GREEN — red via AccountJpaAdapterIT (no adapter); already green via the fake |

### Contract runners
| # | Test Name (FLFI) | TPP | Contradiction (what the code-so-far wrongly assumes) | Status |
|---|------------------|-----|------------------------------------------------------|--------|
| 13 | FakeAccountRepositoryTest runs the AccountRepository contract | n/a | The fake the unit tests rely on behaves like the real adapter. | ✅ EARLY-GREEN — the fake predates the contract; kept because dropping the map write in save() reddens rows 10 and 12 |
| 14 | AccountJpaAdapterIT runs the AccountRepository contract against H2 | n/a | JPA mapping and schema match the domain, so the adapter needs no proof. | ✅ RED→GREEN — red with unresolved reference to AccountJpaAdapter, then green against H2 |

### Controller — DepositMoneyControllerIT
| # | Test Name (FLFI) | TPP | Contradiction (what the code-so-far wrongly assumes) | Status |
|---|------------------|-----|------------------------------------------------------|--------|
| 15 | returns_200_and_the_new_balance_when_the_deposit_is_accepted | n/a | No route exists at all. | ✅ RED→GREEN — red with unresolved reference to DepositMoneyController |
| 16 | returns_400_when_the_request_body_is_malformed | n/a | Every request body reaching the route is parseable JSON. | ✅ RED→GREEN — red in the same batch; green once the advice mapped HttpMessageNotReadableException |
| 17 | returns_400_when_the_amount_is_missing | n/a | A well-formed body always carries an amount. | ✅ RED→GREEN — red in the same batch; green once a null amount raised MissingDepositAmount |
| 18 | returns_400_when_the_amount_is_not_a_number | n/a | A present amount is always numeric. | ✅ RED→GREEN — red in the same batch; green via the same unreadable-body mapping |
| 19 | returns_400_when_the_deposit_amount_is_not_positive | n/a | A domain invariant violation surfaces as an unhandled 500. | ✅ RED→GREEN — red in the same batch; green once DepositAmountNotPositive mapped to 400 |
| 20 | returns_404_when_no_account_has_the_requested_id | n/a | An unknown account surfaces as an unhandled 500. | ✅ RED→GREEN — red in the same batch; green once AccountNotFound mapped to 404 |

### End-to-end — DepositMoneyEndToEndIT
| # | Test Name (FLFI) | TPP | Contradiction (what the code-so-far wrongly assumes) | Status |
|---|------------------|-----|------------------------------------------------------|--------|
| 21 | returns_200_and_persists_the_increased_balance_when_a_deposit_is_posted | n/a | Each layer passes in isolation, so the whole vertical must be wired together. | ✅ RED→GREEN — red with 'DepositMoneyController required a bean of type DepositMoneyUseCase that could not be found' |

### Deleted
- `returns_the_account_id_in_the_response` — no discriminating power over row 15, which already pins the whole response body.
- `returns_500_when_the_repository_fails` — the port has no failure result; an infrastructure fault is the framework's default 500 and no code of ours would be exercised.
- `deposits_a_fractional_amount` — same code path as row 2; the `BigDecimal` scalar is already forced there.
