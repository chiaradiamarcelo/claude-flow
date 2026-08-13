# This project is an experimental arm. Read this before doing anything.

This repository exists to **measure the pipeline**, not to ship software. Everything
below protects the measurement. It is identical in every arm, so it cancels out of
any comparison between them.

## Do

- Run `/run-pipeline bank-accounts` and nothing else.
- **Work in place, in this directory.** Do NOT call `EnterWorktree` and do not create
  a worktree. The global Step-0 worktree rule does not apply here: this workspace is
  already an isolated, freshly-initialised git repo, and a worktree would move the
  session transcripts under a different project slug, which makes the run impossible
  to score.
- Behave exactly as you would on a real feature otherwise.

## Do not

- Do **not** run `/intent-and-goal`. The specification at
  `docs/specifications/bank-accounts/specification.md` is already approved and
  **frozen**. Regenerating or editing it makes this arm incomparable to every other
  arm, which destroys the experiment.
- Do **not** edit any agent definition, skill, or slash command under `~/.claude/`.
  Those files *are* the configuration under test.
- Do **not** add build plugins for coverage, mutation testing, or duplication. The
  measurement oracle is applied out-of-band after the run and must stay invisible to
  the work, so that nothing here is written to score well rather than to satisfy the
  specification.

## Project shape

Plain Kotlin + Spring Boot 3.5 + JPA/H2, JUnit 5. `com.example.bank`. Clean
Architecture as defined by the global `clean-architecture` skill: `domain/`,
`application/`, `infrastructure/`, and a thin HTTP boundary.
