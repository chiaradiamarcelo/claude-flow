# SCENARIO-01: Fetch the overview of a persisted premium account over HTTP

## Scenario

```gherkin
Scenario: Fetch the overview of a persisted premium account over HTTP
  Given a persisted account ACC-001 with balance 1500
  When a client GETs /accounts/ACC-001/overview
  Then the response status is 200 and the body is {accountId: ACC-001, balance: 1500, tier: PREMIUM}
```

## Context for the implementer

A **read-side (CQRS query) vertical slice** on Spring Boot 4 + Spring Data JPA + H2
(in-memory), base package `com.example.bank`, following the project's Clean Architecture +
CQRS conventions. This is the READ side: model it as a **Query** with a read model, in the
peer `query/` folder — NOT a write-side Repository + UseCase, and NOT through the account
aggregate. The derived-`tier` rule is framework-free read-model logic and lives in the read
model / query layer, never in the controller or the JPA entity. The JPA persistence entity
lives in `infrastructure/`, never in `domain/` or the read model. Money is `BigDecimal`.

<!-- The architect appends "## Structure & Contracts" below.
     The test-designer then appends "## Ordered Test List (FLFI · TPP · Contradiction)". -->

## Structure & Contracts

Read-side (CQRS query) vertical slice. Base package `com.example.bank`. No aggregate,
Repository, or UseCase is introduced — this scenario is out of the write side's scope
(Rule: pure reads plug directly into the controller).

- **Vocabulary / read model — `domain/query/`:**
  - `AccountTier` (`domain/query/AccountTier.kt`) — `enum class AccountTier { STANDARD, PREMIUM }`
    with a companion factory that is the single, intent-revealing home for the derivation
    rule: `companion object { fun forBalance(balance: BigDecimal): AccountTier }` (PREMIUM
    when `balance >= 1000`, else STANDARD; boundary 1000 is PREMIUM). This is framework-free
    logic — no Spring, no JPA imports — and is the only place the tier rule is expressed.
  - `AccountOverviewView` (`domain/query/AccountOverviewView.kt`) — `data class AccountOverviewView(val accountId: String, val balance: BigDecimal, val tier: AccountTier)`.
    Pure data, no methods: `tier` is precomputed by the adapter (via `AccountTier.forBalance`)
    at projection time, never recomputed downstream. No identity/equality obligation beyond
    the default `data class` structural equality (this is a projection, not an aggregate — no
    "equality required" note needed).

- **Read-side port — `domain/query/AccountOverviewQuery.kt`:**
  - `interface AccountOverviewQuery { fun findByAccountId(accountId: String): AccountOverviewView? }`
    — nullable return (no `Optional`), `null` signals "no such account" and is what the
    controller maps to 404.
  - Gets an abstract contract test `AccountOverviewQuery.contract.kt`, same folder, next to
    the port. The fake (`domain/query/fakes/`) and the real JPA adapter
    (`infrastructure/`) each run the contract via their own spec.

- **Fake — `domain/query/fakes/FakeAccountOverviewQuery.kt`:**
  - Implements `AccountOverviewQuery`.
  - `fun seed(view: AccountOverviewView)` — populates the in-memory store so
    `findByAccountId(view.accountId)` returns it; unseeded ids return `null`. This fake is
    the test seam for the controller slice test (no UseCase to mock).

- **Persistence — `infrastructure/`:**
  - `AccountJpaEntity` (`infrastructure/AccountJpaEntity.kt`) — `@Entity @Table(name = "accounts")`
    with `@Id val accountId: String` and `val balance: BigDecimal`. Lives only in
    infrastructure; never referenced from `domain/` or `api/`.
  - `AccountJpaRepository` (`infrastructure/AccountJpaRepository.kt`) — Spring Data
    `interface AccountJpaRepository : JpaRepository<AccountJpaEntity, String>`. Framework
    plumbing, internal to the adapter.
  - `AccountOverviewQueryJpaAdapter` (`infrastructure/AccountOverviewQueryJpaAdapter.kt`) —
    implements `AccountOverviewQuery` using `AccountJpaRepository`. `findByAccountId` loads
    the `AccountJpaEntity` by id, maps it to `AccountOverviewView` computing `tier` via
    `AccountTier.forBalance(entity.balance)`, and returns `null` when no row exists. This is
    the one place the JPA entity is converted to the read model.
  - Real adapter's contract spec (`AccountOverviewQueryJpaAdapterIT`, next to the adapter)
    runs `AccountOverviewQuery.contract.kt` against an H2-backed `AccountJpaRepository`.

