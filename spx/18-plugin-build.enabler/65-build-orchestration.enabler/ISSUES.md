# Build orchestration issues

## Executable checkout-local Codex recipe evidence

The compliance evidence parses the `codex-local` recipe and proves that it
declares the build, runtime preparation, and `CODEX_HOME`-bound launch commands.
The test-evidence audit rejects this as insufficient for the assertion in
`build-orchestration.md` because a regression inside
`build_project_runtime()` could leave the recipe declaration unchanged.

Revisit with an L2 harness that executes the `codex-local` path in an isolated
product copy, proves generated plugin and custom-agent state, and terminates the
real Codex launch through a bounded non-interactive argument such as `--help`.
The harness must not mutate the assigned checkout or the user's Codex home.
