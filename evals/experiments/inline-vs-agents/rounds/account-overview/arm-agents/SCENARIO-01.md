# SCENARIO-01: Fetch the overview of a persisted premium account over HTTP

## Scenario

Scenario: Fetch the overview of a persisted premium account over HTTP
  Given a persisted account ACC-001 with balance 1500
  When a client GETs /accounts/ACC-001/overview
  Then the response status is 200 and the body is {accountId: ACC-001, balance: 1500, tier: PREMIUM}

## Structure & Contracts

- **Read side, no aggregate exists yet:** greenfield slice — no write-side `Account` aggregate/Repository in this codebase, and none is introduced by this scenario (out of scope per spec). The overview is projected straight from persistence, so per CQRS Rule 5/9 there is no primary-key-lookup aggregate to reuse — this is a genuine `*Query` from the start.
- **Domain vocabulary:** `Tier` enum (`PREMIUM`, `STANDARD`) at `domain/models/` (bounded-context root, shared vocabulary) — derivation rule (`balance >= 1000` → `PREMIUM`) is computed once at the adapter (CQRS Rule 6), not in the read model or controller.
- **Read model:** `AccountOverviewView` (`domain/query/`) — flat data, fields `accountId: String`, `balance: BigDecimal`, `tier: Tier`; no methods, no derivation (CQRS Rule 6). No domain identity/equality concerns beyond structural data equality for test assembly.
- **Read-side port:** `AccountOverviewQuery` (`domain/query/`) — method `findByAccountId(accountId: String): AccountOverviewView?` (nullable = not-found, per Rule 4 of the spec). Gets an abstract contract test `AccountOverviewQuery.contract.kt` (`domain/query/`); a fake (`domain/query/fakes/FakeAccountOverviewQuery.kt`, with `seed(...)` support) and a real JPA adapter (`infrastructure/AccountOverviewQueryPostgresAdapter.kt` — actually H2/JPA here) each extend it.
- **Persistence:** JPA entity `AccountJpaEntity` (`infrastructure/`, `@Entity`) with fields `accountId` (id), `balance`; adapter computes `Tier` and maps entity → `AccountOverviewView` in a mapper method. No migration tool in this stack — schema comes from JPA entity + `spring.jpa.hibernate.ddl-auto` against H2.
- **No use case:** controller injects `AccountOverviewQuery` directly (CQRS Rule 4 — pure read, no orchestration logic on the way out).
- **API:** `GET /accounts/{accountId}/overview` → `200` with `AccountOverviewResponse` (`api/dto/`: `accountId`, `balance`, `tier`) on found; `404` when the account does not exist (query returns null, per spec Rule 4) — no domain exception to map, controller branches on null result directly. Controller class: `AccountOverviewController` (`api/`).

## Ordered Test List (FLFI · TPP · Contradiction)

> Note to architect: rows 1-3 need the tier rule as a pure domain function on `Tier`
> (`domain/models/Tier.kt`, e.g. `Tier.forBalance(balance)`), not inline in the adapter —
> the threshold rule is business logic and must be driven at a framework-free seam.
> The adapter still owns calling it while mapping (CQRS Rule 6).

### Unit — TierTest
| # | Test Name (FLFI) | TPP | Contradiction (what the code-so-far wrongly assumes) | Status |
|---|------------------|-----|------------------------------------------------------|--------|
| 1 | returns_premium_when_the_balance_is_above_the_premium_threshold | nil → constant (2) | No code derives a tier from a balance at all. | ✅ RED→GREEN — red with `Unresolved reference 'Tier'`; no tier derivation existed |
| 2 | returns_standard_when_the_balance_is_below_the_premium_threshold | unconditional → conditional (6) | Every balance is PREMIUM, so a balance of 999 is premium too. | ✅ RED→GREEN — red on the same missing `Tier`; forced the `>=` branch |
| 3 | returns_premium_when_the_balance_is_exactly_the_premium_threshold | n/a | The threshold is exclusive (`> 1000`), so exactly 1000 falls to STANDARD. | ✅ RED→GREEN — red on the same missing `Tier`; pins `>=` over `>` |

### Contract — AccountOverviewQueryContractTest
| # | Test Name (FLFI) | TPP | Contradiction (what the code-so-far wrongly assumes) | Status |
|---|------------------|-----|------------------------------------------------------|--------|
| 4 | returns_every_stored_field_of_the_account_with_the_requested_id | n/a | Projection is whole, so a dropped or mis-sourced field is invisible. Seed: all columns distinctive. | ✅ RED→GREEN — red with `Unresolved reference 'AccountOverviewView'`; runs against the fake and the JPA adapter |
| 5 | returns_the_tier_derived_from_the_persisted_balance | n/a | The tier is hardcoded PREMIUM; a stored balance under 1000 still reports PREMIUM. | ✅ RED→GREEN — red on the missing port; forced both adapters to call `Tier.forBalance` |
| 6 | returns_only_the_account_whose_id_was_requested | n/a | The lookup ignores the id and returns the first stored account. Seed: 2 accounts, ask for the second. | ✅ RED→GREEN — red on the missing `findByAccountId` |
| 7 | returns_nothing_when_no_account_has_the_requested_id | n/a | Every id resolves to an account, so a missing id yields another account or an error. | ✅ RED→GREEN — also red a second time on the JPA adapter with `expected: null but was: AccountOverviewView(accountId=ACC-002, …)` from data leaking between JPA tests |

### Controller — AccountOverviewControllerIT
| # | Test Name (FLFI) | TPP | Contradiction (what the code-so-far wrongly assumes) | Status |
|---|------------------|-----|------------------------------------------------------|--------|
| 8 | returns_200_and_the_overview_body_when_the_account_exists | n/a | No route exists at `/accounts/{accountId}/overview`. | ✅ RED→GREEN — red with `Unresolved reference 'AccountOverviewController'`; body asserted as exact JSON |
| 9 | returns_404_when_no_account_has_the_requested_id | n/a | The query always yields a view, so a null result is serialized as a 200 with an empty body. | ✅ RED→GREEN — red on the same missing controller; forced the null branch |

### Deleted
- `returns_the_tier_field_in_the_response` — no discriminating power over row 8 under a mocked query.
- `returns_400_when_the_account_id_is_blank` — a blank path segment never reaches the handler; no mapped status.
- `returns_standard_tier_in_the_response_for_a_low_balance` — domain rule already pinned by rows 2 and 5; identical controller path.
- `returns_500_when_the_query_fails` — no failure mapping is defined in the structure.
