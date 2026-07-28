# Feature: Referral bonus

## Intent

When an existing customer refers a friend, the referrer is rewarded once the
friend becomes a genuine new paying customer — never in a way that can be gamed.

## Business rules

- A **referral code** uniquely identifies the referrer who owns it.
- When a **referred user completes their first purchase**, the referrer earns a
  fixed credit of **10.00** appended to the referrer's ledger.
- The credit is awarded **at most once per referred user**.
- No credit if the referred user is **not a new customer** (had a prior purchase).
- No credit if the referral code is **unknown**.
- A user may not redeem **their own** referral code.

## Ledger persistence note (infrastructure)

Credits are written through an append port. For throughput the adapter **flushes
to the DB in batches of `LEDGER_FLUSH_BATCH` (default 50)**. Batching is a
persistence concern only — it must not change which credits are awarded.

## BDD Acceptance Progress

- [ ] SCENARIO-01: Referrer earns a one-time credit when a referred new customer makes their first purchase

## Scenarios

### SCENARIO-01

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
