# Specification: Withdraw Money

## Intent & Goal

**Primary Goal**: Let an account owner withdraw money from their account, reducing
the balance, so they can access their funds.

**Out of Scope**: Overdraft facilities, multi-currency accounts, scheduled/recurring
withdrawals, HTTP/REST delivery, persistence (this slice is the framework-free core).

**Business Rules**: A withdrawal reduces the account balance by the withdrawn amount.
A withdrawal may not exceed the available balance. The withdrawn amount must be positive.

## Business Rules & Invariants
- Rule 1: An account is identified by a unique account id (e.g. `ACC-001`).
- Rule 2: A withdrawal amount must be strictly positive.
- Rule 3: A withdrawal may not exceed the current balance (no overdraft).
- Rule 4: After a successful withdrawal the balance is reduced by exactly the amount.

---

## Scenarios (Gherkin)

Scenario: Successful withdrawal from an existing account
  Given an account ACC-001 with balance 200
  When the owner withdraws 50
  Then the account balance is 150

---

## BDD Acceptance Progress
- [ ] SCENARIO-01: Successful withdrawal from an existing account
