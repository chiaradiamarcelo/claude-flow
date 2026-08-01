# Reviewer findings — round 3 (account-overview, read-side) BATCH arm (11: 5 test + 6 refactor)

## test-reviewer (5)
- **WARNING** no 500 / error-path test; `FakeAccountOverviewQuery` has no failure-injection seam.
- **WARNING** `returns_404_...` over-seeds an irrelevant account; drop the seed or rename.
- **WARNING** controller IT imports `kotlin.test.Test` while the rest of the suite uses `org.junit.jupiter.api.Test` (inconsistent).
- **SUGGESTION** file `AccountOverviewQuery.contract.kt` not PascalCase-matching its class name.
- **SUGGESTION** shared fixture constants live inside the contract file rather than a dedicated fixtures file.

## refactor-advisor (6)
- **WARNING** `AccountTier.PREMIUM_THRESHOLD = 1000` hard-coded business policy; extract to an injectable policy.
- **WARNING** `AccountOverviewView.tier` constructor param can contradict balance; make it a private ctor + factory (`of(accountId, balance)`).
- **SUGGESTION** adapter mapping simplifies once the view factory exists.
- **SUGGESTION** primitive obsession on `accountId: String`; consider an `AccountId` value class.
- **SUGGESTION** `AccountJpaEntity` default param values let it be built blank; prefer a JPA no-arg ctor / kotlin-jpa plugin.
- **SUGGESTION** `ApiExceptionHandler` empty 404 body; adopt a shared error-response shape as handlers grow.

---
**Note:** as in rounds 1–2, both arms surface the same core issues (no 500 test, `AccountOverviewView`
tier-invariant, hard-coded threshold, fixture builder, contract-file naming) — plan/architecture-level,
not discipline-driven. Batch drew slightly *more* findings this round (opposite of rounds 1–2),
confirming the ±few spread is noise.