- **Exception mapping — centralized, reused by all future read/write endpoints:**
  - `AccountNotFoundException` (`api/AccountNotFoundException.kt` or `domain/` if reused by a
    future write side — for this scenario, keep it in `api/` since only the controller raises
    it) — thrown by the controller when the query returns `null`.
  - `ApiExceptionHandler` (`api/ApiExceptionHandler.kt`) — `@RestControllerAdvice` with an
    `@ExceptionHandler(AccountNotFoundException::class)` mapping to `404 Not Found`. This is
    the centralized not-found→404 mapping other scenarios/endpoints can extend.

- **API — `api/`:**
  - `AccountOverviewController` (`api/AccountOverviewController.kt`) — `@RestController`,
    constructor-injects `AccountOverviewQuery` directly (no UseCase — pure read, Rule 4 of
    CQRS skill). `GET /accounts/{accountId}/overview` → looks up via
    `findByAccountId(accountId)`; `null` → throws `AccountNotFoundException`; otherwise maps
    the `AccountOverviewView` to `AccountOverviewResponse` and returns `200 OK`.
  - `AccountOverviewResponse` (`api/dto/AccountOverviewResponse.kt`) —
    `data class AccountOverviewResponse(val accountId: String, val balance: BigDecimal, val tier: AccountTier)`,
    a near pass-through serialization DTO (no derivation — `tier` arrives already computed on
    the `AccountOverviewView`).
  - Status codes this endpoint must handle: `200` (found), `404` (account does not exist, via
    `AccountNotFoundException` → `ApiExceptionHandler`).

- **Behavioural entry point for this scenario:** `AccountOverviewController.overview(accountId)`,
  backed directly by `AccountOverviewQuery.findByAccountId`. Its output shape is
  `AccountOverviewResponse(accountId, balance, tier)`, serialized as the JSON body
  `{accountId, balance, tier}` — this is the shape downstream test rows assert against.

## Ordered Test List (FLFI · TPP · Contradiction)

Read-side slice, no UseCase. Three seams: the framework-free tier rule (`AccountTier.forBalance`),
the read-side port contract (`AccountOverviewQuery`, run by BOTH the fake spec and the JPA adapter
IT), and the read controller. Global `#` order is the red→green execution order.

Shared constants used below: `ACC_001 = "ACC-001"`, `MISSING_ID = "ACC-999"`, `PREMIUM_BALANCE = 1500`,
`STANDARD_BALANCE = 999`, `BOUNDARY = 1000` (all `BigDecimal`).

ZOMBIES pass (candidates surfaced): **Z** — missing account → `null` (rows 5, 7). **O/M** — one row
by id (rows 4, 6). **B** — the `1000` tier boundary, below/at/above (rows 1–3) is the heart of this
slice. **I** — full projection shape `{accountId, balance, tier}` pinned once (row 4). **E** — no
failure/throw path in scope (query returns nullable, not `Result`; 500 is not a scenario obligation —
see note under Controller). **S** — each row seeds the minimum to force its one contradiction.

`AccountOverviewView` declares **no identity/equality obligation** (the architect's Structure note:
it is a projection, default `data class` structural equality suffices) — so no dedicated equality row.
The full-object contract row (4) exercises that structural equality end-to-end.

### Unit — AccountTierTest

Framework-free derivation rule `AccountTier.forBalance(balance)`. This is the only place the boundary
lives, so it gets the classic below/at/above triple — each row kills a distinct predicate mutant.

| # | Test Name (FLFI) | TPP | Contradiction | Status |
|---|------------------|-----|---------------|--------|
| 1 | returns_STANDARD_when_balance_is_below_1000 | nil → constant (2) | No code exists; `forBalance(999)` must yield a tier. Smallest step: return the constant `STANDARD`. Seed one value below the boundary — `999`. | ☐ |
| 2 | returns_PREMIUM_when_balance_is_above_1000 | unconditional → conditional (6) | Code-so-far always returns `STANDARD`; `forBalance(1500)` falsifies that, forcing the execution to split (`if balance >= 1000 → PREMIUM`). `1500` is unambiguously above, so it forces the branch without touching the boundary. Kills the "always STANDARD" mutant. | ☐ |
| 3 | returns_PREMIUM_when_balance_is_exactly_1000 | conditional refinement — pins `>=` over `>` (boundary of 6) | Code-so-far could satisfy rows 1–2 with `balance > 1000`, which returns `STANDARD` at exactly `1000`. Seeding the boundary `1000` (Rule 2: boundary is PREMIUM) falsifies `>`, pinning `>=`. This is the mutation guard for `>` ↔ `>=` and `>=` ↔ `>`. Off-by-one vs row 1 (`999`) closes the pair. | ☐ |

