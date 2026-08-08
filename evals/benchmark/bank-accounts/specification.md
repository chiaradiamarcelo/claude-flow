# Specification: Bank Accounts

> **FROZEN BENCHMARK — do not edit.** Every experimental arm runs this exact file, with
> `/intent-and-goal` skipped entirely. If the spec can move between arms, scenario-generation
> variance swamps the signal the experiment is trying to read. Changing anything here invalidates
> every prior arm.
>
> Fixture: `evals/golden-repo-spring` (Boot 3.x / JUnit 5, so PIT drives the unit tests natively).
> Baseline of record for the *Android* stack is `evals/scorecard/baseline-gym-walls.md`; it is a
> different stack and a different feature, so it is context, never a control for these arms.

## Intent & Goal

**Primary Goal**: a bank holds accounts, money moves into and out of them, and every movement is
recoverable as a statement. This is a measurement rig for the pipeline itself, so the domain is
deliberately ordinary — the point is that the *shape* of the work matches real feature work, not
that the domain is interesting.

**Who**: an account holder deposits, withdraws and transfers; a teller reads a statement.

**Out of Scope**: interest, currencies and exchange, overdrafts and credit, authentication and
authorisation, closing an account, scheduled or recurring movements, multi-bank settlement.

## Business Rules & Invariants

- **Rule 1**: **An account is identified by an account number the holder is given, and no two
  accounts share one.**
- **Rule 2**: **An account's balance is the sum of its movements, never a separately stored number
  that could disagree with them.**
- **Rule 3**: **Money only moves in positive amounts.** Zero and negative are refused, not treated
  as a no-op — a deposit of 0 that silently succeeds is indistinguishable on screen from one that
  worked.
- **Rule 4**: **An account's balance never goes below zero.** A withdrawal beyond the balance is
  refused and applies nothing.
- **Rule 5**: **A transfer moves money between two existing accounts as one change, or not at
  all.** Half a transfer is worse than no transfer: it destroys money or creates it.
- **Rule 6**: **An account's identity survives every movement.** Depositing, withdrawing or
  transferring updates the account the holder already has; it does not replace it with a new one.
- **Rule 7**: **A stored account that predates movements is not loaded.** There is no answer to
  "what movements produced this balance" that is better than admitting the bank does not know, and
  a fabricated opening movement is worse than an absent account because nothing reveals it is wrong.
- **Rule 8**: **A change that cannot be stored is reported and applies nothing.**
- **Rule 9**: **An operation naming an account the bank does not have is reported as not found**,
  and is distinguishable from an operation that was refused on its merits.

---

## Scenarios (Gherkin)

```gherkin
Scenario: SCENARIO-01 An account is opened
  Given the bank has no account "ACC-001"
  When an account "ACC-001" is opened
  Then "ACC-001" is one of the bank's accounts
  And its balance is 0

Scenario: SCENARIO-02 Money is deposited into an account
  Given an account "ACC-001" with a balance of 0
  When 50 is deposited into "ACC-001"
  Then the balance of "ACC-001" is 50

Scenario: SCENARIO-03 A deposit that is not positive is refused
  Given an account "ACC-001" with a balance of 50
  When 0 is deposited into "ACC-001"
  Then the holder is told the amount must be positive
  And the balance of "ACC-001" is still 50

Scenario: SCENARIO-04 Money is withdrawn from an account
  Given an account "ACC-001" with a balance of 50
  When 20 is withdrawn from "ACC-001"
  Then the balance of "ACC-001" is 30

Scenario: SCENARIO-05 A withdrawal beyond the balance is refused
  Given an account "ACC-001" with a balance of 30
  When 100 is withdrawn from "ACC-001"
  Then the holder is told the balance is insufficient
  And the balance of "ACC-001" is still 30

Scenario: SCENARIO-06 Money is transferred between two accounts
  Given accounts "ACC-001" with a balance of 100 and "ACC-002" with a balance of 0
  When 40 is transferred from "ACC-001" to "ACC-002"
  Then the balance of "ACC-001" is 60
  And the balance of "ACC-002" is 40
  And both are the same accounts the bank already had, not replacements

Scenario: SCENARIO-07 An account's statement lists its movements
  Given "ACC-001" was opened, received 100, and sent 40 to "ACC-002"
  When the statement for "ACC-001" is read
  Then it lists the deposit of 100 and the transfer of 40, most recent first

Scenario: SCENARIO-08 A stored account from before movements existed is not loaded
  Given a stored account from before accounts recorded their movements
  When the bank's accounts are read
  Then it is not among them

Scenario: SCENARIO-09 An operation on an unknown account is reported as not found
  Given the bank has no account "ACC-404"
  When 10 is deposited into "ACC-404"
  Then the holder is told there is no such account
```

