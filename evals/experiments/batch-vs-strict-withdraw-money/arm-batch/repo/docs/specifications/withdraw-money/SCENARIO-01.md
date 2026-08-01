# SCENARIO-01: Successful withdrawal over HTTP from a persisted account

## Scenario

```gherkin
Scenario: Successful withdrawal over HTTP from a persisted account
  Given a persisted account ACC-001 with balance 200
  When a client POSTs a withdrawal of 50 to /accounts/ACC-001/withdrawals
  Then the response status is 200 and the persisted balance is 150
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

> **Language: Kotlin.** The repo is Kotlin/JVM (Spring Boot 4). The `.java` suffixes and
> Java idioms (`Optional<T>`, `: void`) in the skeleton below denote *contracts*, not the
> implementation language — implement idiomatic Kotlin (nullable types / `?`, `data class`
> for DTOs, no `Optional`). Test file naming keeps the project convention (`<Name>Test`,
> controller slice `<Name>IT`).

Greenfield slice — nothing exists yet under `com.example.bank`. All artifacts below are new.

### Domain — `com.example.bank.domain.models.account`

- **`Account`** (aggregate root, `Account.java`) — has identity (`accountId`, a `String` such as `ACC-001`); **equality required** (based on `accountId`). Fields: `accountId : String`, `balance : BigDecimal`. Behaviour:
  - `withdraw(amount: BigDecimal): Account` — returns the aggregate in its new state (post-withdrawal balance); enforces the invariants below and never leaves the aggregate in a state that violates them. Enforcement is expressed through intent-revealing private predicates (e.g. `isNotPositive(amount)`, `exceedsBalance(amount)`), not inline comparisons.
  - Invariants owned by the aggregate (Rules 2–4 of the spec): withdrawal amount must be strictly positive; withdrawal may not exceed current balance; resulting balance is reduced by exactly the withdrawn amount.
  - Domain exceptions raised from `withdraw`: `InvalidWithdrawalAmountException` (non-positive amount) and `InsufficientFundsException` (amount exceeds balance). Both live in `com.example.bank.domain.models.account` (framework-free, no Spring annotations).
- **`AccountNotFoundException`** — raised by the use case (not the aggregate) when no account exists for the given id; lives in `com.example.bank.domain.models.account`.
- **`AccountRepository`** (port, `AccountRepository.java`, write side — per the `cqrs` skill this is a write-side aggregate port: it changes state and owns the consistency boundary) — lives next to `Account`:
  - `save(account: Account): void`
  - `findById(accountId: String): Optional<Account>`
- **`AccountRepositoryContractTest`** (abstract contract, `AccountRepositoryContractTest.java`, same package) — the shared behavioural suite every `AccountRepository` implementation must satisfy. Excluded from direct test runs; invoked only via the concrete specs below.
- **`FakeAccountRepository`** (`com.example.bank.domain.models.account.fakes`) — in-memory `AccountRepository` for use-case and controller-slice tests. Its spec (`FakeAccountRepositoryTest`) extends `AccountRepositoryContractTest`.

### Application — `com.example.bank.application`

- **`WithdrawMoneyUseCase`** (`WithdrawMoneyUseCase.java`) — the behavioural entry point this scenario is verified through. Concrete class (no interface), constructor-injected with `AccountRepository`. Orchestrates only:
  - `execute(accountId: String, amount: BigDecimal): Account` — loads the account via `findById` (throws `AccountNotFoundException` if absent), delegates invariant enforcement to `Account.withdraw`, persists the result via `save`, and **returns the updated `Account`** aggregate — this is the return shape the controller maps to its response DTO.

### Infrastructure — `com.example.bank.infrastructure`

- **`AccountJpaEntity`** (`infrastructure/persistence/AccountJpaEntity.java`) — JPA persistence entity (`@Entity`), field-mapped explicitly (`accountId` as `@Id`, `balance`); lives only in `infrastructure/`, never in `domain/`.
- **`AccountJpaRepository`** (`infrastructure/persistence/AccountJpaRepository.java`) — Spring Data JPA repository interface over `AccountJpaEntity`; internal persistence primitive, not exposed as domain API.
- **`AccountRepositoryAdapter`** (`infrastructure/persistence/AccountRepositoryAdapter.java`) — implements the domain `AccountRepository` port; converts `Account` ↔ `AccountJpaEntity` at the boundary via an explicit mapper method. Its spec (`AccountRepositoryAdapterIT`, using H2) extends `AccountRepositoryContractTest`.
- **H2 seed data** for the persisted fixture account `ACC-001` (balance 200) needed by this scenario's integration test — via test-scoped `data.sql`/`@Sql` or an equivalent seeding mechanism local to the adapter/controller integration tests, not production code.

### API — `com.example.bank.api`

- **`WithdrawMoneyController`** (`api/WithdrawMoneyController.java`) — one controller for this single business action; thin: deserialize → call `WithdrawMoneyUseCase.execute` → map to response DTO. Constructor-injected with `WithdrawMoneyUseCase`.
- **Route:** `POST /accounts/{accountId}/withdrawals` (resource-oriented, plural noun, no verb in the URL).
- **Request DTO:** `WithdrawalRequest` (`api/dto/WithdrawalRequest.java`) — `amount : BigDecimal`. Format-only validation at this layer (e.g. field present, parseable as a number); the positivity/overdraft *business* rules stay in the domain (`Account.withdraw`), not as annotations on this DTO.
- **Response DTO:** `WithdrawalResponse` (`api/dto/WithdrawalResponse.java`) — `accountId : String`, `balance : BigDecimal`. Never returns the `Account` aggregate directly.
- **Status codes / exception mapping:**
  - `200 OK` with `WithdrawalResponse` body on success (read/update-with-content semantics; no new resource is created, so no `201`/`Location`).
  - `404 Not Found` — map `AccountNotFoundException`.
  - `400 Bad Request` — map `InvalidWithdrawalAmountException` and `InsufficientFundsException` (domain invariant violations), and malformed/missing `amount` in the request body.
  - `500 Internal Server Error` — unexpected infrastructure failures, no more specific mapping applies.
- Exception → status mapping is centralized (e.g. a `@RestControllerAdvice`/exception-handling component in `api/`) rather than embedded as branching logic inside the controller method.

## Ordered Test List (FLFI · TPP · Contradiction)

The Gherkin scenario is the happy vertical, but the architect's structure hands the aggregate the full invariant set (Rules 2–4). Those non-happy outcomes are pinned once, at the unit level (`AccountTest`) where they live; the controller only proves the exception→status **mapping**, never re-litigates the domain rule. The scenario's "persisted balance is 150" is proven by composition — adapter contract (persistence) + use case (orchestration) + controller slice (HTTP) — not by one slow end-to-end test. Global `#` runs unbroken across all four levels; execute red→green in this order.

