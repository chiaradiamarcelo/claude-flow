## Formatting logic in domain entities

### Smell
A domain entity contains methods that format data for display (e.g., `displayLabel()`,
`formattedAddress()`, `shareText()`). These methods assemble human-readable strings using
domain fields but serve no domain invariant or business rule. They couple the domain to
presentation concerns — locale, label conventions, abbreviation rules — that change for
UI reasons, not business reasons.

### Trigger
A second display context appears (e.g., a share sheet alongside a detail screen) that needs
a different format from the same entity. The entity accumulates formatting variants, or the
same conditional logic (e.g., which address field to prefer) appears in multiple methods.

### Refactoring
1. Identify methods on domain entities that produce display strings (not enforce invariants).
2. Create a `*TextFormatter` object or class in the presentation layer.
3. Move the formatting methods to the formatter as static/companion functions that take the
   entity as a parameter: `OrderTextFormatter.summaryLine(order)`.
4. Extract shared derivation logic as a private helper inside the formatter.
5. Update all call sites in presentation/ViewModel code.
6. Move tests from the domain test directory to a presentation test directory.

### Structure after refactoring
- Domain entity: only invariant enforcement, domain queries, and equality. Zero string
  formatting.
- `*TextFormatter` in presentation: owns all display-string assembly. One place to change
  when label conventions evolve.
- Dependency direction preserved: formatter depends on domain, not the reverse.

### Tests
- Formatter tests live in the presentation test directory, exercising each formatting method
  with boundary inputs (missing optional fields, equal fields, differing fields, etc.).
- Domain entity tests only cover invariants and domain behavior.
- All existing assertions are preserved — only the call site changes.

### Example
**E-commerce order system**
`Order.summaryLine()`, `Order.shippingLabel()`, and `Order.receiptText()` were display-string
methods on the domain entity. Moved to `OrderTextFormatter` in the presentation layer. The
`recipientName()` helper became a private function in the formatter. Domain `Order` retained
only `total()`, `isShippable()`, and invariant enforcement.
