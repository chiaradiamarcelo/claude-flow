---
description: Review a pull request in three parallel unbiased lanes - the native code-review skill on Opus at high effort for correctness, the project's convention reviewers over the PR's changed files, and a lean/remove pass over the comments the PR adds. Posts a summary comment on the PR by default; --fix fixes and pushes instead.
argument-hint: <PR number, PR URL, or branch> [--fix] [--unattended] [--effort <low|medium|high|max>]
allowed-tools: Bash, Agent, Read, Edit, Write, Grep, Glob, Skill
---

Review pull request: **$ARGUMENTS**

This command reviews code **it did not write**. The whole point of the subagent
in Step 3 is that the reviewer starts with an empty context: it never sees this
session's reasoning about the change, who wrote it, or why the author thought it
was correct. Do not review the diff yourself, do not summarise your own opinion
of it, and do not pass the subagent any framing beyond the target and the ticket
text — anything you add is the bias the subagent exists to avoid.

Run it from a checkout of the PR's repository. The lanes' `isolation="worktree"`
makes worktrees of the session's repo, so a session sitting in another repo
reviews the wrong code. If the session's `origin` is not the PR's repository,
stop and say so.

## Step 1: Resolve the target

Parse **$ARGUMENTS**:

- A bare number (`4630`) or a GitHub URL → that PR number.
- Anything else that is not a flag → treat as a branch name and resolve it with
  `gh pr list --head <branch> --json number --jq '.[0].number'`.
- No target at all → the PR for the current branch:
  `gh pr view --json number --jq .number`. If there is none, stop and say so.

Flags:

- `--fix` — instead of posting the summary comment, fix what must be fixed on
  the PR branch, commit and push (Step 5b). Use it on your own PR. Fixing is
  never implied — only this flag triggers it.
- `--effort <level>` — override the review effort. **Default: `high`.**
- `--unattended` — nobody is watching the session (a routine or a scripted
  review started it), so the command never asks the user anything and never
  waits for input. Each place below that would stop and ask says what to do
  instead. When a choice comes up that this file does not cover, pick the
  option that asks the PR author a question in the summary comment over the
  one that asks the user. Not allowed with `--fix`: fixing someone's branch
  unattended is never right, so stop and say so.

Without `--fix`, the command posts one summary comment on the PR (Step 5a) —
that is the default. `--comment` is accepted and means the same thing.

## Step 2: Fetch PR context (cheap, metadata only)

Run in one message:

```
gh pr view <N> --json number,title,body,headRefName,baseRefName,additions,deletions,changedFiles,files
```

If the PR body references a ticket (`TICKET-123`, `ISSUE-45`, …), keep the
identifier — the subagent may fetch it. Do **not** paste your own interpretation
of the ticket.

**Guard:** if `changedFiles` exceeds 150 or `additions + deletions` exceeds 5000,
say so and ask whether to proceed before spending the review — a changeset that
size is usually a rename sweep or a lockfile bump wearing a feature's clothes.
With `--unattended`, proceed without asking and mention the size in the
summary comment.

With `--unattended`, also check the author now, before any lane runs:
`gh pr view <N> --json author --jq .author.login` against `gh api user --jq .login`.
If it is your own PR, post nothing, say so, and stop.

## Step 3: Dispatch the reviewers

Three lanes, dispatched **in the same message** so they run in parallel. They
answer different questions and none subsumes another: 3a finds bugs, 3b finds
convention violations, 3c finds comments that should be leaner or gone. All
start from an empty context.

### Step 3a: the correctness lane

Spawn exactly one agent, on Opus, in an isolated worktree so a
`gh pr checkout` can never touch the user's working tree:

```
Agent(
  subagent_type="general-purpose",
  model="opus",
  isolation="worktree",
  description="Unbiased review of PR <N>",
  prompt="""
You are reviewing PR #<N> in this repository with no prior involvement in it.

Check out the PR: `gh pr checkout <N>`.

Then invoke the code-review skill:
  Skill(skill="code-review", args="<effort> <N>")

Follow that skill's instructions exactly, including its verification pass —
report only findings that survive verification, and use ReportFindings if the
skill tells you to.

Ground rules:
- Judge the code as written against the repo's own conventions
  (AGENTS.md, .claude/CLAUDE.md, ${CLAUDE_PLUGIN_ROOT}/knowledge/refactor-catalog/).
- A finding needs a concrete failure scenario: inputs or state -> wrong
  output, crash, or violated convention. Drop anything you cannot make concrete.
- Do not soften a finding because the change looks intentional, and do not
  invent findings to justify the review. "Nothing found" is a valid result.
- <ticket line: "Context: ticket <ID> — fetch it yourself if you need the
  intent." Omit this line entirely if the PR references no ticket.>

Return the findings verbatim, most severe first, plus a one-line verdict.
"""
)
```

