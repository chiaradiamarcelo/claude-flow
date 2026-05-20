---
name: ui-testing
description: Use whenever writing, modifying, or reviewing UI tests in React projects. Defines naming, structure, query priority, render conventions, and mocking patterns for component and hook tests. Framework-agnostic on the component library; assumes React + Testing Library + a modern test runner (Vitest or Jest). Inherits the high-level principles from [[testing]].
allowed-tools: Read, Write, Edit, Glob, Grep, Bash
---

## Scope

React component tests (`*.test.tsx` / `*.test.jsx`) and React hook tests (`*.test.ts`). For pure-function and domain tests follow [[testing]] — but the high-level principles in this skill (naming, structure, data minimality, one-behavior-per-test, behavior-over-implementation, delete-vacuous-tests) are pulled directly from [[testing]] and stay in force here too.

## Global test setup

Most React projects centralize global mocks in a test setup file (e.g. `vitest.config.ts`'s `setupFiles`, `jest.config.js`'s `setupFilesAfterEach`, or a `defaultMocks.ts`). **Always read that file first** when starting on a test suite — what's already mocked globally doesn't need explicit local mocking unless you need to assert on calls (a global `vi.fn()` returns a fresh function per render and is unassertable; override locally when you need to spy).

## File naming

- Component tests: `<Component>.test.tsx`, co-located with the component.
- Hook tests: `<useHook>.test.ts`, co-located with the hook.
- One test file per source file. Don't create siblings for helpers — test through the consuming component, or extract the helper to its own module if it's important enough to test directly.

## Test name pattern

Natural-language sentence in **present simple, third-person**, describing the observable behavior. No leading "Should". snake_case and camelCase are not allowed.

```ts
// Good — present simple, plain language, behavior-focused
it('hides the dismiss button when status is healthy', ...);
it('fires the viewed event once on mount', ...);
it('navigates to the diagnostics route when the CTA is clicked', ...);

// Bad — leading "Should"
it('Should hide the dismiss button when status is healthy', ...);

// Bad — snake_case or camelCase
it('hides_dismiss_when_healthy', ...);
it('hidesDismissWhenHealthy', ...);
```

Use plain English a product person would say. Prefer `does not render …`, `calls …`, `shows …`, `hides …` over invented jargon. For failure paths, prefer `fails when <condition>` over `throws when <condition>`. Avoid implementation details in the name.

## Test structure (Given / When / Then)

Every test follows **Given / When / Then**. Three phases → **two** blank lines (Given→When, When→Then). Statements within the same phase stay grouped — no blank lines inside Given even when it has multiple lines (mock setup + render together). **No `// Given` / `// When` / `// Then` comments.**

```tsx
// Good — render is part of the setup (Given); one blank line between phases
it('calls onDismiss when the Dismiss button is clicked', async () => {
  const onDismiss = vi.fn();
  const user = userEvent.setup();
  renderBanner({ status: 'critical' }, { onDismiss });

  await user.click(screen.getByRole('button', { name: /Dismiss/i }));

  expect(onDismiss).toHaveBeenCalledTimes(1);
});
```

**Rendering belongs to Given.** The `render(...)` call establishes the state the test acts on — it's part of the setup, not a phase of its own. Given ends when the action under test begins.

**Traceability**: every value the When or Then references must be explicit in the Given. Don't rely on factory defaults to seed values the test asserts on. If a value matters to the assertion, pass it explicitly via the render/setup helper.

## Test data minimality

- Seed only what the assertion needs. Drop props, response fields, or fixture rows that don't affect the outcome.
- When a behavior can be proven with one trigger / one row, don't pile on extras.
- Prefer **semantic shared constants** for recurring values (e.g. `CRITICAL_RESPONSE`, `DEFAULT_USER`) over ad-hoc literals.

## Test data visibility

