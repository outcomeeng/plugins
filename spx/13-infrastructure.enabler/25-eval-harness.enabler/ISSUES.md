# Eval Harness: Deferred Items

Open items carried forward from the eval-harness refactor. None block the harness as shipped; each is a follow-up decision or enhancement.

## Just recipe naming

Confirm `just eval-run` vs. `just eval` aligns with the existing Justfile pattern when the eval recipes are added.

## Required model selection

NEVER run a bare `claude --print` in an eval as this uses the environment's default model. The eval-harness defines a default model to override the environment's default.
An optional `model` field in `eval.toml` would let an eval pin against a specific model for reproducibility but this violates the eval-harness's governed maxim of consistency.

## Cross-suite parallelism

The harness supports `--workers` for parallelism within a suite. `run --all` could also parallelize across suites. Defer; today's use case is one eval at a time.

## CI integration

The CI workflow `.github/workflows/spec-tree-evals.yml` runs the eval suites: it discovers each `eval.toml` under the configured root and runs it through `outcomeeng-evals run` (the CLI has no `run --all`; the workflow loops over `discover` output), gating the job on each suite's exit code. It triggers on every `pull_request` touching the spec-tree plugin / its evals / the harness (gated by a collaborator-authorization job so untrusted PRs never receive secrets), on `push` to main, on a weekly `schedule`, and on `workflow_dispatch`. The runner derives `--bare` from the inherited environment by default per `eval-harness.md`: it passes `--bare` when `ANTHROPIC_API_KEY` is set (the only `--bare`-compatible auth source), otherwise it omits `--bare` so `CLAUDE_CODE_OAUTH_TOKEN` / `apiKeyHelper` / an OAuth login session is accepted. A developer with `ANTHROPIC_API_KEY` exported locally gets `--bare`-isolation from ambient `~/.claude/CLAUDE.md` and the cwd's `AGENTS.md` without further setup. For CI to take the isolated path, `secrets.ANTHROPIC_API_KEY` must be exposed to the job and forwarded into env — currently the workflow forwards only `CLAUDE_CODE_OAUTH_TOKEN`, so CI runs without `--bare` (which is correct for that auth source but does not provide isolation). See the workflow-env TODO below.

CI owns the canonical appends on main: `spec-tree-evals.yml`'s commit-back step pushes them with `[skip ci]` via the `OUTCOMEENG_EVAL_STORE` PAT. Developer-machine runs still append local rows that show up as `git diff` noise. Staging discipline: do not stage `**/evals/**/history.jsonl` unless the commit's purpose *is* an eval run — restore it (`git checkout -- <path>`) before committing unrelated changes. The repo's `.gitattributes` marks these files `merge=union` so concurrent appends from different branches merge cleanly instead of conflicting; that covers merges, not the staging hygiene, which still wants the CI step (or a pre-commit guard) to fully solve.

`append_history_row` (in `outcomeeng_evals/history.py`) opens the file in append mode and writes one line. Within a single `outcomeeng-evals run` the GIL serializes the workers, so rows land in case order. But two overlapping `run` invocations against the same eval directory — a CI matrix, or a developer running while CI runs — can interleave their rows in the file (`merge=union` resolves the *git merge*, not the *concurrent write*). `spec-tree-evals.yml` serializes its main/schedule runs (concurrency group per ref, `cancel-in-progress: false`), so the workflow's own runs don't interleave their appends. The file lock (`fcntl.flock` or a lockfile) is only needed if a developer runs the same eval while CI runs it, or if the workflow later fans out the same eval across a matrix.

The eval CI workflow (`spec-tree-evals.yml`) scopes to trusted triggers: `push` to `main`, `schedule`, and `workflow_dispatch` run unconditionally; `pull_request` runs only after the `authorize` job confirms the PR is same-repo (not a fork) and its author has `admin`/`maintain`/`write` permission. Fork PRs are skipped because GitHub withholds secrets from `pull_request` events triggered by a fork, so the `claude` subprocess would never receive `CLAUDE_CODE_OAUTH_TOKEN`. `_subprocess_env` forwards the full job environment to the `claude` subprocess, so an eval crafted in an untrusted PR could otherwise exfiltrate job secrets; the mitigation is the trigger scoping plus the authorization gate, not env filtering (auth resolution requires the inherited env).

