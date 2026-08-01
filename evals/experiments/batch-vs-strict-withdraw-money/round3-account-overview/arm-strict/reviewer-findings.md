# Reviewer findings — round 3 (account-overview, read-side) STRICT arm (8: 5 test + 3 refactor)

## test-reviewer (5)
- **WARNING** no 500 / error-path test; `FakeAccountOverviewQuery` has no failure-injection seam.
- **WARNING** `AccountOverviewView(...)` constructed identically across 3 test files; extract a fixture builder.
- **SUGGESTION** controller IT hardcodes `"ACC-001"`/`1500`/`"PREMIUM"` in the expected JSON instead of interpolating the seed constants (drift risk).
- **SUGGESTION** `AccountTierTest` raw `BigDecimal` boundary literals; name them (BELOW/AT/ABOVE threshold).
- **SUGGESTION** file `AccountOverviewQuery.contract.kt` not PascalCase-matching its class name.

## refactor-advisor (3)
- **WARNING** `AccountOverviewView.tier` is a constructor param derived from balance → a mismatched (balance, tier) pair is constructible; make `tier` a computed property / factory.
- **WARNING** `AccountTier.PREMIUM_THRESHOLD = 1000` is a hard-coded business policy; consider making it configurable.
- **SUGGESTION** `ApiExceptionHandler` returns an empty 404 body; consider a structured error payload.
