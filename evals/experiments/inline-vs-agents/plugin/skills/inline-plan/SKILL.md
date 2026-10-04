---
name: inline-plan
description: "[experiment arm B] Planning phase run inline — merges the architect and test-designer roles into one pass that writes, for one scenario, the Structure & Contracts skeleton and the Ordered Test List (FLFI · TPP · Contradiction) into docs/specifications/<slug>/SCENARIO-XX.md. Spawns nothing."
allowed-tools: Read, Write, Edit, Glob, Grep
---

You are planning **one scenario**, inline. You write no production code and no test code.
The output is one plan file; `inline-implement` executes it.

Prerequisite skills — already loaded once by the orchestrator, **do not re-invoke**:
`clean-architecture`, `testing` (section *Ordering & justifying the list*), plus `cqrs` if
the scenario adds a port or a read-side query and `api-conventions` if it touches HTTP.

## Inputs

1. `docs/specifications/<slug>/specification.md` — intent, business rules, scenario text.
   **Never modify it in this phase.**
2. Existing source: read what already exists (domain, ports, use cases, controllers, fakes,
   contract tests) so contracts are reused, not duplicated.

## Output — `SCENARIO-XX.md`

Write the scenario title, the Gherkin verbatim, then both sections below.

### Part 1 — `## Structure & Contracts`

A **declarative skeleton** — not a checklist, not a test list, no method names, no
assertions. Which artifacts must exist, where they live, what they must conform to.

**Budget: at most 40 lines.** One bullet per artifact. No rationale paragraphs, no
alternatives-considered, no narration of what you read on the way. Where a choice
genuinely needs defending, defend it in one clause inside the bullet — not a paragraph
beneath it. Think as hard as the scenario deserves; the cap is on what you **write down**.

```markdown
## Structure & Contracts

- **Write side:** `BankAccountRepository` port (`application/port/`) — `save`, `findById`. Gets an abstract contract test `BankAccountRepositoryContractTest` (`application/contract/`); the fake (`application/fakes/`) and the real adapter (`infrastructure/repository/`) each extend it.
- **Domain:** `BankAccount` entity (`application/domain/`) — has identity (id); **equality required**.
- **Use case:** `WithdrawMoney` (`application/usecase/`) — the behavioural entry point this scenario is verified through; returns `<shape>`.
- **API:** `POST /accounts/{id}/withdrawals` → `200`; `404` when the account does not exist; `400` on invalid amount. Map `AccountNotFound` → `404`.
```

Only what this scenario needs; skip layers that exist unchanged.

- **Write side vs read side (CQRS)** — decide before declaring a port. Write side: name
  ends in `Repository` (`save`, `findById`, `delete`), and a **use case is required**.
  Read side: name ends in `Finder` / `Query` / `Reader` / `Report` (`findAll`, `findBy*`,
  `count`); a use case is **not** required if the controller just forwards to the port —
  declare that the controller injects it directly. Only add a read-side use case when
  there is real logic on the way out.
- **Every port gets a contract test** — declare the abstract contract test and its
  placement, and that the fake and the real adapter each extend it.
- **Name the behavioural entry point and its output shape** — the return shape is part of
  the contract the rows assert against.
- **Flag domain identity** with "equality required" on the bullet.
- **Declare the API surface, not the test matrix**: resource-oriented URL, method, success
  code (`201` + `Location` for create, `204` for empty-body update, `200` for read), which
  4xx/5xx it handles, any new exception→status mapping.

### Part 2 — `## Ordered Test List (FLFI · TPP · Contradiction)`

```markdown
## Ordered Test List (FLFI · TPP · Contradiction)

### Unit — DepositMoneyUseCaseTest
| # | Test Name (FLFI) | TPP | Contradiction (what the code-so-far wrongly assumes) | Status |
|---|------------------|-----|------------------------------------------------------|--------|
| 1 | returns_the_deposited_amount_as_the_new_balance | nil → constant (2) | No code stores or returns a balance at all. | ☐ |
| 2 | credits_the_amount_that_was_deposited_rather_than_a_fixed_one | constant → scalar (4) | The new balance is the same whatever amount was deposited. | ☐ |

### Contract — AccountRepositoryContractTest
| # | Test Name (FLFI) | TPP | Contradiction (what the code-so-far wrongly assumes) | Status |
|---|------------------|-----|------------------------------------------------------|--------|
| 3 | returns_a_saved_account_with_every_movement_it_was_stored_with | n/a | The round trip preserves the account, so dropping movements is invisible. | ☐ |

### Controller — DepositMoneyControllerIT
| # | Test Name (FLFI) | TPP | Contradiction (what the code-so-far wrongly assumes) | Status |
|---|------------------|-----|------------------------------------------------------|--------|
| 4 | returns_201_and_the_new_balance_when_the_deposit_is_accepted | n/a | No route exists at all. | ☐ |

### Deleted
- `returns_the_balance_in_the_response` — no discriminating power over row 4 under a mocked use case.
```

Apply the `testing` skill's *Ordering & justifying the list (FLFI · TPP · Contradiction)*
procedure to every row — ZOMBIES first to surface candidates, FLFI names, TPP ordering,
the Contradiction/mutation lens, minimal-seed derivation, the redundancy gate, mechanism
isolation. Then these hard gates:

- **Names are snake_case and state the complete rule including its condition** (FLFI),
  from the first write, and are never renamed.
- **TPP cells cite a transformation from the canonical list by name, with its rank** —
  never an invented name or a guessed number. `n/a` for contract, equality,
  controller-status and ordering rows.
- **Every Contradiction cell names a false belief the code currently holds** — never the
  seed, never what the row "pins". If you cannot state it, the row is vacuous: delete it.
  **At most 120 characters.**
- **One continuous `#` numbering** across all tables.
- **One table per level:** `### Unit — <UseCaseName>Test`, `### Contract —
  <PortName>ContractTest`, `### Controller — <ControllerName>IT`. Include a dedicated
  equality row when the structure declares an entity with identity.
- **Redundancy gate is a delete, not a footnote** — one line each under `### Deleted`.
- **Controller rows** cover the validation matrix the status mapping implies (happy;
  malformed/parse/missing-field → 400; not-found → 404; 500 where defined); one status
  per row.
- **All rows start `☐`.**

Since planner and designer are the same author here, there is no `> Note to architect:`
back-channel — when a row needs a seam Part 1 does not have, fix Part 1 directly.

## Budget

The two sections and nothing else. No prose before the first table, no analysis of
rejected seams. A real scenario has **more rows, not longer ones**.

## Done when

`SCENARIO-XX.md` has both sections. Then hand to `inline-implement`.
