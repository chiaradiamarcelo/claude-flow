## Extract named conditions

### Smell
A boolean expression appears inline in an `if` statement or ternary. The expression uses
low-level checks (`typeof`, `in`, `===`, `instanceof`) whose combined intent is not obvious
without reading every operand. Readers must reverse-engineer what the condition *means* from
how it is *computed*.

### Trigger
An `if` condition spans multiple lines, combines 2+ operators, or requires a comment to
explain its purpose. Or the same compound check appears in more than one place.

### Refactoring
1. Extract the condition into a named function or variable whose name states the business
   or structural intent (e.g., `hasNumericSchemaVersion`, `isExpired`, `isEligibleForDiscount`).
2. Use a type-narrowing return type when the language supports it (TypeScript `is`, Kotlin
   smart cast) so subsequent code benefits from the narrowed type.
3. Replace the inline expression with a call to the named function.
4. If the condition is used once and is short, a `const` with a descriptive name is sufficient;
   a function is preferred when type narrowing is needed or when reuse is likely.

### Structure after refactoring
- Each `if` reads as a domain/structural assertion: `if (!isPlainObject(parsed))`.
- Named predicates live as private helpers near the function that uses them.
- Type guards carry narrowing information so callers don't need follow-up casts.

### Tests
- Pure refactor — existing tests stay green.
- If the extracted predicate is non-trivial, consider a focused unit test.

### Example
**Diagnostics report schema versioning (TypeScript)**
```typescript
// Before
if (!('schemaVersion' in record) || typeof record.schemaVersion !== 'number') { ... }

// After
function hasNumericSchemaVersion(
  record: Record<string, unknown>,
): record is Record<string, unknown> & { schemaVersion: number } {
  return 'schemaVersion' in record && typeof record.schemaVersion === 'number';
}
if (!hasNumericSchemaVersion(parsed)) { ... }
```
The `if` now reads as a structural assertion. The type narrowing flows into subsequent code.
