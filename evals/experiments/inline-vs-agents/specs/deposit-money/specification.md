# Specification: Deposit Money (HTTP + persistence vertical slice)

## Intent & Goal

**Primary Goal**: Let an account owner deposit money into their account over HTTP,
increasing the persisted balance, so their funds are available.

**Out of Scope**: Multi-currency accounts, scheduled/recurring deposits, interest,
authentication. This slice DOES include the full vertical: HTTP delivery (REST) and
persistence (relational, via JPA against an in-memory database).

**Business Rules**: A deposit increases the account balance by the deposited amount.
The deposited amount must be positive.

## Business Rules & Invariants
- Rule 1: An account is identified by a unique account id (e.g. `ACC-001`).
- Rule 2: A deposit amount must be strictly positive.
- Rule 3: After a successful deposit the balance is increased by exactly the amount.

---

## Scenarios (Gherkin)

Scenario: Successful deposit over HTTP into a persisted account
  Given a persisted account ACC-001 with balance 200
  When a client POSTs a deposit of 50 to /accounts/ACC-001/deposits
  Then the response status is 200 and the persisted balance is 250

---

## BDD Acceptance Progress
- [ ] SCENARIO-01: Successful deposit over HTTP into a persisted account
