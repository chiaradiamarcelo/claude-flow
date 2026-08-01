# SCENARIO-01: Successful deposit over HTTP into a persisted account

## Scenario

```gherkin
Scenario: Successful deposit over HTTP into a persisted account
  Given a persisted account ACC-001 with balance 200
  When a client POSTs a deposit of 50 to /accounts/ACC-001/deposits
  Then the response status is 200 and the persisted balance is 250
```

## Context for the implementer

A FULL vertical slice on Spring Boot 4 + Spring Data JPA + H2 (in-memory), base
package `com.example.bank`, following the project's Clean Architecture layout
(aggregate-per-package on the write side; `application/` holds the UseCase;
`infrastructure/` holds the JPA adapter; `api/` holds the controller + DTOs). The
dependency rule is strict: `domain/` has NO framework imports; the JPA persistence
entity lives in `infrastructure/`, never in `domain/`. Money is modelled as
`BigDecimal`.

<!-- The architect appends "## Structure & Contracts" below.
     The test-designer then appends "## Ordered Test List (FLFI · TPP · Contradiction)". -->

## Structure & Contracts

Full vertical slice, write side only (deposit is a state-changing command; no read-side
port needed for this scenario). Base package `com.example.bank`.

- **Domain aggregate:** `com.example.bank.domain.models.account.Account`
  (`domain/models/account/Account.kt`) — aggregate root with identity `accountId: String`
  (**equality required**, based on `accountId`). Holds `balance: BigDecimal`. Exposes:
  - `fun deposit(amount: BigDecimal): Account` — returns a new `Account` with
    `balance` increased by `amount`. Enforces the single domain invariant for this
    scenario: **the amount must be strictly positive**; violating it raises a domain
    exception `InvalidDepositAmountException` (`domain/models/account/InvalidDepositAmountException.kt`).
    No overdraft / insufficient-funds rule applies here — deposit only ever increases
    the balance, so there is no upper/lower bound check beyond the positive-amount rule.
  - Construction/factory enforces `accountId` is non-blank (existing invariant, unchanged
    if already present).

- **Write-side port:** `AccountRepository` (`domain/models/account/AccountRepository.kt`)
  — write-side port, aggregate-shaped:
  - `fun findById(accountId: String): Account?` (nullable, no `Optional`)
  - `fun save(account: Account): Account`

  Gets an abstract contract test `AccountRepositoryContract`
  (`domain/models/account/AccountRepository.contract.kt`), executed indirectly (not run
  directly) by:
  - the fake's spec, `FakeAccountRepositoryTest` (`domain/models/account/fakes/`)
  - the real adapter's spec, `AccountRepositoryJpaAdapterTest` (`infrastructure/`)

- **Fake:** `FakeAccountRepository` (`domain/models/account/fakes/FakeAccountRepository.kt`)
  — in-memory `MutableMap<String, Account>`-backed implementation of `AccountRepository`,
  plus a `seed(account: Account)` helper for test setup.

- **Application use case:** `DepositMoneyUseCase`
  (`application/DepositMoneyUseCase.kt`) — the behavioural entry point this scenario is
  verified through. Constructor-injects `AccountRepository`. Public contract:
  - `fun deposit(accountId: String, amount: BigDecimal): Account` — loads the account via
    `findById`, throws `AccountNotFoundException` (`domain/models/account/AccountNotFoundException.kt`)
    when absent, calls `account.deposit(amount)` to enforce the positive-amount invariant,
    persists the result via `save`, and **returns the updated `Account` aggregate** (the
    shape the controller maps to the response DTO).

- **Infrastructure (JPA) adapter:**
  - `AccountJpaEntity` (`infrastructure/AccountJpaEntity.kt`) — `@Entity` persistence
    entity, explicit field mapping (`accountId` as `@Id`, `balance` as `BigDecimal`
    column). Framework annotations live only here, never in `domain/`.
  - `AccountJpaRepository` (`infrastructure/AccountJpaRepository.kt`) — Spring Data
    `JpaRepository<AccountJpaEntity, String>`, kept internal to the adapter as a
    persistence primitive, not exposed as domain API.
  - `AccountRepositoryJpaAdapter` (`infrastructure/AccountRepositoryJpaAdapter.kt`) —
    implements `AccountRepository`; converts `Account` ↔ `AccountJpaEntity` via mapper
    methods at the boundary; delegates to `AccountJpaRepository`.
  - Migration: H2 schema for the `account` table (`accountId` PK, `balance`), provided via
    Spring Data JPA schema generation or a migration script under
    `infrastructure/db/migration/` per project convention.