## FOLLOW-UP: no PR-time guarantee that `dist/claude/spec-tree` matches `src/plugins/spec-tree`

`spec-tree-evals.yml` loads `--plugin-dir dist/claude/spec-tree` — the committed runtime tree, which is what consumers install, so grading the committed `dist` is the correct surface for the eval. But a PR that edits `src/plugins/spec-tree/**` while committing a stale `dist/` (a `--no-verify` bypass of the `build-skills` pre-commit hook) would have the eval grade the old runtime, hiding a source-only regression. The repo has no deterministic CI gate on PRs (`just check`'s `dist-diff` step runs only locally and in the pre-commit hook), so nothing on the PR independently enforces `dist == build(src)`.

The right fix is a repo-wide deterministic CI gate (run `just check`, including `dist-diff`, on `pull_request`), not a `dist`-freshness step bolted onto the eval workflow — the eval's job is to grade the shipped artifact, not to police build freshness. Track here until that gate exists.

`.github/workflows/spec-tree-evals.yml` commits the appended `history.jsonl`
rows back to `main` using the org-level PAT secret `OUTCOMEENG_EVAL_STORE`
rather than the built-in `GITHUB_TOKEN`, so the push keeps working once `main`
is branch-protected (the built-in token cannot push to a protected branch).
If the secret is not visible to this repo, the commit-back step skips with a
warning and the eval gate still runs — so the gate stays unblocked, but no
canonical `history.jsonl` baseline is recorded.

Action required for commit-back to work on a protected `main`:

- Ensure the org secret `OUTCOMEENG_EVAL_STORE` includes `outcomeeng/plugins`
  in its repository-visibility scope (org → Secrets and variables → Actions →
  the secret → Repository access).
- When enabling branch protection on `main`, add the token's account to the
  protection bypass-allowances so its push is not rejected.

## TODO: expose `ANTHROPIC_API_KEY` to the eval workflow so CI runs isolated

`spec-tree-evals.yml` currently forwards only `CLAUDE_CODE_OAUTH_TOKEN` into the `evals` job env. Under the runner's derive rule (`eval-harness.md`), that means CI runs without `--bare` — `claude` is invoked under the OAuth token (correct for that auth source) but ambient discovery is not suppressed at the CLI level. CI's runner image happens to have no `~/.claude/CLAUDE.md` or repo `AGENTS.md` in the standard locations, so the contamination surface is narrower than a developer's, but the CLI flag is the explicit defense and the workflow should take it.

Action required:

- Add `ANTHROPIC_API_KEY` to the repo's Actions secrets (org-scope or repo-scope; either is fine for this workflow).
- In `spec-tree-evals.yml`, add `ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}` to the `evals` job's `env` block alongside the existing `CLAUDE_CODE_OAUTH_TOKEN`. The runner's derive rule then takes the `--bare` path on every CI invocation.

Until both land, CI omits `--bare` and runs under OAuth (functional, but not the spec-canonical isolated surface).

## CLI `--bare` / `--no-bare` overrides

The runner exposes `bare: bool | None = None`: `None` derives `--bare` from the inherited environment (`ANTHROPIC_API_KEY` present → pass `--bare`), `True` and `False` force the flag on or off regardless of env. The derivation covers the common case — a developer with `ANTHROPIC_API_KEY` exported gets isolation automatically — so the canonical entry point does not need a flag to make `--bare` reachable. The overrides remain useful for two narrow cases: (a) exercising the ambient-discovery code path under test even when `ANTHROPIC_API_KEY` happens to be set (`bare=False`), and (b) forcing isolation when the auth source is `apiKeyHelper` rather than the env-var form (`bare=True`). Add a `--bare` / `--no-bare` flag pair to `outcomeeng-evals run` (wired through `build_claude_runner`) so the two overrides are reachable from the canonical entry point; defer until either need surfaces in a real session.

## FOLLOW-UP: cover the empty-auth-env path in `_effective_bare` tests

The spec assertion at `eval-harness.md:16` names three OAuth-side auth sources under which `--bare` is omitted: `CLAUDE_CODE_OAUTH_TOKEN`, `apiKeyHelper`, and "an OAuth login session". The scenario tests in `tests/test_runner.scenario.l1.py` cover `CLAUDE_CODE_OAUTH_TOKEN` (`test_claude_cli_runner_omits_bare_when_only_oauth_token_is_set`) and both explicit overrides, but the path where neither `ANTHROPIC_API_KEY` nor `CLAUDE_CODE_OAUTH_TOKEN` is set in env — the "OAuth login session" or "no env-form auth" case — has no dedicated scenario. `_effective_bare` returns `False` in that case (correct: derivation only flips to `--bare` when `ANTHROPIC_API_KEY` is set), but the assertion mapping to the OAuth-login-session path is untested.

Add a scenario test that monkeypatches both `ANTHROPIC_API_KEY` and `CLAUDE_CODE_OAUTH_TOKEN` out of the env, runs `ClaudeCliRunner(plugin_dir=tmp_path)`, and asserts `--bare` is absent from the captured argv. Co-locate in `test_runner.scenario.l1.py` alongside the existing four derive/override cases.

## Independent uv project for `outcomeeng_evals`

`outcomeeng_evals` builds from the single repo `pyproject.toml`. Split into an independent uv project only when it is published to PyPI or its dependency surfaces diverge from the marketplace's.

## `outcomeeng_evals.testing` public-API contract

The runner ships fakes and factories under `outcomeeng_evals.testing`. Whether that subpackage is a stable, versioned surface or an internal helper with no compatibility guarantees is not yet declared. Decide when the first external consumer appears.

## Prompt-template placeholder validation (stricter form)

`_render_prompt` (in `outcomeeng_evals/cli/commands/run.py`) emits a stderr warning when it meets an identifier-shaped `{token}` that isn't a known placeholder (catching `{casse_id}` and similar typos at render time). A stricter form — validating `prompt.md` against the known keys at `load_definition` time and *raising* rather than warning — would catch the typo before any model call. Deferred: the render-time warning covers the common case, and raising would need care so a template that legitimately contains a `{identifier}` literal (rare, but possible) is not rejected. Revisit if prompt authoring becomes a frequent operation.

## Version-keyed `claude` envelope extraction

`_assistant_text` (in `outcomeeng_evals/runner.py`) probes the parsed `claude --output-format json` envelope for `result`, then `response`, then `content`. If a future CLI release renames the key or adds one that collides with an unrelated field, the probe could succeed and return the wrong text rather than failing loudly. If `claude --output-format json` emits a version field (`cli_version`, `schema_version`, or similar), use it to select the extraction path instead of probing by key order. Deferred until the envelope shape actually shifts.

## Tilde-fenced code blocks in the link walker

`_strip_code_regions` (in `outcomeeng_testing/evals/link_integrity.py`) blanks backtick fences (`` ``` ``) but not tilde fences (`~~~`), which CommonMark also allows. A `~~~`-fenced block containing a `[test](...)` or `[eval](...)` example would be treated as a real evidence reference and flagged broken. No marketplace spec markdown uses tilde fences today; if one does, add tilde-fence matching to `_strip_code_regions`.

## Partial-trial evidence in parallel-path errors

`_error_outcome` (in `outcomeeng_evals/suite.py`) replaces all of a case's trials with one synthetic `trial_index=0` failing trial when the worker raises. If trial 1 passed and trial 2 raised, the successful trial's evidence is lost from the report. A richer error outcome — successful trials kept, the error appended as the final trial — would preserve that evidence. Defer; today's runs use `trials_per_case = 1`, so the loss is moot until multi-trial parallel runs are common.

## Drop `[review]` once the `[audit]` migration completes

`spx/14-verification.pdr.md` introduces the `[audit]` verification type (backed by the auditing type) and runs it alongside the legacy `[review]` tag during migration. This validator (`outcomeeng/validation/eval_links.py` → `outcomeeng_testing/evals/link_integrity.py`) resolves only the path-bearing `[test]` and `[eval]` links; `[audit]` and `[review]` are pathless and not resolved here. Once every assertion carrying `[review]` is reclassified — to `[audit]` (agentic checklist evidence) or to a reviewing gate (no lane) — drop `[review]` from the recognized evidence tags in `references/assertion-types.md`, `references/verification-kinds.md`, and any validator or lint rule that enumerates the lane set.
