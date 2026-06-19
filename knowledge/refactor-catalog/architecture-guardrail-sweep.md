## Architecture guardrail sweep

### Smell
Code passes functional tests but the architecture starts drifting: layer boundaries blur, validation
is duplicated across adapters and core, acceptance tests stop running in CI, and business policy is
hard-coded in use cases.

### Trigger
A review finds that behavior is correct today, but extension risk rises because the next rule change
would require touching multiple layers or changing core code for policy-only updates.

### Refactoring
1. Run a focused review pass with these rules:
   - layer dependency boundaries (no inward leaks from adapters/frameworks)
   - validation ownership and consistency (single authoritative boundary per invariant)
   - test lifecycle coverage (unit + integration + acceptance wired intentionally)
   - policy configurability (hard-coded thresholds/tiers extracted behind config/policy objects)
2. Classify findings by severity (`VIOLATIONS`, `WARNINGS`, `GOOD PRACTICES`) to prioritize work.
3. Refactor only the highest-impact guardrail breaks first, preserving behavior with regression
   tests.
4. Encode recurring findings in catalog entries so future reviews are faster and consistent.

### Structure after refactoring
- Clear adapter/application/domain boundaries with explicit dependency direction.
- Invariants enforced once at a deliberate boundary, with adapters mapping errors consistently.
- CI lifecycle intentionally includes the chosen test layers.
- Business policy represented as configurable input or dedicated policy abstraction.

### Tests
- Keep use case tests for rule behavior.
- Keep controller tests for API contract and validation mapping.
- Ensure acceptance tests are either wired in CI or explicitly documented as manual.
- Add regression tests when moving validation/policy ownership to prevent behavioral drift.

### Example
**Hotel Room Allocation API**
- Validation overlap found between controller input validation and domain constructor.
- Acceptance test exists but is excluded from CI lifecycle.
- Premium threshold is hard-coded in use case instead of being configurable.
