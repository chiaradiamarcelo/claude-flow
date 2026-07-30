---
name: android-ui-testing
description: Use whenever writing, modifying, or reviewing Compose UI tests (Robolectric or instrumented). Defines the robot pattern, test tag conventions, Voyager-specific patterns, and Robolectric limitations.
allowed-tools: Read, Write, Edit, Glob, Grep, Bash
---

## When to use this skill

Invoke when writing or reviewing:
- Robolectric Compose UI tests (`src/test/` with `@RunWith(AndroidJUnit4::class)`)
- Instrumented Compose UI tests (`src/androidTest/`)
- Navigation contract tests
- Any test that uses `createComposeRule()` or `createAndroidComposeRule()`

This skill supplements the base `testing` skill — all rules from `testing` still apply. This skill adds Compose-specific conventions.

Inline examples use a hypothetical `Festival` domain type and a search screen for illustration. Substitute your codebase's actual domain types and screens — the robot pattern, test-tag conventions, and Robolectric caveats generalize.

---

## 1. Robot Pattern (mandatory for navigation and screen tests)

Every Compose UI test that exercises more than one screen interaction must use a **test robot**. The robot hides Compose semantics plumbing behind domain-language helpers.

### The rule

The test body must be readable in 5 seconds. If it isn't: extract helpers, use domain words, hide tags and semantics.

### Good

```kotlin
@Test
fun `search list scroll position survives tab switch`() {
    app.launchApp()
    app.openSearch()
    app.waitForFestivalList()
    app.scrollFestivalListTo(15)

    app.openHome()
    app.openSearch()

    app.assertFestivalNotVisibleInSearch("Festival 1")
}
```

### Bad

```kotlin
@Test
fun `search list scroll position survives tab switch`() {
    composeTestRule.setContent { VoyagerNavGraph() }
    composeTestRule.onNodeWithTag("nav_item_search").performClick()
    composeTestRule.waitForIdle()
    composeTestRule.waitUntil(timeoutMillis = 5_000) {
        composeTestRule.onAllNodesWithText("Festival", substring = true)
            .fetchSemanticsNodes().isNotEmpty()
    }
    composeTestRule.onNodeWithTag("festival_list").performScrollToIndex(15)
    composeTestRule.waitForIdle()
    composeTestRule.onNodeWithTag("nav_item_home").performClick()
    composeTestRule.waitForIdle()
    composeTestRule.onNodeWithTag("nav_item_search").performClick()
    composeTestRule.waitForIdle()
    val nodes = composeTestRule.onAllNodesWithText("Festival 1").fetchSemanticsNodes()
    assert(nodes.isEmpty()) { "..." }
}
```

### Robot structure

```kotlin
class AppNavTestRobot(private val rule: ComposeContentTestRule) {
    // Navigation
    fun launchApp() { ... }
    fun openHome() { ... }
    fun openSearch() { ... }
    fun openMap() { ... }
    fun pressBack() { ... }

    // Actions
    fun waitForFestivalList() { ... }
    fun scrollFestivalListTo(index: Int) { ... }
    fun tapFestivalInSearch(name: String) { ... }
    fun typeSearchQuery(query: String) { ... }

    // Assertions
    fun assertHomeVisible() { ... }
    fun assertSearchVisible() { ... }
    fun assertDetailVisible() { ... }
    fun assertFestivalNotVisibleInSearch(name: String) { ... }
}
```

### Naming conventions for robot methods

| Category | Pattern | Examples |
|----------|---------|----------|
| Navigation | `open<Tab>()`, `pressBack()` | `openSearch()`, `openHome()` |
| Actions | verb + domain noun | `scrollFestivalListTo(15)`, `tapFestivalInSearch("name")`, `typeSearchQuery("kirchweih")` |
| Waiting | `waitFor<Thing>()` | `waitForFestivalList()` |
| Assertions | `assert<Condition>()` | `assertSearchVisible()`, `assertHomeSelected()` |

### Robot placement

