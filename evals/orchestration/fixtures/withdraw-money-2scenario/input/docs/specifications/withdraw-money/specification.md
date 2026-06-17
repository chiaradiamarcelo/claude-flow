# Specification: Withdraw Money

## Intent & Goal
**Primary Goal**: Withdraw money from an account, reducing the balance.
**Out of Scope**: HTTP, persistence (framework-free core).

## Scenarios (Gherkin)

Scenario: Successful withdrawal from an existing account
  Given an account ACC-001 with balance 200
  When the owner withdraws 50
  Then the account balance is 150

Scenario: Withdrawal is rejected when the amount exceeds the balance
  Given an account ACC-001 with balance 200
  When the owner withdraws 250
  Then the withdrawal is rejected and the balance is unchanged

---

## BDD Acceptance Progress
- [ ] SCENARIO-01: Successful withdrawal from an existing account
- [ ] SCENARIO-02: Withdrawal is rejected when the amount exceeds the balance
