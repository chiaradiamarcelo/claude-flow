# Specification: Withdraw Money

## Intent & Goal
**Primary Goal**: Withdraw money from an account, reducing the balance.
**Out of Scope**: HTTP, persistence (framework-free core).

## Scenarios (Gherkin)

Scenario: Successful withdrawal from an existing account
  Given an account ACC-001 with balance 200
  When the owner withdraws 50
  Then the account balance is 150

---

## BDD Acceptance Progress
- [ ] SCENARIO-01: Successful withdrawal from an existing account