All test data referenced in assertions must be visible in the test body. Module-scope or `describe`-scope fixtures that build implicit test data violate this — the reader should not have to scroll to outer scopes to understand what is being asserted. Pass data explicitly through the render helper, or use named constants whose meaning is obvious from the name alone.

## One behavior per test

Each `it(...)` verifies a **single observable behavior**. If the name needs "and", split.

- Watch the **rendered tree**, not just the assertions. A test named "renders the dismiss button" with a fixture that also exercises other variants is doing work for several rules at once. Reduce the seed to the minimum that proves the named rule.
- Two `expect` calls that prove **different rules** is the smell. Two `expect` calls that prove **different facets of the same outcome** (e.g. payload shape + call count) are fine.
- **No duplicate test cases.** Two `it(...)` blocks that exercise the same behavior with the same setup (even if worded slightly differently) are pure noise — keep one, delete the rest.

## Rendering: centralize provider setup

Use a single render helper (`renderWithProviders`, `customRender`, etc.) that wires up routing, state management, theming, and i18n. Components under test should NOT see raw `render()` from `@testing-library/react` — that bypasses real providers and drifts from production behavior.

```tsx
// Good
renderWithProviders(<MyComponent />);

// Bad — duplicated provider setup in every test
render(
  <Provider store={...}>
    <Router>
      <ThemeProvider><MyComponent /></ThemeProvider>
    </Router>
  </Provider>
);
```

For hooks, use `renderHook` from `@testing-library/react`.

### Custom state for state-managed apps

When a test needs the state container in a specific shape (e.g. asserting conditional rendering based on user properties), build a custom test store and pass it to the render helper. Wrap dispatches in `act()` so React commits the state before assertions run.

```ts
import { act } from '@testing-library/react';

const store = createTestStore({ user: userReducer });

it('shows the banner for new users', () => {
  act(() => {
    store.dispatch(userPatch({ signupDate: new Date('2026-01-19') }));
  });
  renderWithProviders(<MyComponent />, store);

  expect(screen.getByText('Banner text')).toBeTruthy();
});
```

