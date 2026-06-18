# SCENARIO-01: Successful withdrawal over HTTP from a persisted account

## Scenario

```gherkin
Scenario: Successful withdrawal over HTTP from a persisted account
  Given a persisted account ACC-001 with balance 200
  When a client POSTs a withdrawal of 50 to /accounts/ACC-001/withdrawals
  Then the response status is 200 and the persisted balance is 150
```

## Implementation Plan

A FULL vertical slice on Spring Boot + Spring Data JPA + H2 (in-memory):
domain → write-side port → contract test → fake → use case → JPA adapter → REST
controller. Follow the Clean Architecture layout (aggregate-per-package on the
write side; `application/` holds the UseCase; `infrastructure/` holds the JPA
adapter; `api/` holds the controller + DTOs). The base package is
`com.example.bank`. The dependency rule is strict: `domain/` has NO framework
imports; the JPA persistence entity lives in `infrastructure/`, never in `domain/`.

### Write-side core (framework-free)
- [ ] Step 1: `BankAccountTest` — domain entity test: equality by id (same id = equal, different id = not equal) and that `withdraw` reduces the balance (red)
- [ ] Step 2: `BankAccount` — aggregate root under `domain/models/account/` (account id, balance, `withdraw` behaviour, equality by id, money as `BigDecimal`). No framework imports.
- [ ] Step 3: `BankAccountRepository` — write-side port in `domain/models/account/` (`findById`, `save`)
- [ ] Step 3b: `BankAccountRepositoryContract` — abstract contract test next to the port
- [ ] Step 3c: `FakeBankAccountRepository` — in-memory fake under `domain/models/account/fakes/`
- [ ] Step 3d: `FakeBankAccountRepositoryTest` — runs the contract against the fake
- [ ] Step 4: `WithdrawMoneyUseCaseTest` — use-case unit test driving the fake (red)
- [ ] Step 5: `WithdrawMoneyUseCase` — under `application/`, orchestrating load → withdraw → save

### Persistence adapter (JPA + H2)
- [ ] Step 6: `BankAccountJpaAdapter` — under `infrastructure/`, implements `BankAccountRepository` using a JPA persistence entity (`@Entity`) + a Spring Data `JpaRepository`, both kept internal to the adapter; map persistence entity ↔ domain at the boundary
- [ ] Step 7: `BankAccountJpaAdapterTest` — `@DataJpaTest` integration test running the SAME `BankAccountRepositoryContract` against the real adapter (proves the adapter is contract-equivalent to the fake)

### HTTP delivery (REST)
- [ ] Step 8: `WithdrawRequest` / `AccountResponse` DTOs under `api/dto/`
- [ ] Step 9: `AccountController` — `POST /accounts/{id}/withdrawals` under `api/`, injects the `WithdrawMoneyUseCase`, returns `200` with the updated balance
- [ ] Step 10: `AccountControllerIT` — controller integration test (`@SpringBootTest` + `MockMvc`, or `@WebMvcTest` with the use case provided): seed account ACC-001 balance 200, POST a withdrawal of 50, assert `200` and resulting balance 150

### Done
- [ ] Step 11: All tests green via `./gradlew test` → mark SCENARIO-01 done in `specification.md`
