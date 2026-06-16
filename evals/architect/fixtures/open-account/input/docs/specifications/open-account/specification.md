# Specification: Open Account

## Intent & Goal

**Primary Goal**: Let a new customer open a bank account with an initial deposit,
so they can start using the bank, returning the newly created account.

**Out of Scope**: KYC/identity verification, account types beyond a single default,
joint accounts, currency selection.

**Business Rules**: Opening an account creates a new account resource with a unique
id and an initial balance. The initial balance must not be negative.

## Business Rules & Invariants
- Rule 1: A newly opened account is assigned a unique account id.
- Rule 2: The initial balance must be zero or positive (no negative opening balance).
- Rule 3: Opening is a state-changing command that creates a new account resource.

---

## Scenarios (Gherkin)

Scenario: Open a new account with a valid initial balance
  Given a customer with no account
  When the customer opens an account with an initial balance of 100
  Then a new account is created with balance 100

Scenario: Opening is rejected when the initial balance is negative
  Given a customer with no account
  When the customer opens an account with an initial balance of -10
  Then the account is not created
  And the request is rejected

---

## BDD Acceptance Progress
- [ ] SCENARIO-01: Open a new account with a valid initial balance
- [ ] SCENARIO-02: Opening is rejected when the initial balance is negative
