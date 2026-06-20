# Diagnostics

PROVIDES a portable environment-diagnostics capability — the `diagnose` skill — that runs a sequence of named health checks over a spec-tree / spx environment and reports a per-check verdict with a remediation hint
SO THAT a user or agent working any spec-tree product
CAN self-diagnose a misconfigured environment without recalling and typing the underlying interrogation by hand

The capability orchestrates surfaces every consumer already has — the `spx` CLI, the harness session environment, and the install state — and carries no heavy diagnostic logic of its own; a check that outgrows light orchestration extracts into the `spx` CLI per `spx/12-shipped-scripting.adr.md` rather than accreting in the shipped skill. Each check is an independent named diagnostic, so checks are added by extension without restructuring the existing report. The first checks cover the `SessionStart`-hook session environment — the round-trip proven by `spx/21-spec-tree.enabler/13-agent-environment.enabler` — and `spx` reachability and version.

## Assertions

### Compliance

- ALWAYS: the session-environment check classifies the session as working, identity-only, silent no-op, or — when the readings are inconsistent or a command errors — unknown, from the agent session identity, the worktree-claim flag, and the `spx worktree status` round-trip, pairing each verdict with a remediation hint ([eval](evals/session-environment-check/eval.toml))
- ALWAYS: the spx-reachability check classifies `spx` as reachable-and-current, reachable-below-floor, unreachable, or — when the version or declared minimum cannot be determined — unknown, from its PATH resolution and reported version against the consumer's declared minimum, pairing each verdict with a remediation hint ([eval](evals/spx-reachability-check/eval.toml))
- ALWAYS: the skill aggregates its checks into one report carrying a named verdict per check and an overall verdict ([eval](evals/diagnostic-report/eval.toml))
- ALWAYS: the shipped skill reasons only about surfaces every consumer has — the `spx` CLI, harness environment variables, and install state — and names no product-internal spec-tree node address ([audit])
- ALWAYS: each check is an independent named diagnostic carrying its own verdict and remediation, so a check is added by extension without restructuring existing checks ([audit])
- NEVER: the shipped skill carries heavy, test-bearing diagnostic logic of its own — light orchestration of existing `spx` and harness surfaces stays in the skill, and a check that outgrows it extracts into the `spx` CLI per `spx/12-shipped-scripting.adr.md` ([audit])
