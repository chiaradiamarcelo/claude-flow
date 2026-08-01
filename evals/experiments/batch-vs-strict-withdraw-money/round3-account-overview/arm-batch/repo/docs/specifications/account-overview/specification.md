# Specification: Account Overview (read-side / query slice)

## Intent & Goal

**Primary Goal**: Let a client fetch a read-only overview of an account over HTTP —
its balance and a derived membership tier — so a UI can show account status without
loading the full write-side aggregate.

**Out of Scope**: Any mutation of the account, authentication, pagination, multi-currency.
This is a **read-side (CQRS query) slice**: HTTP delivery (REST GET) and a read model
projected directly from persistence (relational, JPA against an in-memory database). It
does NOT go through the write-side aggregate or a use case — it is a query.

**Business Rules**: The overview reports the account's persisted balance and a derived
membership tier. The tier is `PREMIUM` when the balance is at least 1000, otherwise
`STANDARD`.

## Business Rules & Invariants
- Rule 1: An account is identified by a unique account id (e.g. `ACC-001`) and has a balance.
- Rule 2: The overview's `tier` is `PREMIUM` when `balance >= 1000`, else `STANDARD`
  (the boundary value 1000 is `PREMIUM`).
- Rule 3: The overview reflects the currently persisted balance.
- Rule 4: Requesting the overview of an account that does not exist is a not-found condition.

---

## Scenarios (Gherkin)

Scenario: Fetch the overview of a persisted premium account over HTTP
  Given a persisted account ACC-001 with balance 1500
  When a client GETs /accounts/ACC-001/overview
  Then the response status is 200 and the body is {accountId: ACC-001, balance: 1500, tier: PREMIUM}

---

## BDD Acceptance Progress
- [ ] SCENARIO-01: Fetch the overview of a persisted premium account over HTTP