- **API layer:**
  - `DepositMoneyController` (`api/DepositMoneyController.kt`) — one controller for this
    action. `POST /accounts/{accountId}/deposits` → `200 OK` with the updated balance in
    the body (deposit mutates an existing sub-resource of an already-created account, not
    a new top-level resource, so `200` applies rather than `201`/`Location`). Constructor-
    injects `DepositMoneyUseCase`. Method body: deserialize `DepositRequest` → call
    `depositMoneyUseCase.deposit(accountId, request.amount)` → map result to
    `DepositResponse`.
  - `DepositRequest` (`api/dto/DepositRequest.kt`) — `data class DepositRequest(val amount: BigDecimal)`.
    API-layer validation is format-only (e.g. `amount` is a parseable, non-null
    `BigDecimal`); the positive-amount **business** rule is enforced solely by the domain
    (`Account.deposit`), never duplicated as a `@Min`/`@DecimalMin` annotation on the DTO.
  - `DepositResponse` (`api/dto/DepositResponse.kt`) — `data class DepositResponse(val accountId: String, val balance: BigDecimal)`,
    mapped from the `Account` returned by `DepositMoneyUseCase.deposit`.

- **Exception → status mapping:** centralized `@RestControllerAdvice`
  `ApiExceptionHandler` (`api/ApiExceptionHandler.kt`) maps:
  - `AccountNotFoundException` → `404 Not Found`
  - `InvalidDepositAmountException` → `400 Bad Request`
  - malformed/unparseable request body (e.g. non-numeric `amount`) → `400 Bad Request`
  - unhandled exceptions → `500 Internal Server Error`

  All domain exceptions stay defined in `domain/models/account/`; only the advice
  translates them to HTTP status codes, and none of them appear in the response body
  beyond a generic error message shape.

## Ordered Test List (FLFI · TPP · Contradiction)

Global build order is red→green top-to-bottom. Money is `BigDecimal`: assert amounts with
scale-insensitive comparison (`isEqualByComparingTo` / `compareTo == 0`), never `isEqualTo`
on the raw `BigDecimal` (250 vs 250.00 must not matter).

> Design note (contract rows 7–9): `Account` equality is **identity-only** (`accountId`).
> Therefore an `assertThat(found).isEqualTo(Account(...))` in the round-trip test would pass
> even if the adapter mapped the wrong `balance` (balance is outside `equals`). The projection
> guard MUST assert `balance` **explicitly** (`found.balance()` compared by value), not rely on
> whole-object equality. This is the one place the identity-only equality bites, so it is called
> out rather than left to the developer to rediscover.

### Unit — AccountTest (identity equality)
| # | Test Name (FLFI) | TPP | Contradiction | Status |
|---|------------------|-----|---------------|--------|
| 1 | accounts_with_the_same_id_are_equal_regardless_of_balance | n/a | Kills a data-class / all-fields `equals`. Two `Account`s with the same `accountId` but **different** balances (200 vs 250) must be equal — balance is not part of identity. Distinct balances are the whole point; equal balances would prove nothing. | ☐ |
| 2 | accounts_with_different_ids_are_not_equal | n/a | Kills a constant `equals` that returns `true` (or ignores id). Two `Account`s with different `accountId` (same balance so only id differs) must not be equal. | ☐ |

### Unit — DepositMoneyUseCaseTest
| # | Test Name (FLFI) | TPP | Contradiction | Status |
|---|------------------|-----|---------------|--------|
| 3 | increases_the_returned_balance_by_the_deposited_amount_when_the_account_exists | constant → scalar (4) | Code-so-far returns nothing / an unchanged account. Seed ACC-001 @ 200, deposit 50 → returned aggregate balance is 250. Forces `findById` → `account.deposit(amount)` → return. Amount (50) and start (200) differ and don't share a suspicious factor, so a mutant returning the amount, the old balance, or a hard-coded constant all diverge from 250. | ☐ |
| 4 | persists_the_increased_balance_when_the_account_exists | statement → statements (5) | Code-so-far computes the new balance and returns it **without saving** (`deposit` then no `save`). Seed ACC-001 @ 200, deposit 50, then read back via `repository.findById("ACC-001")` → 250. Kills the dropped-`save` mutant; reads the observable persisted state, not a spy count. | ☐ |
| 5 | fails_when_the_deposit_amount_is_not_positive | unconditional → conditional (6) | Code-so-far deposits any amount. Seed ACC-001, deposit `0` (the strictly-positive boundary: `> 0` vs `>= 0` only diverges at 0) → `InvalidDepositAmountException`. A negative amount would exercise the same predicate and is dropped as redundant. Also proves the balance is left unchanged (no save on the reject path). | ☐ |
| 6 | fails_when_the_account_does_not_exist | unconditional → conditional (6) | Code-so-far assumes `findById` is non-null and dereferences it. Do **not** seed; deposit into "ACC-404" → `AccountNotFoundException`, and nothing is persisted. Forces the null-guard branch before `deposit`. | ☐ |

