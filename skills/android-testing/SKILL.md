---
name: android-testing
description: General Android test conventions — JVM vs instrumented source-set choice, Robolectric caveats, MainCoroutineRule, JVM-first escalation. Load when writing or reviewing Android tests that aren't strictly Compose UI (which has its own android-ui-testing skill).
allowed-tools: Read, Write, Edit, Glob, Grep, Bash
---

## When to use this skill

Load when writing or reviewing Android tests **other than Compose UI tests** — those have their own `android-ui-testing` skill. Typical fits:

- Deciding whether a test belongs in `src/test/` (JVM) or `src/androidTest/` (emulator)
- Writing ViewModel tests with coroutines
- Working with Robolectric (including its CMP-resource limitations)
- Testing platform adapters (permission wrappers, intent builders, calendar launchers)

This skill supplements the base `testing` skill — all rules from `testing` still apply. This skill adds Android-specific conventions and constraints.

## Source-set choice — JVM first

Prefer JVM unit tests. Always. They're an order of magnitude faster than instrumented tests and don't need an emulator to be running.

The layered strategy, from fastest to slowest:

| Layer | Location | Runs on | Command | Use for |
|---|---|---|---|---|
| Unit tests | `src/test/` | JVM | `./gradlew testDebugUnitTest` | Domain, use cases, ViewModels, mappers, formatters |
| Narrow integration | `src/androidTest/` | Emulator | `./gradlew connectedAndroidTest` | Adapters that require real Android context or assets |
| Compose UI | `src/androidTest/` | Emulator | `./gradlew connectedAndroidTest` | Visual rendering + user interaction (see `android-ui-testing`) |

### Escalation ladder

Before adding an instrumented test, exhaust the faster options:

1. **Replace the Android dependency with a fake.** Wrap the framework class behind an interface, inject a fake in tests.
2. **Move the logic into a pure Kotlin class.** If the code has non-trivial branching or state, it likely doesn't need Android at all — extract it into `domain/` or a helper and unit-test it on the JVM.
3. **Test in the ViewModel on the JVM.** Only escalate to an instrumented Compose test for visual verification of the rendered result.
4. **Only when 1–3 fail, write the instrumented test.** Some behaviors genuinely need the emulator (context types, permissions, intent flags, real `SharedPreferences`).
5. **Manual QA is the fallback of last resort** — never declare a behavior "untestable" without walking the whole ladder first.

## Robolectric — what it can and cannot do

Robolectric runs Android tests on the JVM by faking out the framework. It's fast, but it doesn't emulate everything.

### Robolectric works for
- Android adapters that call into `Context` / `SharedPreferences` / `PackageManager` for structural work (permission wrappers, intent builders, resource string lookups against the platform R-file).
- Non-CMP resource lookups via the platform `R.string.*` / `R.drawable.*`.

### Robolectric does NOT work for
- **Compose Multiplatform resources** (`Res.string.*`, `Res.drawable.*`, `Res.font.*`). The CMP resource loader is not compatible with Robolectric's resource pipeline. Any test that renders a composable calling `stringResource(Res.string.…)` or `painterResource(Res.drawable.…)` **must be instrumented** (`src/androidTest/`), not Robolectric (`src/test/`).
- Rendering-heavy Compose paths that need the real Android graphics pipeline.

### Fake `DrawableResource` for JVM tests

When you need a `DrawableResource` value in a JVM unit test that never actually paints (e.g., asserting a formatter picked the right drawable), build a stub with the internal constructor:

```kotlin
@OptIn(InternalResourceApi::class)
private val TEST_IMAGE = DrawableResource("test_id", emptySet())
```

This is safe for non-rendering tests (formatters, mappers). It **crashes in instrumented tests** because CMP tries to load the ID from resources — in instrumented tests use a real `Res.drawable.*`.

## Coroutine tests

### `MainCoroutineRule` for ViewModel tests

ViewModels use `viewModelScope`, which dispatches on `Dispatchers.Main`. On the JVM there's no Main dispatcher, so tests need a rule that installs a `TestDispatcher` before each test and resets it after.

```kotlin
class MainCoroutineRule(
    private val dispatcher: TestDispatcher = StandardTestDispatcher(),
) : TestWatcher() {

    override fun starting(description: Description) {
        super.starting(description)
        Dispatchers.setMain(dispatcher)
    }

    override fun finished(description: Description) {
        super.finished(description)
        Dispatchers.resetMain()
    }
}
```

Use it in every ViewModel test:

```kotlin
class FestivalsViewModelTest {

    @get:Rule
    val coroutineRule = MainCoroutineRule()

    @Test
    fun `emits Success state with sorted festivals on load`() = runTest {
        val useCase = FakeGetFestivals(listOf(festival1, festival2))
        val viewModel = FestivalsViewModel(useCase, fakeStore, fakeFavourites, fakeClock)

        val state = viewModel.uiState.first { it is FestivalFeedState.Success }

        assertEquals(2, (state as FestivalFeedState.Success).festivals.size)
    }
}
```

### `runTest` for coroutine bodies

Wrap any coroutine-driving test body in `runTest { … }`. Never launch coroutines from a plain test body without a `TestScope` — you'll get flaky results because uncompleted work escapes the test's lifetime.

- `advanceTimeBy(ms)` / `advanceUntilIdle()` inside `runTest` deterministically move virtual time forward.
- Never `Thread.sleep` in a coroutine test. Ever.

### Avoid `viewModel.uiState.first { … condition … }` as a substitute for a proper wait

If every test in a file starts with `val state = viewModel.uiState.first { it is Success }`, extract a helper (`viewModel.awaitSuccess()`) — see `testing`'s "Repeated construction = extract a helper" rule. The helper also becomes the natural home for a sealed-hierarchy assertion helper (see `testing`'s "Sealed-hierarchy assertion helpers" rule).

## Platform adapter tests

Platform adapters (permission controllers, calendar launchers, share launchers, URL openers, back handlers) are the layer where Android framework types leak into the codebase. Test them narrowly.

- **Test through the port they implement**, not through their internal `Intent` / `PackageManager` details (see the base `testing` skill: "Test adapters through their public interface"). The consumer cares about "share was launched with this text," not "the Intent has `ACTION_SEND` and `EXTRA_TEXT`."
- **Robolectric is often enough.** If the adapter builds an `Intent` and hands it to `startActivity`, a Robolectric test can inspect the launched `ShadowIntent` without an emulator.
- **When the framework's behavior can't be faked** (real permission dialogs, real system settings screens), the test escalates to instrumented — but that's rare; most adapter logic is pure `Intent`-shaping code.

## What this skill does NOT cover

- Compose UI tests (screen rendering, user gestures, robot pattern, test tags, screen-state testing) — see `android-ui-testing`.
- Language-neutral test structure (GWT, naming, no control flow, fixture builders, assertions) — see the base `testing` skill.
- Kotlin idioms (sealed classes, no unsafe casts, `suspend`) — see `kotlin-conventions`.
