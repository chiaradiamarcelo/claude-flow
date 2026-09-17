# Specification: Withdraw Money (HTTP + persistence vertical slice)

## Intent & Goal

**Primary Goal**: Let an account owner withdraw money from their account over HTTP,
reducing the persisted balance, so they can access their funds.

**Out of Scope**: Overdraft facilities, multi-currency accounts, scheduled/recurring
withdrawals, authentication. This slice DOES include the full vertical: HTTP delivery
(REST) and persistence (relational, via JPA against an in-memory database).

**Business Rules**: A withdrawal reduces the account balance by the withdrawn amount.
A withdrawal may not exceed the available balance. The withdrawn amount must be positive.

## Business Rules & Invariants
- Rule 1: An account is identified by a unique account id (e.g. `ACC-001`).
- Rule 2: A withdrawal amount must be strictly positive.
- Rule 3: A withdrawal may not exceed the current balance (no overdraft).
- Rule 4: After a successful withdrawal the balance is reduced by exactly the amount.

---

## Scenarios (Gherkin)

Scenario: Successful withdrawal over HTTP from a persisted account
  Given a persisted account ACC-001 with balance 200
  When a client POSTs a withdrawal of 50 to /accounts/ACC-001/withdrawals
  Then the response status is 200 and the persisted balance is 150

---

## BDD Acceptance Progress
- [ ] SCENARIO-01: Successful withdrawal over HTTP from a persisted account