| Source set | Robot file | Rule type |
|-----------|-----------|-----------|
| `src/test/` (Robolectric) | `AppNavTestRobot.kt` accepting `ComposeContentTestRule` |
| `src/androidTest/` (instrumented) | `AppNavTestRobot.kt` accepting `AndroidComposeTestRule` |

Two copies are needed because the rule types differ. Keep the API surface identical.

---

## 2. Scoping Assertions to Retained Tabs

With retained tab composition, all three tabs are always composed. Assertions that search for text or nodes globally will find matches in hidden tabs.

### Rules

- When asserting festival content, scope to the active tab's test tag
- Use `hasAnyAncestor(hasTestTag("search_screen"))` or `hasAnyAncestor(hasTestTag("festival_list"))` to scope
- When tapping a festival card, scope to the active screen

### Good

```kotlin
fun tapFestivalInSearch(name: String) {
    rule.onNode(hasText(name) and hasAnyAncestor(hasTestTag("search_screen")))
        .performClick()
}

fun assertFestivalNotVisibleInSearch(name: String) {
    val nodes = rule.onAllNodesWithText(name)
        .filter(hasAnyAncestor(hasTestTag("festival_list")))
        .fetchSemanticsNodes()
    assert(nodes.isEmpty()) { "Expected '$name' scrolled off in search" }
}
```

### Bad

```kotlin
fun tapFestival(name: String) {
    rule.onNodeWithText(name).performClick()  // ambiguous with retained tabs
}
```

---

## 3. Test Tag Conventions

### Standard tags

| Element | Tag | Notes |
|---------|-----|-------|
| Home screen root | `home_screen` | On root modifier of HomeScreen |
| Search screen root | `search_screen` | On root modifier of SearchScreen |
| Map screen root | `map_screen` | On root modifier of MapScreen |
| Detail screen root | `detail_screen` | On root modifier of DetailScreen |
| Home nav item | `nav_item_home` | On NavigationBarItem |
| Search nav item | `nav_item_search` | On NavigationBarItem |
| Map nav item | `nav_item_map` | On NavigationBarItem |
| Festival list | `festival_list` | On LazyColumn in search |
| Home sections list | `home_sections_list` | On LazyColumn in home |
| Search input | `search_input` | On text field |
| Festival card | `festival_card_{id}` | On each card root |
| Location filter summary | `active_filter_summary` | On location summary row |
| Bottom nav bar | `bottom_nav` | On NavigationBar |

### Rules

- Tags are `snake_case`
- Every interactive element asserted in tests must have a tag
- Decorative elements do not need tags
- Parameterized tags use `_` separator: `festival_card_{id}`

---

## 4. Robolectric vs Instrumented Tests

### Use Robolectric (`src/test/`) when

- Testing navigation contracts (tab switching, back behavior, overlay push/pop)
- Testing scroll retention across tab switches
- Testing screen state rendering with prepared UiState
- Testing ViewModel-driven Compose screens with Koin test modules

### Use Instrumented (`src/androidTest/`) when