### Notes on scenario choices

- **SCENARIO-03 and SCENARIO-05 are the two red-arrival chains, and they are the load-bearing part
  of this benchmark.** Each is red *only* if its predecessor deliberately did not build the guard —
  03 depends on 02 leaving the amount unchecked, 05 on 04 leaving the balance unchecked. The
  lookahead experiment is a test of whether a plan drafted against an in-flight predecessor stays
  valid; without a chain of this shape there is nothing to test.
- **SCENARIO-06's third `Then` is the mutant-killer of the set.** A transfer implemented as
  delete-and-recreate, or as two independent saves either of which can fail alone, passes the first
  two `Then`s and violates Rules 5 and 6 silently. It is also the scenario with the largest ripple —
  two aggregates, an atomicity obligation, a new use case and a new endpoint — so it is where the
  contract-cap experiment is most likely to show a cost if there is one.
- **SCENARIO-09 is the trivial case, deliberately.** One controller row and no domain change. It is
  the test case for the small-scenario fast path, which the gym-walls data showed is where ceremony
  overhead dominates: its SCENARIO-06 wrote 2.6× more journal than code.
- **SCENARIO-08 is the only scenario about data already on disk**, and it is the shape that found
  the single live defect in the gym-walls run — a decode seam that reported one bad record as a
  total read failure.
- **Rules 2, 6 and 8 get no scenario of their own.** Rule 2 is an implementation constraint on how
  the balance is derived, Rule 6's observable half *is* SCENARIO-06's third `Then`, and Rule 8's is
  a failure path already carried by the refusal scenarios. Dressing them as user stories would be
  dishonest.

### Expected shape (recorded before the first arm, so it is a prediction and not a rationalisation)

- **~60–65 test rows**, against gym-walls' 92 (69 of them JVM). All rows here are JVM-reachable, so
  the mutation oracle covers 100% of the suite rather than 75%.
- **Three test levels exercised** — `Unit`, `Contract`, and `Controller — …IT` — which bare Kotlin
  could not provide, and which a third of the test-designer's output contract is written for.
- **Four reviewers fire**: `arch-reviewer`, `test-reviewer`, `refactor-advisor`, and `api-reviewer`
  — the last for the first time, since gym-walls had no HTTP boundary. The two Android reviewers
  never fire here, so Stage 1's reviewer metrics cover 4 of 6 rather than 5 of 6.

---

## BDD Acceptance Progress

- [ ] SCENARIO-01: An account is opened
- [ ] SCENARIO-02: Money is deposited into an account
- [ ] SCENARIO-03: A deposit that is not positive is refused
- [ ] SCENARIO-04: Money is withdrawn from an account
- [ ] SCENARIO-05: A withdrawal beyond the balance is refused
- [ ] SCENARIO-06: Money is transferred between two accounts
- [ ] SCENARIO-07: An account's statement lists its movements
- [ ] SCENARIO-08: A stored account from before movements existed is not loaded
- [ ] SCENARIO-09: An operation on an unknown account is reported as not found
