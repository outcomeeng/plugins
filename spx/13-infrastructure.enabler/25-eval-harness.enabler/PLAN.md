# Eval Harness: Plan — Wire eval CI workflow

Concrete steps to wire `.github/workflows/spec-tree-evals.yml` so the five gate evals under `spx/21-spec-tree.enabler/76-merging.enabler/evals/` actually run against their `0.85` thresholds, plus the eval-harness node's own scenario evals as the harness grows them.

The runner contract is settled (see `eval-harness.md` line 16): the default invocation omits `--bare` and accepts `CLAUDE_CODE_OAUTH_TOKEN` from the inherited environment. The CI workflow follows the existing `.github/workflows/spec-tree.yml` and `.github/workflows/spec-tree-review.yml` patterns, which already consume the same secret.

## Steps

1. **Author `.github/workflows/spec-tree-evals.yml`** with:
   - **Triggers**: `push` to `main` (so commits that add or modify eval coverage run at merge), `workflow_dispatch` (manual first-run validation), and a `schedule` cron (weekly cadence — start there; tighten if drift signals warrant). NEVER add unrestricted `pull_request` from forks — `_subprocess_env` forwards the full job env, including `CLAUDE_CODE_OAUTH_TOKEN`, to the `claude` subprocess; an eval crafted in a fork PR could exfiltrate the secret.
   - **Job env**: `CLAUDE_CODE_OAUTH_TOKEN: ${{ secrets.CLAUDE_CODE_OAUTH_TOKEN }}` — the same secret `spec-tree.yml` and `spec-tree-review.yml` already use.
   - **Steps**: checkout → setup-python + uv → `uv sync` → `uv run outcomeeng-evals run --all` (the CLI's exit codes already gate pass/fail).
   - **Concurrency**: a single in-flight run per branch (concurrency group keyed to the workflow + ref) so two overlapping invocations against the same eval directory cannot interleave their `history.jsonl` rows. The runner's `append_history_row` is not currently locked; the eval-harness ISSUES.md "CI integration" item names this as the trigger for a `fcntl.flock` if matrix concurrency is ever wanted.

2. **First-run validation via `workflow_dispatch`** — kick the workflow once manually after the first push. Confirm all five gate suites and any eval-harness-local suites exit 0 and meet their `threshold` (default `0.85`). If any suite is non-deterministic under pass@k, tune cases or prompts in the owning eval directory (e.g. `spx/21-spec-tree.enabler/76-merging.enabler/evals/<rule>/`).

3. **CI owns the canonical `history.jsonl` appends**. Per `eval-harness.md` line 28, every suite run appends one summary row to the per-eval `history.jsonl`. CI's run must commit + push that append (or PR it). Developer-machine runs produce local appends that stay out of unrelated commits.

4. **Cadence**: weekly is the starting cadence. Reassess once a few cycles of trend data exist.

5. **Stretch — wire the CLI `--bare` opt-in** (tracked in this node's `ISSUES.md` under "CLI `--bare` opt-in"). The runner already exposes `bare: bool = False`; `outcomeeng_evals/cli/wiring.py:build_claude_runner` does not pass it through. Add a `--bare` flag to `outcomeeng-evals run` and forward to the runner. Optional for this PR; the CI workflow itself does not require the opt-in because CI's discovery surface is already empty.

## References

- **Runner contract**: `spx/13-infrastructure.enabler/25-eval-harness.enabler/eval-harness.md:16` — default argv, auth surface, opt-in `--bare` semantics.
- **Gate-eval node**: `spx/21-spec-tree.enabler/76-merging.enabler/merging.md` — the five `[eval]` assertions whose suites this workflow runs against their thresholds.
- **PR-authority PDR**: `spx/15-agent-pr-authority.pdr.md` — what the merging-node evals grade against.
- **Existing OAuth-token caller workflows**: `.github/workflows/spec-tree.yml`, `.github/workflows/spec-tree-review.yml`, `.github/CLAUDE_WORKFLOWS.md`.
- **Related ISSUES**: this directory's `ISSUES.md` "CI integration" section (high-level framing) and "CLI `--bare` opt-in" tracked item; `spx/21-spec-tree.enabler/76-merging.enabler/ISSUES.md` item 2 (the unrun gate evals).