Notes on the parameters, so they are not "cleaned up" later:

- `model="opus"` is deliberate — the default subagent model is weaker at
  spotting cross-file correctness bugs, which is most of what this command is
  for.
- `subagent_type="general-purpose"` is what gives the reviewer the full toolset
  the `code-review` skill needs (Bash for `gh`, Read, Grep, ReportFindings).
  The project's `type: reviewer` agents are convention checkers with a narrow
  toolset — those run via `/claude-flow:run-reviewers`, not here.
- `isolation="worktree"` also keeps the review off whatever branch the session
  happens to be on, so a dirty working tree cannot leak into the diff.

Never forward `--fix` or `--comment` to the `code-review` skill. The lanes only
report; Step 5 is the single place that posts or fixes, so the PR gets one
summary instead of a spray of inline comments, and fixes cover all three lanes.

### Step 3b: the convention lane

```
Agent(
  subagent_type="general-purpose",
  isolation="worktree",
  description="Convention review of PR <N>",
  prompt="""
Check out PR #<N>: `gh pr checkout <N>`.

Then run the project's convention reviewers over exactly the files this PR
changes, via the `/claude-flow:run-reviewers` command:

  Skill(skill="claude-flow:run-reviewers", args="<comma-separated changed file paths from Step 2>")

Pass the file paths, not their parent directories — a directory argument lets
the reviewers re-discover files this PR never touched and report pre-existing
violations as if they were introduced here.

Return that command's consolidated report verbatim, including its verdict.
Do not review the code yourself beyond what the reviewers report, and do not
fix anything.
"""
)
```

Why this lane is separate rather than a step inside 3a:

- It needs the PR checked out in a worktree of its own. `/claude-flow:run-reviewers` with
  no arguments works off `git diff` against the current checkout — run from the
  session it would review whatever the user happens to have dirty on their
  branch, not the PR.
- It runs at the **default** model, not Opus. These reviewers are glob-routed
  convention checkers reading their own skill files; the correctness hunt in 3a
  is what needs the stronger model.
- `/claude-flow:run-reviewers` fans out to one fresh agent per triggered reviewer, so the
  bias property holds here too without any extra work.
- A changeset matching no reviewer yields an empty report. That is a valid
  result, not a failure — do not fire reviewers by hand to fill the gap.

### Step 3c: the comments lane

```
Agent(
  subagent_type="general-purpose",
  isolation="worktree",
  description="Comment review of PR <N>",
  prompt="""
Check out PR #<N>: `gh pr checkout <N>`.

Load the comments skill: Skill(skill="claude-flow:comments").

Then read `gh pr diff <N>` and judge every comment the PR adds or modifies —
production source and tests alike — against that skill. Ignore comments the PR
does not touch.

For each comment that fails the skill's test, report: file:line, the comment
verbatim, the verdict (REMOVE, or LEAN with the proposed replacement text, or
RENAME when the comment is a missing name — give the name), and one line citing
the skill's reason.

Return the list, or "No comment issues" if every added comment earns its place.
Do not fix anything.
"""
)
```

## Step 4: Report

Relay the subagent's findings to the user unchanged — the agent's report is not
shown to them. Print, in this order:

```
## PR #<N> — <title>
<changedFiles> files, +<additions>/-<deletions> · effort: <effort> · lanes: correctness + conventions + comments

### Correctness (fresh Opus agent, code-review skill)
<each finding: severity, file:line, one-sentence defect, failure scenario>

### Conventions (run-reviewers)
<VIOLATIONS / WARNINGS / SUGGESTIONS, each prefixed with the reviewer name>
<which reviewers fired, and which were skipped for no glob match>

### Comments (comments skill)
<each: file:line, REMOVE / LEAN / RENAME, proposed text, reason>

### Verdict: <each lane's verdict, verbatim; the PR is clean only if all pass>
```

