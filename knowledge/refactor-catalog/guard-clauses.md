## Guard clauses

### Smell
A function uses nested `if/else` blocks or assigns to a local variable through conditional
branches before reaching the "real work." The happy path is buried inside indentation, and
the reader must mentally track which conditions lead to which outcomes. Error/edge-case
handling is interleaved with the main logic instead of being dispatched up front.

### Trigger
A function has 2+ levels of nesting for validation or precondition checks, or the main
logic is inside an `if` block whose `else` is an error/throw.

### Refactoring
1. Identify each precondition or invalid-state check in the function.
2. Invert the condition and return/throw immediately (early exit).
3. Remove the `else` branch — the rest of the function *is* the happy path.
4. The function now reads top-down: guards first, then linear main logic at the base
   indentation level.

### Structure after refactoring
- Each guard clause is a one-liner `if (!condition) throw/return`.
- Guards appear at the top of the function in order of cheapest-to-check first.
- The main logic follows at the same indentation level — no nesting.

### Tests
- No behavioral change — tests remain green throughout.
- Each guard maps to a test that triggers that specific early exit.

### Example
**Diagnostics report schema versioning (TypeScript)**
`parseDiagnosticsReportEnvelope` originally used nested `if/else` blocks to validate the
parsed JSON. Refactored to sequential guard clauses:
```typescript
if (!isPlainObject(parsed))           throw new Error(MALFORMED);
if (!hasNumericSchemaVersion(parsed))  throw new Error(MALFORMED);
if (isCurrentSchemaVersion(parsed))    return extractV1UserAgents(parsed);
throw new UnsupportedSchemaVersionError(parsed.schemaVersion);
```
Each line is a self-contained decision. The function reads as a checklist.
