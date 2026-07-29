# SCENARIO-01: Successful withdrawal from an existing account

## Scenario

```gherkin
Scenario: Successful withdrawal from an existing account
  Given an account ACC-001 with balance 200
  When the owner withdraws 50
  Then the account balance is 150
```

## Structure & Contracts

Framework-free core only — plain Kotlin + JUnit5, no Spring, no JPA, no DB, no HTTP.

- **Domain:** `BankAccount` aggregate (`domain/`) — identity `accountId`, a `balance`, and a `withdraw(amount)` behaviour that returns the debited account. Has identity → **equality required** (by id).
- **Write side:** `BankAccountRepository` port (`domain/`) — `findById(accountId)` returning the account or none, and `save(account)`. Gets an abstract `BankAccountRepositoryContractTest`; the in-memory `FakeBankAccountRepository` extends it via `FakeBankAccountRepositoryContractTest`.
- **Use case:** `WithdrawMoney` (`application/`) — the behavioural entry point; loads the account, calls `withdraw`, saves it, and returns the debited account.

Scope: only the happy path of SCENARIO-01. The positive-amount and no-overdraft rules are out of this scenario.

## Ordered Test List (FLFI · TPP · Contradiction)

### Unit — WithdrawMoneyTest
| # | Test Name (FLFI) | TPP | Contradiction | Status |
|---|------------------|-----|---------------|--------|
| 1 | reduces_the_balance_by_the_withdrawn_amount_when_funds_are_sufficient | nil → constant | nothing computes a new balance yet; withdraw 50 from 200 must yield 150 (three distinct values, so echoing the balance or amount is red) | ☐ |

### Unit — BankAccountTest
| # | Test Name (FLFI) | TPP | Contradiction | Status |
|---|------------------|-----|---------------|--------|
| 2 | is_equal_to_another_account_with_the_same_id | n/a | reference equality makes two accounts with the same id unequal; seed same id + different balances | ☐ |
| 3 | is_not_equal_to_an_account_with_a_different_id | n/a | an equals ignoring id (or comparing balance) passes row 2; seed different ids + same balance | ☐ |

### Contract — BankAccountRepositoryContractTest
| # | Test Name (FLFI) | TPP | Contradiction | Status |
|---|------------------|-----|---------------|--------|
| 4 | returns_the_saved_account_for_its_id | n/a | a store that returns nothing; save one account and read it back by id | ☐ |
| 5 | returns_no_account_for_an_unknown_id | n/a | a store that returns the first row regardless of id; seed one account under a different id and look up a missing one | ☐ |
