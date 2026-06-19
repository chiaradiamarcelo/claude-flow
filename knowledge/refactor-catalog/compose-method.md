## Compose method

### Smell
A function is long and mixes multiple levels of abstraction: low-level mechanics (parsing,
casting, null-checking) alongside high-level decisions (dispatching on a version, selecting
a strategy). The reader must constantly shift mental gears between *what* the function does
and *how* it does each step. The function is hard to scan because the outline (the sequence
of steps) is buried in implementation details.

### Trigger
A function exceeds ~15 lines, or you can identify 2+ distinct "phases" within it (validate,
transform, dispatch) that each involve their own low-level logic.

### Refactoring
1. Identify the high-level steps the function performs (e.g., parse → validate → dispatch).
2. Extract each step into a named private function whose name describes *what* it does, not
   *how*: `extractV1UserAgents(record)`, `assertWellFormed(condition)`.
3. The composed function becomes a short sequence of calls at a single level of abstraction —
   a table of contents for the algorithm.
4. Each extracted function owns one concern and can be understood independently.
5. Keep extracted helpers private/local unless reuse is proven.

### Structure after refactoring
- The public function reads like pseudocode: 5–10 lines, each a named step.
- Private helpers contain the mechanical details (type checks, casts, error construction).
- Each helper has a clear input → output contract.

### Tests
- No behavioral change — existing tests stay green.
- Helpers are tested indirectly through the composed function; extract a dedicated test only
  when a helper has complex branching worth pinning independently.

### Example
**Diagnostics report schema versioning (TypeScript)**
`parseDiagnosticsReportEnvelope` was refactored from a single function with inline validation
and extraction into a composed method:
```typescript
export function parseDiagnosticsReportEnvelope(json: string): UserAgentChecks {
  const parsed: unknown = JSON.parse(json);
  if (!isPlainObject(parsed))            throw new Error(MALFORMED);
  if (!hasNumericSchemaVersion(parsed))   throw new Error(MALFORMED);
  if (isCurrentSchemaVersion(parsed))     return extractV1UserAgents(parsed);
  throw new UnsupportedSchemaVersionError(parsed.schemaVersion);
}
```
Each helper (`isPlainObject`, `hasNumericSchemaVersion`, `isCurrentSchemaVersion`,
`extractV1UserAgents`) owns a single concern. The main function is a readable checklist.
