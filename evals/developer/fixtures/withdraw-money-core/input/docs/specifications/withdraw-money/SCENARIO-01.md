# SCENARIO-01: Successful withdrawal from an existing account

## Scenario

```gherkin
Scenario: Successful withdrawal from an existing account
  Given an account ACC-001 with balance 200
  When the owner withdraws 50
  Then the account balance is 150
```

## Implementation Plan

This is the framework-free core only — plain Kotlin + JUnit5, no Spring, no JPA,
no DB, no HTTP. Implement domain → port → fake → contract test → use case.

- [ ] Step 1: `BankAccountTest` — domain entity test: equality (same id = equal, different id = not equal) (red)
- [ ] Step 2: `BankAccount` — domain entity (account id, balance, `withdraw` behaviour, equality by id)
- [ ] Step 3: `BankAccountRepository` — write-side port interface (`findById`, `save`)
- [ ] Step 3b: `BankAccountRepositoryContractTest` — abstract contract test for the port
- [ ] Step 3c: `FakeBankAccountRepository` — in-memory fake implementation of the port
- [ ] Step 3d: `FakeBankAccountRepositoryContractTest` — fake contract test extending the abstract contract test
- [ ] Step 4: `WithdrawMoneyTest` — use case unit test driving the fake (red)
- [ ] Step 5: `WithdrawMoney` — use case orchestrating load → withdraw → save
- [ ] Step 6: All tests green → mark SCENARIO-01 done in `specification.md`
