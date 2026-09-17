# SCENARIO-01: Fetch the overview of a persisted premium account over HTTP

```gherkin
Scenario: Fetch the overview of a persisted premium account over HTTP
  Given a persisted account ACC-001 with balance 1500
  When a client GETs /accounts/ACC-001/overview
  Then the response status is 200 and the body is {accountId: ACC-001, balance: 1500, tier: PREMIUM}
```

## Structure & Contracts

- **Read side (CQRS), no write side, no use case** — the slice is a pure projection; per `cqrs` Rule 4 the controller injects the port directly.
- **Port:** `AccountOverviewQuery` (`domain/query/`) — `findByAccountId(accountId: String): AccountOverview?`; `null` means no such account.
- **Read model:** `AccountOverview` (`domain/query/`) — data only: `accountId: String`, `balance: BigDecimal`, `tier: MembershipTier`. No methods, no derivation at read time (`cqrs` Rule 6).
- **Vocabulary:** `MembershipTier` enum (`domain/query/`) — `PREMIUM`, `STANDARD`, plus `forBalance(balance: BigDecimal)` carrying Rule 2 (`>= 1000` ⇒ `PREMIUM`). Read-side only, so it stays in `query/` rather than the shared `models/` root.
- **Contract test:** abstract `AccountOverviewQueryContractTest` in `src/test/.../domain/query/` next to the port; abstract `seed(accountId, balance)` + `query` seams. Both implementations extend it.
- **Fake:** `FakeAccountOverviewQuery` (`domain/query/fakes/`) with `seed(accountId, balance)`; derives the tier through `MembershipTier.forBalance` so it cannot drift from the adapter. Its spec `FakeAccountOverviewQueryTest` extends the contract.
- **Adapter:** `AccountOverviewQueryJpaAdapter` (`infrastructure/`) over a JPA `AccountRecord` entity (`accountId` PK, `balance` `DECIMAL(19,2)`) and an internal Spring Data `AccountJpaRepository`. Derives the tier at projection time. Its spec `AccountOverviewQueryJpaAdapterIT` (`@DataJpaTest`) extends the contract.
- **API:** `AccountOverviewController` (`api/`) — `GET /accounts/{accountId}/overview` → `200` with `AccountOverviewResponse` (`accountId`, `balance`, `tier`); `404` when the port returns `null`. No request body, so no `400` row.
- **No entity with identity in this scenario** — no equality row.

## Ordered Test List (FLFI · TPP · Contradiction)

### Unit — MembershipTierTest
| # | Test Name (FLFI) | TPP | Contradiction (what the code-so-far wrongly assumes) | Status |
|---|------------------|-----|------------------------------------------------------|--------|
| 1 | returns_standard_when_the_balance_is_below_1000 | nil → constant (2) | No tier is derived from a balance at all. | ✅ RED→GREEN — red with `Unresolved reference 'MembershipTier'` before the enum existed |
| 2 | returns_premium_when_the_balance_is_exactly_1000 | unconditional → conditional (6) | Every balance yields STANDARD, however large. | ✅ RED→GREEN — red in the same batch; green once `forBalance` branched on the threshold |
| 3 | returns_premium_when_the_balance_is_above_1000 | n/a | Only a balance of exactly 1000 is premium. | ✅ RED→GREEN — red in the same batch; kills the `== 1000` mutant rows 1–2 leave alive |

### Contract — AccountOverviewQueryContractTest
| # | Test Name (FLFI) | TPP | Contradiction (what the code-so-far wrongly assumes) | Status |
|---|------------------|-----|------------------------------------------------------|--------|
| 4 | returns_every_stored_field_of_the_overview_for_a_persisted_account_id | n/a | The projection can drop or mis-source a field unnoticed. | ✅ RED→GREEN — red with `Unresolved reference 'AccountOverviewQuery'` for both implementations |
| 5 | returns_nothing_when_no_account_has_the_requested_id | n/a | Every lookup finds an account. | ✅ RED→GREEN — red in the same batch for both implementations |
| 6 | returns_the_overview_of_the_requested_account_when_other_accounts_are_persisted | n/a | The lookup may ignore the id and return any stored account. | ✅ RED→GREEN — red in the same batch for both implementations |

### Controller — AccountOverviewControllerIT
| # | Test Name (FLFI) | TPP | Contradiction (what the code-so-far wrongly assumes) | Status |
|---|------------------|-----|------------------------------------------------------|--------|
| 7 | returns_200_and_the_account_overview_when_the_account_exists | n/a | No route exists at all. | ✅ RED→GREEN — red with `Unresolved reference 'AccountOverviewController'` |
| 8 | returns_404_when_no_account_has_the_requested_id | n/a | A missing account is indistinguishable from a found one. | ✅ RED→GREEN — red in the same batch |

### Deleted
- `returns_premium_tier_in_the_response_body` — no discriminating power over row 7, which pins the whole body.
- `returns_the_balance_of_the_requested_account_over_http` — same body assertion as row 7; vacuous.
- `returns_standard_when_the_balance_is_zero` — row 1 already fails under the same contradiction.