Report every lane even when one is empty — "no convention violations" is a
result the user needs, and silently dropping an empty lane makes it look like
the lane never ran. If a lane failed outright (agent errored, `gh` could not
reach the PR), say so in place of its findings rather than reporting it as
clean.

Never approve or merge the PR — this command reviews, the user decides.

## Step 5: Act on the findings

Always runs: Step 5a by default, Step 5b with `--fix`. Both act on the same
**must-fix set**:

- every correctness finding;
- every convention **VIOLATION** and **WARNING**;
- the convention **SUGGESTIONS** you judge worth fixing — say which you kept
  and, in one line each, why you dropped the rest;
- every comments-lane finding (REMOVE / LEAN / RENAME).

**Stop and ask when a fix reverses intent.** If a fix would contradict the PR
description, its ticket, or a documented decision in the code or ADRs (the
finding says the PR's own change is wrong), do not pick a side. Put the
options to the user — typically "revert the PR's change" vs "change the
decision" — and wait.
With `--unattended`, do not ask the user and do not count the finding as
must-fix: ask the author instead, as a question in the summary comment
(Step 5a's `### Questions for the author`).

### Step 5a: default — post a summary comment

Post **one** top-level comment with `gh pr comment <N> --body-file <file>`
(write the body to a file in the scratchpad; do not inline it in the shell).
Shape it like this:

- `## Review summary` — one line naming the three lanes, then
  **Verdict: approve / request changes** and which items block.
- `### Must fix — correctness`, `### Must fix — conventions`,
  `### Must fix — comments (/comments)` — numbered or grouped by reviewer, each
  item with a bold one-line title, `file:line`, the failure scenario and the fix.
  In the comments section, list comments that are now false first; put the
  REMOVE and LEAN lists in `<details>` blocks, LEAN items with their replacement
  text.
  Leave out a section whose lane has nothing to fix — no heading, no "None."
  line, no list of reviewers that passed. The verdict line already says the
  PR is clean on that lane; if every lane is empty, the comment is just the
  `## Review summary` block.
- `### Questions for the author` — only with `--unattended`, and only when a
  finding reverses intent: one short question per finding, with `file:line`
  and the options. Questions do not block the verdict.
- Dropped suggestions with a one-line reason each, and findings on older code
  the PR only touches, in a final `<details>` block marked out of scope. Omit
  the block when both are empty.

Before posting, check the PR's author with
`gh pr view <N> --json author --jq .author.login` against `gh api user --jq .login`.
If it is your own PR, stop and ask whether `--fix` was meant instead.

### Step 5b: `--fix` — fix and push

1. Check out the PR head in a fresh, detached worktree of its own — never the
   user's current checkout, never a review worktree:
   `git fetch origin <headRefName> && git worktree add --detach <scratchpad>/pr-<N> origin/<headRefName>`.
   Detached, because the branch is often already checked out in another
   worktree and `git worktree add <branch>` refuses it. Work only inside it.
2. Fix every item in the must-fix set, delegating by module: spawn one
   `general-purpose` agent per module (Gradle module, package, app) that has
   items, in the same message, all working in that one worktree. Give each its
   items verbatim, the skills to load (`claude-flow:testing`,
   `claude-flow:android-testing` or `claude-flow:ui-testing` for tests,
   `claude-flow:comments` for comments), and these limits: touch only files in
   its module, run no state-changing git command, run its module's tests and
   lint, and report each item as fixed or skipped with the reason.
   A handful of items in one module needs no agent — fix them yourself.
3. Check every agent's report: all tests and lint pass. If anything fails,
   fix it; if you cannot, stop, report the failure, and do not push.
4. Commit once, with a message that lists what was fixed, then
   `git push origin HEAD:<headRefName>`. Never force-push.
5. If a fix changed what the PR claims — a behaviour its description lists,
   a test count, a reverted change — update the description
   (`gh pr edit <N> --body-file <file>`) so it matches the pushed code,
   including its test plan if it has one.
6. Report what was fixed, which suggestions were dropped and why, and the
   pushed commit SHA. Remove the worktree.
