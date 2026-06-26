# PLAN: operability of the `/issue` skill depends on `spx session handoff -C`

## Pending operational dependency

The `/issue` skill files a cross-repo follow-up by running `spx session handoff -C <target-dir>` — a git-style flag that runs the handoff against another repository's checkout so the recorded `git_ref` and the queued session belong to the target.

The installed `spx` does not yet expose `-C`:

- `spx --version` → `0.6.4`; `spx session handoff --help` advertises only `--sessions-dir <path>`, not `-C`.
- `REQUIRED_SPX_VERSION` in `outcomeeng/validation/spx_version.py` is `0.6.3`; the CI pin `SPX_VERSION` in `.github/workflows/check.yml` is `0.6.3`.

Per the repository rule "Depend on an `spx` CLI capability only after it is PUBLISHED and the floor is advanced," the skill is non-operable for consumers until `-C` ships. The `issue-capture` eval is a decision-simulation that verifies the model's judgment, not the CLI, so it runs independently of `-C`; the skill's runtime invocation does not.

## Remaining steps

1. Land `spx session handoff -C <dir>` in `@outcomeeng/spx` and publish a release to npm.
2. Advance `REQUIRED_SPX_VERSION` in `outcomeeng/validation/spx_version.py` to that published version.
3. Bump `SPX_VERSION` in `.github/workflows/check.yml` to a published version at or above the floor.
4. Remove `21-spec-tree.enabler/76-sessions.enabler/43-issue.enabler` from `spx/EXCLUDE` and run the `issue-capture` eval to record a passing run in `evals/issue-capture/history.jsonl`.

Until step 1 publishes, the node carries its specification and the skill carries its workflow, but the runtime `-C` call cannot succeed against a consumer's installed `spx`.
