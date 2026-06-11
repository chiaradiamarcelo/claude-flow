# Finding 04 — Writing robust agent evals

**Date:** 2026-06 · **Area:** `evals/` fixture & grader design
**Status:** distilled conventions (from building the 29-fixture test-reviewer corpus)

Practices that emerged from making non-deterministic agents testable. Each one
traces to a concrete failure we hit.

## 1. Dispatch in a fresh `claude -p --agent`, never the in-session Agent tool

**Change:** evals call `claude -p --agent <reviewer>` as a fresh process.
**Why:** the in-session `Agent` tool runs a **cached agent definition** — editing
`Agent.md` and re-running it tests the *old* prompt. A fresh `claude -p` picks up
the edited definition. This silently wasted effort until caught (the agent kept
emitting a marker we'd already deleted).

## 2. Assert tolerant facts, never exact prose

**Change:** `expected.json` asserts only coarse, non-determinism-safe properties:
`expectedStatus`, count/severity **ranges**, and `mustMention` substrings.
**Why:** the agent is a non-deterministic function; its wording varies run to
run. Comparing prose would flake constantly. Extract a structured verdict and
assert stable facts.

## 3. Don't over-constrain severity

**Change:** for fuzzy/stylistic rules, assert `FAIL` + a `mustMention` keyword and
**no severity floor/cap**.
**Why (cost: a flaky fixture):** a `magic-numbers` fixture pinned `WARNING: max 0`.
A thorough reviewer legitimately found an extra WARNING (an oversized fixture) on
top of the intended SUGGESTION → false failure. A thorough non-deterministic
reviewer can almost always find *one more* defensible thing; capping it is
fragile. Pin the **intent** (`VIOLATION max 0` + `SUGGESTION min 1` +
`mustMention`), not the absence of everything else.

## 4. `mustMention` is a case-insensitive **substring** — pick robust roots

**Change:** choose keyword roots, not whole words.
**Why (cost: a false failure):** `class-field-test-data` asserted `mustMention:
"visible"`, but the reviewer wrote **"visibility"** — and `"visible"` is *not* a
substring of `"visibility"`. The reviewer was correct; the fixture was wrong.
Use the shared root: `"visib"`. Other examples:
- `"symmetric"` matches both *symmetric* and *a**symmetric*** — handy.
- Avoid 2–3 letter keywords (`"if"` matches *speci**fi**c*); they pass vacuously.
- When phrasing is unpredictable, prefer asserting on a token the reviewer must
  quote from the code (a method name, `getByTestId`, `Thread.sleep`) over a
  word it might paraphrase.

## 5. One rule per fixture, otherwise clean

**Change:** each fixture is a minimal test that breaks exactly **one** rule,
otherwise idiomatic.
**Why:** isolates the signal. If a single-violation fixture goes red, you know
*which* rule regressed. (A thorough reviewer will still add incidental
warnings — e.g. ZOMBIES coverage gaps on a one-test fixture — which is why we
assert `mustMention` for the target rule rather than an exact issue count.)

## 6. The corpus tests "does it catch the rule," not "does it need the skill"

**Observation:** the `test-reviewer` scored 29/29 even when its skill failed to
load via the `Skill` tool (it fell back to reading the file, and the model knows
test hygiene well + the body has a category checklist). **Implication:** a green
corpus proves the agent *catches* each rule; it does **not** prove the rule is
*only* catchable because of the skill. If you want to test the skill's marginal
value, you'd need fixtures encoding *project-specific* rules the base model
wouldn't know. Useful to remember before concluding "the skill is doing the work."

## 7. Quarantine is for flaky **agents**, not flaky **graders**

**Change:** `check_routing.py` supports `"quarantine": true` (reports `QUAR`,
non-gating) for genuinely flaky pairs (`pass@k` territory).
**Why / caution:** we quarantined a routing fixture believing the *model* was
flaky. It wasn't — the **grader** had a bug (see finding 01). **Before reaching
for quarantine, confirm the flake is the agent**: reproduce the raw output and
run the grader on it by hand. Quarantining a grader bug hides it.

## 8. Test the grader itself

**Change:** sanity-check `check_routing.py` / `eval_grade.py` on known-good and
known-bad inputs.
**Why:** "deterministic / model-free" does not mean "correct." Finding 01 was a
grader bug that survived precisely because we trusted the grader and only
eyeballed the agent's raw output.