### Contract — AccountRepositoryContract
Run indirectly by `FakeAccountRepositoryTest` (fake) and `AccountRepositoryJpaAdapterTest` (JPA adapter). Both implementations pass the identical suite.
| # | Test Name (FLFI) | TPP | Contradiction | Status |
|---|------------------|-----|---------------|--------|
| 7 | save_then_findById_returns_the_stored_account_with_its_balance | n/a | Projection/round-trip guard. `save(Account("ACC-001", 200))` then `findById("ACC-001")` returns an account with `accountId == "ACC-001"` **and** `balance` compareTo 200 (asserted explicitly — see design note; identity-only `equals` won't catch a mis-mapped balance). For the JPA adapter this also proves the `Account ↔ AccountJpaEntity` mapping both ways. Distinctive non-default values so a mutant mapping the wrong column/id diverges. | ☐ |
| 8 | findById_returns_null_when_no_account_is_stored | n/a | Zero case. Empty repository, `findById("ACC-001")` → `null`. Kills a mutant that fabricates an empty/default `Account` or throws instead of returning `null` (the shape the use-case not-found branch, row 6, depends on). | ☐ |
| 9 | save_updates_the_balance_of_an_existing_account | n/a | Deposit persists an updated aggregate under the same PK. `save(ACC-001 @ 200)` then `save(ACC-001 @ 250)`, `findById` → balance 250 (compareTo), and only one account exists for that id. Kills an insert-only mutant / duplicate-row bug; for JPA proves upsert-on-existing-PK (merge), not a second insert. | ☐ |

### Controller — DepositMoneyControllerIT
`@WebMvcTest` slice; `DepositMoneyUseCase` mocked. Assert status first, then body/delegation. TPP `n/a` (status mapping, no transformation chain).
> The API-matrix "missing required field" case is intentionally **not** a separate row: with a
> non-nullable `BigDecimal amount`, a missing field and a non-numeric field both fail in Jackson
> binding and produce the identical `400` + `verifyNoInteractions(useCase)` outcome. Row 11 covers
> that single mechanism; a second row would be redundant under the mocked use case.
| # | Test Name (FLFI) | TPP | Contradiction | Status |
|---|------------------|-----|---------------|--------|
| 10 | returns_200_and_the_updated_balance_when_the_deposit_succeeds | n/a | Happy path + delegation + mapping. Mock `deposit("ACC-001", 50)` → `Account("ACC-001", 250)`. `POST /accounts/ACC-001/deposits` `{ "amount": 50 }` → 200, body `{ "accountId": "ACC-001", "balance": 250 }`, and verify the use case was called with the path id and body amount (kills a swapped/hard-coded-arg mutant and a wrong-DTO mapping). | ☐ |
| 11 | returns_400_when_the_request_body_amount_is_not_a_number | n/a | Parse-layer failure, no domain reached. Body `{ "amount": "abc" }` → 400 and `verifyNoInteractions(useCase)`. Distinguishes format validation (400 before delegation) from the domain-invariant 400 in row 12. | ☐ |
| 12 | returns_400_when_the_deposit_amount_is_not_positive | n/a | Distinct from row 11: here the body parses, the use case **is** invoked and throws `InvalidDepositAmountException`; the advice maps it to 400. Verifies the use case was called (delegation happened) — the opposite delegation assertion from row 11. Kills a mutant that maps this exception to 500 or 404. | ☐ |
| 13 | returns_404_when_the_account_does_not_exist | n/a | Mock `deposit` throws `AccountNotFoundException`. `POST /accounts/ACC-404/deposits` → 404. Kills the mutant mapping not-found to 400/500. | ☐ |
| 14 | returns_500_when_the_deposit_fails_unexpectedly | n/a | Mock `deposit` throws a generic `RuntimeException`. → 500. Pins the fallthrough branch of `ApiExceptionHandler` and proves an unmapped failure is not silently coerced to a 4xx. | ☐ |
