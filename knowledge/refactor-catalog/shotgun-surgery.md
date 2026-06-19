## Shotgun surgery

### Smell
A change to one concept (adding a parameter, renaming a field, changing a type) requires
identical edits in many files. The knowledge of how to construct or configure that concept is
spread across every call site instead of living in one place.

Common forms:
- The same constructor call (with the same arguments) is copy-pasted across 5+ test methods or
  multiple test files.
- A data class gains a field and dozens of call sites need updating.
- A factory or formatter is instantiated inline in every ViewModel test with identical config.

### Trigger
A signature change touches 3+ files with identical edits, or you find yourself doing
find-and-replace across test files to add the same parameter everywhere.

### Refactoring
1. **Before the feature change**, scan call sites for the constructor/method being modified.
2. If 3+ sites use identical construction, extract a shared helper first:
   - Test fixtures: `aFestival(...)`, `testCardFormatter()`, `successState()`
   - Test render helpers: `renderDetailScreen(uiState = ...)`
   - Production factories: Koin module, companion factory method
3. Verify all tests still pass (the extraction is a pure refactor — no behavior change).
4. **Then** make the actual feature change — it lands in one place (the helper), not N call sites.

"Make the change easy (this might be hard), then make the easy change." — Kent Beck

### Structure after refactoring
- One shared helper/fixture per repeated construction pattern.
- Call sites specify only what differs from defaults.
- Adding a new parameter to the underlying constructor requires editing one helper, not N files.

### Tests
- The extraction step is green-to-green: all existing tests pass before and after.
- The feature change modifies only the helper — existing tests continue to pass or fail based
  on their own assertions, not on incidental constructor noise.

### Example
**WaWo Android app**
`FestivalCardFormatter(untilTemplate = "Bis %s", endsTodayLabel = "Endet heute")` was
constructed identically in 6 ViewModel test files. Adding `festivalImage` required touching
all 6. Extracted `testCardFormatter()` fixture — the `festivalImage` parameter change became
a one-liner.