> **Equality vs. projection guard (design note the developer must honour).** The architect specifies `Account` equality is **identity-only** (`accountId`). That deliberately weakens the usual "assert the whole object with `isEqualTo`" projection guard: `assertThat(found).isEqualTo(Account("ACC-001", 150))` would stay green even if the stored balance were wrong, because `equals` ignores `balance`. Therefore the repository round-trip row (#8) MUST assert `balance()` **explicitly via the accessor**, not lean on `isEqualTo` alone. Rows #6–#7 pin the identity semantics that every other `isEqualTo(anAccount)` in the suite silently depends on.

### Unit — `AccountTest`

| # | Test Name (FLFI) | TPP | Contradiction | Status |
|---|------------------|-----|---------------|--------|
| 1 | `reduces_balance_by_the_withdrawn_amount` | nil → constant (2) | No `withdraw` behaviour exists — a caller gets nothing / an unchanged aggregate. Seed balance 200, withdraw 50, expect 150. Forces the method into existence (a constant `150` still satisfies this row — row #2 breaks that). | ✅ |
| 2 | `allows_withdrawing_the_entire_balance_leaving_zero` | constant → scalar (4) | Code-so-far returns the constant `150` and has no notion the full balance may be withdrawn. Seed balance 200, withdraw 200, expect 0. Forces real `balance - amount`, and pins the Rule 3 boundary as *allowed* (`amount == balance` succeeds). | ✅ |
| 3 | `rejects_a_withdrawal_that_exceeds_the_balance` | unconditional → conditional (6) | Code-so-far always subtracts and would return a negative balance. Seed balance 100, withdraw 150, expect `InsufficientFundsException`. Boundary partner to #2: #2 proved `==` allowed, this proves `>` rejected — together they pin `>` vs `>=` (`exceedsBalance`). | ✅ |
| 4 | `rejects_a_zero_withdrawal_amount` | unconditional → conditional (6) | Code-so-far accepts any amount as valid. Withdraw 0 from balance 200, expect `InvalidWithdrawalAmountException`. Introduces the `isNotPositive` branch; pins the lower boundary of Rule 2. | ✅ |
| 5 | `rejects_a_negative_withdrawal_amount` | unconditional → conditional (6, predicate refinement) | After #4 a `amount == 0` predicate would wrongly *accept* a negative amount. Withdraw -50, expect `InvalidWithdrawalAmountException`. #4 (zero) + this (negative) together force `isNotPositive` to `amount <= 0` rather than `== 0` or `< 0`. | ✅ |
| 6 | `equal_when_account_ids_match` | n/a | Default reference / data-class equality treats two instances as unequal (or compares `balance`). Two accounts with the **same** `accountId` but **different** balances must be equal — kills an all-fields `equals` mutant and proves identity semantics. | ✅ |
| 7 | `not_equal_when_account_ids_differ` | n/a | An `equals` that ignores identity (or always returns true) passes vacuously. Two accounts with **different** `accountId` but the same balance must be unequal. | ✅ |

### Contract — `AccountRepositoryContractTest`
*(realized by `FakeAccountRepositoryTest` and, against H2, by `AccountRepositoryAdapterIT` — both extend this suite. The adapter IT is the JPA contract-equivalence proof: the round-trip row exercises the `Account ↔ AccountJpaEntity` mapper in both directions, so a dropped/mis-mapped column reddens it. Configure the adapter IT's ORM to validate schema against migrations rather than auto-generate.)*

| # | Test Name (FLFI) | TPP | Contradiction | Status |
|---|------------------|-----|---------------|--------|
| 8 | `save_then_find_by_id_returns_the_saved_account` | n/a | A `findById` that returns a fictional / half-mapped account, or a `save` that drops the balance, passes on a key-only check. Seed one fully-populated account (`ACC-001`, balance 200), `save`, `findById("ACC-001")`; assert identity **and** `balance()` explicitly (see equality note). This is the one full-shape/round-trip test — the mapper's mutation guard. | ✅ |
| 9 | `find_by_id_returns_empty_when_no_account_exists` | n/a | An implementation that fabricates an empty/zero account (or throws) for an unknown id. `findById("MISSING")` on an empty store must return the empty/absent result — the Z(ero) case the use case's not-found branch (#13) relies on. | ✅ |
| 10 | `save_overwrites_the_existing_account_for_the_same_id` | n/a | A `save` that inserts a duplicate instead of updating would leave two rows / stale balance — the withdrawal would never persist. `save(ACC-001, 200)` then `save(ACC-001, 150)`, `findById` returns exactly one account with balance 150. | ✅ |

### Unit — `WithdrawMoneyUseCaseTest`
*(uses `FakeAccountRepository` from setup; per-test seeding inside each method.)*

| # | Test Name (FLFI) | TPP | Contradiction | Status |
|---|------------------|-----|---------------|--------|
| 11 | `withdraws_the_requested_amount_and_returns_the_updated_account` | statement → statements (5) | No use case exists — nothing loads, delegates and returns. Seed `ACC-001` balance 200 in the fake, `execute("ACC-001", 50)`, expect the returned aggregate's `balance()` is 150. Proves load → `Account.withdraw` → return of the *updated* aggregate (the shape the controller maps). | ✅ |
| 12 | `persists_the_updated_account` | statement → statements (5) | #11's return value comes straight from `withdraw`; a use case that computes but forgets to `save` stays green there. Seed `ACC-001` balance 200, `execute("ACC-001", 50)`, then `findById("ACC-001")` through the fake returns balance 150 — kills the dropped-`save` mutant. | ✅ |
| 13 | `fails_when_no_account_exists_for_the_id` | unconditional → conditional (6) | Code-so-far assumes `findById` always yields an account and would NPE / proceed. `execute("MISSING", 50)` on an empty fake expects `AccountNotFoundException` — the not-found branch owned by the use case (not the aggregate). | ✅ |

> Domain rejections (insufficient funds, non-positive amount) are **not** re-tested here: the use case only delegates to `Account.withdraw`, which pins them at #3–#5, and their HTTP mapping is pinned at #16–#17. A propagation row here would be vacuous (no catch to break).

### Controller — `WithdrawMoneyControllerIT`
*(slice test — `@WebMvcTest`-style, `WithdrawMoneyUseCase` mocked. Assert status first, then payload / delegation.)*

| # | Test Name (FLFI) | TPP | Contradiction | Status |
|---|------------------|-----|---------------|--------|
| 14 | `returns_200_and_the_new_balance_when_the_withdrawal_succeeds` | n/a | No route / no mapping to `WithdrawalResponse`. Mock `execute("ACC-001", 50)` → `Account("ACC-001", 150)`; `POST /accounts/ACC-001/withdrawals {"amount":50}` returns 200, body `{accountId:"ACC-001", balance:150}`, and the use case is called with `("ACC-001", 50)`. Pins route, DTO shape (never the aggregate), path-var + body binding, delegation. | ✅ |
| 15 | `returns_404_when_the_account_does_not_exist` | n/a | Advice lacks an `AccountNotFoundException` mapping → leaks as 500. Mock throws `AccountNotFoundException` → expect 404. | ✅ |
| 16 | `returns_400_when_the_amount_exceeds_the_balance` | n/a | Advice lacks an `InsufficientFundsException` mapping. Mock throws `InsufficientFundsException` → expect 400. Distinct exception→status entry from #15/#17 — a mutant mapping only one type stays green on the others. | ✅ |
| 17 | `returns_400_when_the_amount_is_not_positive` | n/a | Advice lacks an `InvalidWithdrawalAmountException` mapping. Mock throws `InvalidWithdrawalAmountException` → expect 400. Second distinct domain-invariant mapping the advice must own. | ✅ |
| 18 | `returns_400_when_the_amount_field_is_missing` | n/a | A controller that treats a missing/unparseable `amount` as valid (or reaches the use case with null). `POST` body `{}` → 400 **and** the use case is never invoked. Pins the format-only validation boundary (same path as malformed JSON). | ✅ |
| 19 | `returns_500_when_the_use_case_fails_unexpectedly` | n/a | An unmapped runtime fault would surface as a 200 or a framework default. Mock throws a generic `RuntimeException` → expect 500 (the catch-all the structure defines). | ✅ |
