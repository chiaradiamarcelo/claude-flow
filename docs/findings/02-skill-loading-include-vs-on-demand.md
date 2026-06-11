# Finding 02 — Skill loading: always-on `@`-include vs on-demand `Skill` tool

**Date:** 2026-06 · **Area:** `agents/test-reviewer/Agent.md`, skill loading
**Status:** experiment run, **rejected** (kept the `@`-include baseline)

## The change

Baseline: the reviewer loads its rulebook with an **auto-expand include** in the
body —

```markdown
## Test rules (source of truth)
@skills/testing/SKILL.md
```

Experiment (the agentic-dev-team style): make the dependency **declarative** and
load it **on demand** —

```yaml
tools: Read, Glob, Grep, Skill
skills: [testing]
```
```markdown
Before reviewing, load the test rules by invoking the `testing` skill … do not
review from memory.
```

We measured both against the exhaustive 29-fixture `test-reviewer` corpus.

## Effect — performance & cost

| Metric | Baseline (`@`-include) | Experiment (`skills:` + `Skill`) |
|---|---|---|
| Cost / dispatch | **$0.060** | **$0.108** (measured $0.115 / $0.096 / $0.112) |
| Inference turns | 1 | 2+ (Skill attempt → fallback → verdict) |
| Skill in cached prompt prefix? | ✅ (`cache_read` ~22k @ $0.30/M) | ❌ loads mid-conversation (`cache_read` 31k–50k) |
| Output tokens / dispatch | ~1,200 | ~2,000–2,500 |
| Full 29-fixture corpus | **~$1.7** | **~$3.1** |
| Wall-clock (corpus) | ~12 min | ~20+ min |
| Quality | 29/29 | 29/29 |

**~1.8× the cost and ~1.7× the latency for zero quality gain.**

## Why — the mechanism

The `stream-json` trace showed every experimental dispatch doing:

```
tools=['Skill','Glob','Read','Glob','Glob','Read']   denials=1
```

1. The agent calls `Skill(testing)` → **DENIED** (the eval harness dispatches
   with `--allowedTools Read Glob Grep`; it never granted `Skill`). A wasted turn.
2. It self-heals: `Glob` + `Read` to *find and read* `skills/testing/SKILL.md`
   by hand.
3. The skill therefore enters context as a **mid-conversation tool result —
   outside the cacheable prompt prefix** — and the whole context gets a second
   inference pass.

Even with `Skill` *granted* (a separate probe), it was still ~$0.11: the extra
turn and the non-cached skill load are **structural**, not just the denial.

The `@`-include wins because the skill sits in the **cached prompt prefix**
(cheap `cache_read` at $0.30/M) and there is **one turn, no search**.

## Two findings beyond cost

- **Quality held at 29/29 even when `Skill` was denied** — because the agent was
  resourceful (Glob+Read'd the file) *and* the body checklist plus the model's
  own test-hygiene knowledge are strong. So the corpus tests "does it catch the
  rule," not "does it strictly need the skill." (See finding 04.)
- **On-demand couples the reviewer to orchestrator wiring.** The harness forgot
  to grant `Skill`; the `@`-include has no such failure mode — the skill is just
  *there*, no tool grant required.

## Verdict

**Reject.** Use the always-on `@`-include for a skill the reviewer **always**
needs. On-demand `Skill` invocation is the right tool only for **conditionally**
needed skills (e.g. agentic-dev-team loads feature-file rules *only when*
`.feature` files appear in the changeset) — there the savings of not loading it
every time outweigh the per-invocation overhead.

> Note: a frontmatter `skills:` line has **no** automatic loader in our setup —
> Claude Code does not expand it. It only does anything paired with the `Skill`
> tool + a runtime invocation. As pure documentation it's harmless but
> misleading (looks functional when it isn't).

## Cost of learning this

~$3.5 total (the 29-dispatch experiment run + matched `stream-json` cost probes)
— to confirm rigorously, with per-fixture data, what a single $0.11 probe first
hinted. Worth it: the conclusion is now data, not a hunch.
