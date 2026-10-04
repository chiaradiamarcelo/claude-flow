---
name: api-conventions
description: HTTP / REST boundary rules — controller shape, REST URL design, request/response modeling, validation ownership, status codes, HTTP semantics, idempotency. Stack-agnostic. Invoke this skill when designing or reviewing a new HTTP endpoint, modeling request/response DTOs or error payloads, choosing HTTP methods or status codes, or drawing the line between input-format validation and domain rule enforcement.
---

Stack-agnostic rules for the HTTP boundary. Independent of application architecture (Clean / Hexagonal / classic MVC) — they cover the wire.

Use this skill when:
- Designing or reviewing a new HTTP endpoint.
- Modeling request DTOs, response DTOs, or error payloads.
- Choosing HTTP methods, status codes, or headers.
- Drawing the line between input-format validation and domain rule enforcement.

## 1. Thin controllers

- A controller's job is to deserialize input → call the use case (or read-side query) → map the response. **No business logic** lives in a controller: no domain calculations, no conditional branching on domain state, no filtering / sorting of domain data the use case should own.
- Prefer **one controller class per business action** (`DepositMoneyController`, `WithdrawMoneyController`) over a single fat controller handling many actions (`AccountController.deposit()`, `AccountController.withdraw()`, …). Per-action controllers make routing and testing surface obvious.
- Controller methods stay short — typically a handful of lines. If a method grows past ~15 lines, the logic almost certainly belongs deeper in the stack.

## 2. No domain leakage in API responses

- **Domain entities must never be returned directly from the API.** Map to a response DTO at the boundary. The shape of an HTTP response is a contract the API owes its clients; coupling it to the domain entity drags every internal field rename into a public API change.
- **Domain exceptions are mapped to HTTP status codes at the controller boundary.** The exception type stays in the domain; the controller (or a shared exception filter) translates it. Domain exceptions must not appear in the response body.

## 3. REST URL conventions

- **Resource-oriented paths.** `/accounts/{id}/deposits` — not `/doDeposit`, not `/account/deposit`.
- **Plural nouns for collections.** `/accounts`, `/orders`, `/users`. Not `/account`.
- **No verbs in URLs.** The HTTP method is the verb. `POST /accounts/{id}/deposits` not `POST /accounts/{id}/depositMoney`.
- **Nested resources for relationships.** `/accounts/{id}/transactions` when transactions belong to one account; `/transactions?accountId=…` when they're queried independently.
- **Consistent naming style.** Pick `kebab-case` *or* `camelCase` for path segments and stick to it across the whole API. Don't mix.

## 4. Input validation scope

- **The API layer validates format only**: is the JSON well-formed? Are required fields present? Are types parseable (number, ISO date, enum)?
- **Business rule validation belongs in the domain** — invariants enforced by the entity's constructor or factory, or by the use case. If your DTO has a `@Min(0)` / `@Pattern(...)` annotation that encodes a business rule, that's a violation: the domain can't trust an input that bypassed the API layer (e.g., another microservice, a test, a CLI).
- Result: every entry point into the domain reaches the same invariant enforcement.

## 5. Response modeling

- **Response DTOs contain only what the client needs.** No internal IDs, no domain implementation details, no flags the client can't act on. Each field on a public response is a contract you have to support and version.
- **Error responses follow a consistent structure** across every endpoint. Pick a shape (e.g. `{ "error": { "code": "...", "message": "...", "details": [...] } }`) and use it everywhere. Mixed shapes force every client to handle several parse paths.
- **HTTP status codes are semantically correct**:
  - `200 OK` — successful read or update that returns content.
  - `201 Created` — resource created (usually paired with a `Location` header).
  - `204 No Content` — successful operation with empty body (update with no return, delete).
  - `400 Bad Request` — malformed input, missing required field, type mismatch, **domain invariant violation** (e.g., negative amount).
  - `401 Unauthorized` — missing/invalid authentication.
  - `403 Forbidden` — authenticated but not allowed to access this resource.
  - `404 Not Found` — resource doesn't exist (for GET/PUT/PATCH/DELETE of a missing identifier).
  - `409 Conflict` — operation conflicts with current state (concurrent update, duplicate creation).
  - `500 Internal Server Error` — unexpected infrastructure/runtime failure. Use only when no more specific code applies.

## 6. HTTP semantics

- **Correct methods**:
  - `POST` for create (and for non-idempotent actions when nothing else fits).
  - `GET` for read; must be side-effect-free and cacheable.
  - `PUT` for full replacement; idempotent.
  - `PATCH` for partial update; idempotent if the patch is.
  - `DELETE` for removal; idempotent.
- **`Location` header on `201` responses** when applicable — points to the created resource's URL.
- **`Content-Type` set correctly** on all responses with a body. `application/json; charset=utf-8` is the default for JSON APIs; pick `application/problem+json` if using RFC 7807 problem details.
- **`Cache-Control` and `ETag`** when appropriate for read endpoints with heavy traffic. Out of scope for most internal APIs.

## 7. Idempotency and safety

- `GET`, `PUT`, `DELETE`, `PATCH` should be idempotent — making the same request twice produces the same result.
- `POST` is the only non-idempotent verb by default. If a POST endpoint can be retried safely, document it (or use an `Idempotency-Key` header pattern).
- A `DELETE` of a resource that doesn't exist should return `204` (idempotent) or `404` (strict). Pick one and apply consistently.
