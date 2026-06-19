## Duplicated sealed-class dispatch composable

### Smell
A `when` block that dispatches on a sealed class/interface is copy-pasted across multiple
composable functions. Each copy renders the same variants with the same parameters (image URL,
placeholder resource, content scale, error drawable) but in a slightly different modifier
context. Adding a new variant or changing shared behavior (e.g., adding a `placeholder`
parameter to `AsyncImage`) requires identical edits in every copy.

### Trigger
The same sealed-class `when` dispatch appears in 3+ composable files, or a change to one
variant (e.g., adding an error-placeholder to `Remote`) must be replicated across all copies.

### Refactoring
1. Extract a shared `@Composable` function that takes the sealed type and a `Modifier`,
   dispatches via `when`, and renders each variant.
2. The shared composable owns all variant-specific details (placeholder drawable, content
   description, content scale default).
3. Replace every inline `when` block with a call to the shared composable, passing only the
   sealed value and the caller-specific modifier.
4. If a caller needs a non-default `contentScale`, expose it as an optional parameter with a
   sensible default.

### Structure after refactoring
- One `FestivalImageView(source: FestivalImageSource, modifier, contentScale)` composable in
  `presentation/common/`.
- Callers pass `source` + `modifier` only.
- Adding a new `FestivalImageSource` variant compiles-fails in one place, not N.

### Tests
- Existing Compose UI tests continue to pass unchanged (the extraction is a pure refactor).
- No new unit tests needed — the shared composable is a thin rendering wrapper, tested
  transitively by each screen's UI tests.

### Example
**WaWo Android app**
`when (imageSource) { Remote -> AsyncImage(...); Placeholder -> Image(...) }` was duplicated
in `FestivalSearchCard`, `FestivalDetailHeroSection`, `FestivalMapInfoSheet`, and
`HomeScreen`. Extracted to `FestivalImageView` in `presentation/common/`. All four callers
now delegate to the shared composable. Adding `placeholder = painterResource(...)` to the
`Remote` branch required changing one file instead of four.
