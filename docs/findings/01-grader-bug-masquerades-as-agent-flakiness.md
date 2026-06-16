# Finding 01 — A deterministic grader bug masqueraded as agent flakiness

**Date:** 2026-06 · **Area:** `evals/check_routing.py`, `commands/run-reviewers.md`
**Status:** fixed (commit `97767d6`)

## TL;DR

The `/run-reviewers` routing test looked **~50% flaky** on the "docs-only
changeset → nobody fires" case. We blamed the model ("it routes by topic"),
quarantined the fixture, and even built a deterministic router script to "fix"
it. The real cause was a **one-character regex bug in the grader**. The model
was correct the whole time.

## The change (what we were testing)

A live behavioral test of the `run-reviewers` command: spin up a scratch repo
with a docs-only changeset (`README.md`, `docs/*.md`), run
`claude -p "/run-reviewers --dry-run"`, and assert via `check_routing.py` that
**no** reviewer fires (every reviewer's trigger globs are positive; docs match
none).

## The symptom

- Positive fixtures (a reviewer *does* fire) were always green.
- The universal-negative ("nobody fires") failed ~half the runs through
  `run_all.sh`, but passed every time I ran the same command by hand.
- The reported "fired" set was **always identical**:
  `{arch-reviewer, refactor-advisor, test-reviewer, ui-test-reviewer}` — api
  excluded. *Suspiciously deterministic for "flakiness."*

## What it cost us (before the real diagnosis)

- Tightened `run-reviewers.md` Step 4 to "match by glob only, never by topic"
  (helped nothing — the model wasn't the problem).
- Added a `quarantine` flag and quarantined the fixture (non-gating).
- Built `scripts/route-reviewers.py`, a deterministic router, and rewired the
  command to call it — then reverted it when the user asked to retest.
- Many `claude -p` runs chasing a "model non-determinism" ghost.

## Why — the actual mechanism

`fired_set()` parsed the command's `fires:` line with:

```python
re.search(r"(?im)^\s*fires:\s*(.*)$", output)
```

`\s` **includes `\n`**. The command's output for a no-match changeset is:

```
ROUTING
fires:
skips: api-reviewer, arch-reviewer, refactor-advisor, test-reviewer, ui-test-reviewer
```

On the **empty** `fires:` line, `\s*` after the colon swallowed the newline and
`(.*)` captured the **next line** — the `skips:` list. So the grader reported
the *skipped* reviewers as *fired*. A `_NAME` filter I'd added as "hardening"
then dropped the leading `skips: api-reviewer` token (it has a colon/space),
leaving the clean-looking `{arch, refactor, test, ui}` — which is why it read
like a real, deterministic over-fire.

It only ever bit the **empty-`fires:`** case (the universal-negative); non-empty
fires lines have content before the newline, so `(.*)` stops there.

## The fix

```python
re.search(r"(?im)^[ \t]*fires:[ \t]*(.*)$", output)   # [ \t] can't cross \n
```

Verified: empty `fires:` → `[]` (PASS); a genuine over-fire still fails.

## Effect (after fix)

- Routing suite: **3/3 stable** across repeated runs (was ~50% on the negative).
- Un-quarantined the fixture. Deleted the router-script detour.

## Lessons

1. **An always-identical "flaky" failure is the signature of a deterministic
   bug, not sampling.** Sampling noise varies; a fixed wrong answer doesn't.
2. **Reproduce the raw output and hand-parse it before blaming the model.** Every
   raw dump I looked at showed the *correct* empty-`fires:` line — I just never
   ran the grader on it in isolation. One `check_routing.py <expected> <raw>`
   would have caught it on day one.
3. **A deterministic grader can still be buggy.** "Model-free" ≠ "correct." Test
   the grader on known-good and known-bad inputs.
4. **"Hardening" can mask the underlying bug.** The `_NAME` filter made the
   smoking-gun (`skips:` token) disappear, turning an obvious parse error into a
   plausible-looking model behavior.
5. `\s` in a line-oriented regex is a trap — prefer `[ \t]` when you mean
   "spaces, not newlines."