(`createTestStore` / `userReducer` are placeholders — substitute your project's own store helpers.)

## Repeated construction → extract a helper

When the same render shape appears in 3+ tests, extract a `renderXxx(...)` helper that absorbs the incidental boilerplate. Tests then specify only what matters for their scenario. When the shape gains a new field, update the helper — never patch every call site.

## `beforeEach` discipline

- **Stateless dependencies** (mock factories, navigation mocks, analytics spies) used identically across the suite: declare at `describe` scope, assign in `beforeEach`.
- **Mock state resets** (`vi.clearAllMocks()` / `jest.clearAllMocks()`, `localStorage.clear()`, `vi.useRealTimers()`): live in `beforeEach`.
- **Never seed test data in `beforeEach`.** Data setup belongs in the `it(...)` body so tests stay readable and self-contained.

## Query priority

Per [Testing Library official guidance](https://testing-library.com/docs/queries/about/#priority):

1. `getByRole(role, { name })` — accessible.
2. `getByLabelText` — form fields with labels.
3. `getByPlaceholderText` — fallback.
4. `getByText` — non-interactive content.
5. `getByDisplayValue` — form fields with current value.
6. `getByAltText` / `getByTitle` — last resort for media / hovers.
7. `getByTestId` — escape hatch only. Treat as a smell — usually means the markup should expose a role.

Use `query*` for negative assertions (returns `null` instead of throwing).

## Matchers for text content (the nesting rule)

How `getByText` resolves depends on how your UI library nests text nodes:

- **Flat content**: `<span>Some message</span>` — one element, one text node. `screen.getByText('Some message')` works.
- **Nested content**: `<span>Hello <strong>world</strong></span>` — the parent's `textContent` is `'Hello world'`, but it has element children. Testing Library matches the parent by default; if multiple descendants have the same `textContent` you get ambiguity.

When nesting introduces ambiguity that can't be solved with `getByRole` or `within(container)`, use a scoped predicate:

```ts
screen.getByText((_, el) =>
  el?.tagName === 'SPAN' && el?.textContent === 'Hello world'
);
```

**Default to the plain string form.** Reach for the predicate only when there is real ambiguity. The predicate is brittle and harder to read; using it preventively is over-defensive.

## Interactions: userEvent over fireEvent

- `userEvent.setup()` once per test, then `await user.click(...)`, `await user.type(...)`.
- Use `fireEvent` only for synthetic events `userEvent` doesn't model (resize, scroll, custom events).

## Mocking modules

In Vitest, `vi.mock` is hoisted to the top of the file. Mock factories that reference local symbols must use `vi.hoisted`:

```ts
const mockFn = vi.hoisted(() => vi.fn());

vi.mock('./module', () => ({ exportedFn: mockFn }));
```

To partially mock (preserve other exports), use `vi.importActual`:

```ts
vi.mock('./module', async () => {
  const actual = await vi.importActual<typeof import('./module')>('./module');
  return { ...actual, exportedFn: mockFn };
});
```

In Jest, equivalent patterns: top-level `jest.mock(...)` + `jest.requireActual(...)`.

## Mocking `useNavigate` (react-router-dom)

```ts
const mockNavigate = vi.hoisted(() => vi.fn());

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual<typeof import('react-router-dom')>('react-router-dom');
  return { ...actual, useNavigate: () => mockNavigate };
});
```

## What to assert

**Behavioral, user-observable outcomes only.**

- ✅ A button appears / disappears.
- ✅ A handler was called with specific arguments.
- ✅ Navigation happened to a specific URL.
- ✅ An analytics event fired with the expected payload.
- ❌ Internal state value.
- ❌ Function reference stability across re-renders (no user-observable consequence — **vacuous test**).
- ❌ Implementation details of storage (`localStorage.getItem(...)`) when a behavioral equivalent exists ("the banner stays hidden after remount").

### `expect.arrayContaining` is subset matching, not equality

It passes when the array contains *at least* the listed items — extras slip through. For "exactly these in any order", pair with `toHaveLength(N)` or sort both sides and use `toEqual([...])`.

## Test behavior, not library boundaries

- When a UI library implements your product behavior, the behavior is still yours to test. The library is an implementation detail, not an excuse to skip testing.
- If a behavior is hard to test, **restructure the code for testability first**. Most "untestable" behaviors are a design signal — extract a presentational component, pull state up, separate effects.
- **Delete vacuous tests.** A test that passes regardless of whether the code is correct is worse than no test. If removing the implementation doesn't make the test fail, the test isn't proving anything.

## Forbidden patterns

- Control flow in test bodies (`if`, `for`, `while`, `switch`, `try`). Tests stay declarative and linear.
- Vacuous tests that produce no failure mode.
- Asserting on implementation details when a behavioral equivalent exists.
- Multiple unrelated behaviors per `it(...)`.
- Re-implementing the system under test in the test setup (computing the expected with the same algorithm).
- Manual provider setup when a centralized helper exists.
- Module-scope mutable state that bleeds between tests.

## Cleanup

- `vi.clearAllMocks()` / `jest.clearAllMocks()` in `beforeEach` for any test asserting on mocks.
- `localStorage.clear()` / `sessionStorage.clear()` for storage tests.
- `vi.useRealTimers()` / `jest.useRealTimers()` in `afterEach` for tests that fake time.

## Strategy and efficiency

Prefer fast, deterministic tests. Layer the coverage:

- **Presentational components**: cover the rendering rules (one test per visible branch).
- **Container components**: cover integration with hooks, navigation, analytics.
- **Hooks**: assert on the public surface (return values, observable callbacks). Don't reach into closure internals.
- Prefer the highest level that exercises the behavior. Add lower-level tests only for branches that would be combinatorially expensive at the higher level.