- Testing OsmDroid map rendering (needs real Android View)
- Testing ModalBottomSheet interactions (Robolectric doesn't render them)
- Testing gesture injection on overlay composables
- Testing real Koin AppModule wiring (AppModuleVerificationTest)
- Testing edge-to-edge insets and status bar behavior
- Testing content below the scroll fold that needs `performScrollTo()`

### Known Robolectric limitations

| Issue | Workaround |
|-------|-----------|
| **CMP resources crash** (`Res.string.*`, `Res.drawable.*`, `Res.font.*`) | **Compose UI tests that use CMP resources must be instrumented** (`androidTest/`), not Robolectric. This is a known CMP + Robolectric incompatibility. |
| `ModalBottomSheet` doesn't render | Keep sheet tests in `androidTest/` |
| Content below scroll fold invisible | Use `performScrollTo()` before assertions |
| Gesture injection fails for overlay composables | Keep overlay gesture tests in `androidTest/` |
| `@RunWith(Parameterized::class)` doesn't activate Robolectric | Use `AndroidJUnit4` instead |
| OsmDroid MapView doesn't render | Test map contracts through `MapInteractions` interface, not visual output |

### Robolectric scope after CMP migration

Robolectric is **no longer the main Compose UI test layer**. Since screens use CMP resources (`stringResource(Res.string.*)`, `painterResource(Res.drawable.*)`), they can only be tested on a real device/emulator.

**Use Robolectric only for:** Android adapters, permission wrappers, intent builders, and code that does NOT render CMP resources.

**Use instrumented tests for:** All Compose screen rendering, filter interactions, navigation, and anything that calls `stringResource(Res.string.*)`.

**Use JVM unit tests for:** Domain logic, ViewModel behavior, formatters, mappers — the bulk of confidence.

---

## 5. Koin Test Module Pattern

Navigation tests need a full Koin test module to resolve ViewModels. Use this pattern:

```kotlin
@Before
fun setUp() {
    startKoin {
        androidContext(ApplicationProvider.getApplicationContext<Application>())
        modules(testModule())
    }
}

@After
fun tearDown() {
    stopKoin()
}

private fun testModule() = module {
    single<FestivalRepository> { FakeFestivalRepository(TEST_FESTIVALS) }
    single<LocationFilterStore> { FakeLocationFilterStore() }
    single<FavouritesRepository> { FakeFavouritesRepository() }
    single<Clock> { fakeClock }
    // ... use cases, formatters, ViewModels
}
```

### Rules

- Use `single` for repositories/stores (shared state across ViewModels)
- Use `factory` for use cases and formatters (stateless)
- Use `viewModel` for ViewModels
- Test festival data should be a file-level constant, not class-level field
- The test module should be a `private fun testModule()` factory, not a field

---

## 6. Navigation Contract Tests

`NavigationContractTest.kt` in `androidTest/` verifies behavioral navigation rules that must survive across refactors. These are the most important UI tests.

### What to cover

- App starts on Home
- Tab switching (each tab)
- Back from non-Home → Home
- Back from Home → system exit
- State retention across tab switches (search query, scroll position)
- Overlay push and pop (Detail, LocationPicker)
- Overlay does not change selected tab

### Rules

- Use the robot pattern
- Test behavior, not implementation
- Do not assert on animation, transition direction, or timing
- Do not assert on internal navigation state (route strings, stack depth)

---

## 7. Scroll Retention Testing

### Search screen scroll behavior spec

- Scroll resets **only** when result IDs change (ordered card IDs differ)
- Scroll is preserved when filter inputs change but results stay the same
- Text query change always resets (treated as new search)

### Testing scroll retention

Test the key derivation logic as a pure unit test:

```kotlin
@Test
fun `same cards in same order produce same result key`() {
    val key1 = cards.joinToString(",") { it.id }
    val key2 = cards.joinToString(",") { it.id }
    assertEquals(key1, key2)
}

@Test
fun `reordered cards produce different result key`() {
    val key1 = cards.joinToString(",") { it.id }
    val key2 = cards.reversed().joinToString(",") { it.id }
    assertNotEquals(key1, key2)
}
```

Test scroll position via robot in navigation tests:

```kotlin
@Test
fun `search list scroll position survives tab switch`() {
    app.launchApp()
    app.openSearch()
    app.waitForFestivalList()
    app.scrollFestivalListTo(15)

    app.openHome()
    app.openSearch()

    app.assertFestivalNotVisibleInSearch("Festival 1")
}
```

---

## 8. Screen State Testing (Compose)

### Preferred pattern

Test content composables directly with prepared state via `mutableStateOf`:

```kotlin
var state by mutableStateOf(initialScreenState())

composeTestRule.setContent {
    FestivalSearchScreen(screenState = state, actions = noOpActions())
}

// Act: change state
state = state.copy(cards = reorderedCards)
composeTestRule.waitForIdle()

// Assert
composeTestRule.onNodeWithText("Festival 20").assertIsDisplayed()
```

### Rules

- Never call `setContent` twice in one test — use `mutableStateOf` to drive state changes
- Use `noOpActions()` factory for tests that don't care about callbacks
- Use `waitForIdle()` after state changes
- Use `waitUntil(timeoutMillis)` for async data loading, never `Thread.sleep`
