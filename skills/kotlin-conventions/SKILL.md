---
name: kotlin-conventions
description: Kotlin style and idiom conventions for a Clean-Architecture Kotlin project. Load when writing or reviewing Kotlin code that isn't already covered by clean-architecture, testing, or tdd.
allowed-tools: Read, Glob, Grep
---

## When to use this skill

Load when writing or reviewing Kotlin production code — as a supplement to `clean-architecture`, `tdd`, and `testing`. This skill covers style choices that those skills don't already dictate.

## Type modelling

- **Data classes for entities and DTOs.** Never plain classes with getters/setters.
- **Sealed classes for finite alternatives** — UI state, result types, sealed domain unions. Never use string tags or `enum` when variants carry different payloads.
- **Interfaces for ports, no `I` prefix.** `OrderRepository`, not `IOrderRepository`. Kotlin has one keyword for interfaces; no Hungarian marker needed.
- **Extension functions for mappers** (`OrderDto.toDomain()`, `Order.toDto()`) — keeps mapping close to the DTO while leaving the domain unaware.
- **Prefer explicit return types on public functions.** Inference is fine locally; API surface should be readable at a glance.
- **Avoid `get` prefix on functions** returning values. Use noun-style names: `current()`, `orders()`, `activeUser()` — not `getCurrent()`, `getOrders()`, `getActiveUser()`. `get` in Kotlin is reserved for property getters; using it on functions leaks Java conventions.

## Downcasts

- **Avoid unsafe downcasts (`as SomeType`).** An unsafe cast is a crash waiting for the sealed class to gain a new subtype.
- Use `when` on sealed classes instead of casting — the compiler enforces exhaustiveness and smart-casts inside each branch.
- Use `is` checks or safe casts (`as?`) when the type is genuinely uncertain (e.g. deserialization, `Any`).

```kotlin
// Bad
val success = state as UiState.Success

// Good
val success = when (state) {
    is UiState.Success -> state
    is UiState.Loading -> return
    is UiState.Error -> throw AssertionError("expected Success, was Error")
}
```

## Async

- **`suspend` functions for async operations** — coroutines, not callbacks, not `Future`/`CompletableFuture`.
- **Flows for streams** of values, not `LiveData` or `Observable`. Use `StateFlow` for hot state, `SharedFlow` for events, cold `Flow` for computations.

## Dependency injection

- **No DI annotations in the domain layer.** No `@Inject`, `@Singleton`, `@Provides`, `@HiltViewModel`, or any framework annotation on domain entities, use cases, or ports.
- Domain classes take dependencies via constructor. Wiring happens in the composition root (a DI module in `:app` or wherever the DI framework lives).
- Common choices: **Koin** (pure Kotlin DSL, no annotation processing — good default for KMP); Hilt (annotation-based, Android-only).

## Design constants

- **Extract meaningful design values to named constants** — fonts, colours, icon sets, sizes, and any value that appears more than once or is likely to change. Avoid magic literals scattered across screens.
- In a Compose project, these typically live in `presentation/common/` or `presentation/theme/`.

## Files, packages, and naming

- Package names are all lowercase, no underscores.
- Filenames match the primary declaration (`OrderRepository.kt` for `interface OrderRepository`). Multiple small extensions may share a file named after the topic (`OrderMappers.kt`).
- Test files: `<ClassUnderTest>Test.kt` for unit tests; `<ClassUnderTest>IT.kt` for integration; `<ScreenName>Test.kt` for Compose UI tests.

## What this skill does NOT cover

- Layer boundaries, port/adapter placement, contract tests — see `clean-architecture`.
- RED/GREEN/REFACTOR discipline — see `tdd`.
- Test structure (GWT, fakes, no control flow in tests) — see `testing`.
- Compose UI test patterns — see `android-ui-testing`.