### Contract — AccountOverviewQuery (AccountOverviewQuery.contract.kt)

Abstract suite run by **two** specs: `FakeAccountOverviewQueryTest` (fake) and
`AccountOverviewQueryJpaAdapterIT` (real JPA adapter against H2). Identical rows on both = the
fake↔adapter equivalence proof; the adapter run additionally exercises real column→field mapping and
H2 schema compatibility. TPP is `n/a` (a set of consumer-facing port guarantees, not a transformation chain).

| # | Test Name (FLFI) | TPP | Contradiction | Status |
|---|------------------|-----|---------------|--------|
| 4 | returns_the_full_overview_for_a_persisted_account | n/a | The **one** full-object projection guard. Seed `ACC-001` with `balance = 1500` (every column a distinctive non-default: id ≠ default, balance ≠ 0, tier = `PREMIUM` ≠ first enum value), then assert deep-equality against the explicit literal `AccountOverviewView("ACC-001", 1500, PREMIUM)`. Flip any field and it reddens — kills a projection that drops/renames a column, maps balance from the wrong source, or fails to compute `tier` via `forBalance` at projection time. Keeps the fake honest against the adapter's real mapping. Expected value written as a literal, never derived from the seed. | ☐ |
| 5 | returns_null_when_no_account_has_the_id | n/a | Code-so-far (after row 4) can look up by id but its "not found" behaviour is unproven — a mutant could return the only stored row regardless of id, or throw. Seed `ACC-001` and query `MISSING_ID` (`ACC-999`): asymmetric id forces a genuine miss and must return `null` (Rule 4 → what the controller maps to 404). Kills "return first row" and "throw on miss" mutants. | ☐ |

> The JPA adapter's spec (`AccountOverviewQueryJpaAdapterIT`) runs rows 4–5 verbatim against an
> H2-backed `AccountJpaRepository` — no adapter-specific rows are added; contract-equivalence means the
> adapter earns its correctness through the shared suite, and row 4 through the real adapter is the
> column-mapping / schema-drift guard.

### Controller — AccountOverviewControllerIT

`@WebMvcTest`-style slice over `AccountOverviewController` + `ApiExceptionHandler`. Seam is the real
`FakeAccountOverviewQuery` via `seed(...)` (read-side pattern — no UseCase to mock). `tier` arrives
already computed on the view, so the controller does **no** derivation; tier-rule rows are unit-level
(1–3) and are deliberately NOT duplicated here (redundancy gate). Only the status/mapping matrix the
Structure defines earns controller rows. Assert status first, then body. TPP `n/a`.

| # | Test Name (FLFI) | TPP | Contradiction | Status |
|---|------------------|-----|---------------|--------|
| 6 | returns_200_and_the_overview_when_the_account_exists | n/a | Nothing yet proves the found path serializes to `200` with the contracted JSON. `seed(AccountOverviewView("ACC-001", 1500, PREMIUM))`, `GET /accounts/ACC-001/overview` → `200` and body `{accountId: "ACC-001", balance: 1500, tier: "PREMIUM"}` (full-body equality, the scenario's acceptance shape). Kills wrong-status, dropped-field, and mis-mapped-DTO mutants; the seeded `PREMIUM` tier flows through unchanged (no recompute). | ☐ |
| 7 | returns_404_when_the_account_does_not_exist | n/a | Code-so-far (after row 6) leaves the `null` path undefined — a mutant could 200 an empty body, 500, or NPE. With nothing seeded, `GET /accounts/ACC-999/overview` → query returns `null` → controller throws `AccountNotFoundException` → `ApiExceptionHandler` maps to `404`. Asserts status only. Pins the null→404 mapping (Rule 4). | ☐ |

> Status matrix scope: `200` (row 6) and `404` (row 7) are the only codes the Structure declares for
> this endpoint. `GET` has no request body/DTO, so there is no malformed-input / missing-field `400`
> to cover, and no `500` obligation (the port returns a plain nullable, not a `Result` failure) — no
> rows fabricated for codes this endpoint cannot produce.
