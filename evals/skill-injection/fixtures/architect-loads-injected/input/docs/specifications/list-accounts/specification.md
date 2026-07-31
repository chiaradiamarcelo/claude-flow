# Specification: List Accounts

## Intent & Goal

**Primary Goal**: Let a back-office operator list all accounts with their current
balance, so they can review the portfolio at a glance.

**Out of Scope**: Pagination, filtering, sorting, per-account transaction history,
authorization rules (assume the operator may see all accounts).

**Business Rules**: The list returns every account as a lightweight summary
(account id + balance). It is a pure read — it never changes state.

## Business Rules & Invariants
- Rule 1: Each summary carries the account id and its current balance.
- Rule 2: When there are no accounts, the result is an empty list (not an error).
- Rule 3: Listing accounts must not modify any account.

---

## Scenarios (Gherkin)

Scenario: List returns all accounts with their balances
  Given accounts ACC-001 with balance 200 and ACC-002 with balance 50
  When the operator lists accounts
  Then the result contains ACC-001 with balance 200 and ACC-002 with balance 50

Scenario: List is empty when there are no accounts
  Given there are no accounts
  When the operator lists accounts
  Then the result is empty

---

## BDD Acceptance Progress
- [ ] SCENARIO-01: List returns all accounts with their balances
- [ ] SCENARIO-02: List is empty when there are no accounts
