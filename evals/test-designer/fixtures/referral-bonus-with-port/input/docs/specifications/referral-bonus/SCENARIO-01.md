# SCENARIO-01: Referrer earns a one-time credit when a referred new customer makes their first purchase

## Scenario

```gherkin
Scenario: Referrer earns a one-time credit when a referred new customer makes their first purchase
  Given a referrer "R" owns referral code "GOLD"
  And "F" is a new customer who has never purchased before
  When "F" completes their first purchase carrying code "GOLD"
  Then referrer "R" is credited 10.00
  And a later second purchase by "F" credits R nothing more
  And a purchase carrying an unknown code credits no one
  And a purchase where "F" redeems their own code credits no one
  And "F" purchasing after already having bought before credits no one
```

## Structure & Contracts

- **Read side:** `ReferralCodeFinder` port (`application/port/`) — `findReferrerByCode(code)` returns the owning referrer id or none. Read-only lookup; no use case of its own.
- **Write side:** `ReferralLedger` port (`application/port/`) — `append(credit)`. Owns the ledger append; gets an abstract contract test `ReferralLedgerContractTest` (`application/contract/`); the fake (`application/fakes/`) and the real adapter (`infrastructure/repository/`) each extend it. The real adapter flushes to the DB in batches of `LEDGER_FLUSH_BATCH` (default 50); the fake appends immediately.
- **Domain:** `ReferralCredit` entity (`application/domain/`) — has identity (id); **equality required**. Carries referrer id, referred-user id, amount.
- **Use case:** `AwardReferralCredit` (`application/usecase/`) — the behavioural entry point; resolve code → validate (known / not self / referred user is new / not already awarded) → append credit. Returns nothing (fire-and-forget append).
- **API:** `POST /purchases` (the purchase-completion endpoint that may carry a referral code) → `201`; `400` on malformed body / missing required purchase fields. A non-awarding domain outcome (unknown/self code) is a side effect, not a client error.
