# Engineering findings (lab notebook)

Measured discoveries from building and running the pipeline's own eval harness
("using the tool to build the tool"). Each entry records **what changed**,
**what it caused** (performance / cost / quality), and **why** (the mechanism) —
so a decision is never re-litigated from a hunch.

Every number here was *measured*, not estimated — mostly via
`claude -p ... --output-format stream-json` (`total_cost_usd` + token usage) and
the eval suite (`evals/run_all.sh`).

## Findings

1. [A deterministic grader bug masqueraded as agent flakiness](findings/01-grader-bug-masquerades-as-agent-flakiness.md)
   — a one-character regex flaw (`\s` vs `[ \t]`) looked like the model "routing
   by topic" and cost a quarantine + a whole router script before we found it.
2. [Skill loading: always-on `@`-include vs on-demand `Skill` tool](findings/02-skill-loading-include-vs-on-demand.md)
   — moving the skill from an `@`-include to a frontmatter `skills:` + `Skill`
   tool cost **~1.8× per dispatch** and ~1.7× wall-clock for **zero** quality
   gain. Rejected.
3. [Eval cost model](findings/03-eval-cost-model.md)
   — ~$0.06 per reviewer dispatch, ~$1.7 for the 29-fixture corpus cold, **$0**
   on cached re-runs. What's cached, what isn't, what invalidates it.
4. [Writing robust agent evals](findings/04-writing-robust-agent-evals.md)
   — fresh-process requirement, tolerant assertions, `mustMention` substring
   pitfalls, when (not) to quarantine.

## Conventions used across these notes

- **Change / Effect / Why / Verdict** structure per finding.
- Costs are Sonnet-tier (`model: sonnet` reviewers) unless noted.
- "dispatch" = one `claude -p --agent <reviewer>` reviewing one fixture.
