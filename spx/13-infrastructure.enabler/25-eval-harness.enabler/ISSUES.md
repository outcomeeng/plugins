# Eval Harness: Deferred Items

Open items carried forward from the eval-harness refactor. None block the harness as shipped; each is a follow-up decision or enhancement.

## Sectionless Python producer contributes zero section cases

The producer-section case corpus (`producer_cases()` in `outcomeeng_testing/evals/producer_prompt.py`) scans every shipped `audit*tests` skill for named `<step name="...">` sections. `dist/claude/python/skills/audit-python-tests/SKILL.md` (and its `dist/codex` mirror) carries zero such sections, so the Python producer silently contributes no section cases to the section-materialization and section-mutation evidence, while the spec-tree, TypeScript, and Rust producers contribute 10, 8, and 8. The whole-file mapping evidence (`spx/13-infrastructure.enabler/25-eval-harness.enabler/tests/test_producer_files_prompt.mapping.l1.py`) still covers the Python producer.

**Why deferred**: the fix restructures another plugin's shipped skill content — adding named step sections to `src/plugins/python/skills/audit-python-tests/SKILL.md` requires the skill-auditor gate, a python plugin version bump, `dist/` regeneration, and content design of that skill's section structure; it exists independently of this changeset (the skill ships sectionless on the default branch today).

**Resolution shape**: add named `<step name="...">` sections to `src/plugins/python/skills/audit-python-tests/SKILL.md` and rebuild, then add an assertion in `producer_cases()` (or a dedicated test) that fails when any discovered producer contributes zero named-step cases, so a producer silently losing its step markup surfaces as a test failure. The assertion lands second because it is red until the Python skill carries sections.

## Cross-suite parallelism

The harness supports `--workers` for parallelism within a suite. `run --all` could also parallelize across suites. Defer; today's use case is one eval at a time.

## CI integration

The CI workflow `.github/workflows/spec-tree-evals.yml` runs planned eval
suites through `outcomeeng-evals ci`. It discovers each `eval.toml` under the
configured root, filters out `ci_policy = "manual"` suites, and chooses
full-suite, smoke-case, or skipped execution from the trigger mode and
changed paths. PRs run smoke cases when a changed file matches a suite's
`owned_paths`, run a full suite when the suite definition or eval harness
changed, and skip unrelated suites. `push` to main, the weekly schedule, and
`workflow_dispatch` run every non-manual suite under the configured root.
Each selected suite runs through the Python CI executor, which constructs the
`outcomeeng-evals run` command using the suite's `plugin_dir` or the workflow
fallback, and the job gates on the aggregate exit code.

The workflow triggers on PRs touching declared eval ownership surfaces, pushes
to `main` for the same surfaces, a weekly `schedule`, and `workflow_dispatch`.
PR execution is gated by collaborator authorization so untrusted PRs never
receive secrets. The runner follows the auth mode already provisioned in the
inherited environment per `eval-harness.md`: a non-empty `ANTHROPIC_API_KEY`
selects the `--bare` path, and an absent or empty `ANTHROPIC_API_KEY` keeps the
non-bare path while preserving the inherited environment, including
`CLAUDE_CODE_OAUTH_TOKEN` when present. Agents use the provisioned mode as found
and do not ask the operator to add, remove, or switch auth secrets for an eval
run.

CI owns the canonical appends on main: `spec-tree-evals.yml`'s commit-back step pushes them with `[skip ci]` via the `OUTCOMEENG_EVAL_STORE` PAT. Developer-machine runs still append local rows that show up as `git diff` noise. Staging discipline: do not stage `**/evals/**/history.jsonl` unless the commit's purpose *is* an eval run — restore it (`git checkout -- <path>`) before committing unrelated changes. The repo's `.gitattributes` marks these files `merge=union` so concurrent appends from different branches merge cleanly instead of conflicting; that covers merges, not the staging hygiene, which still wants the CI step (or a pre-commit guard) to fully solve.

`append_history_row` (in `outcomeeng_evals/history.py`) opens the file in append mode and writes one line. Within a single `outcomeeng-evals run` the GIL serializes the workers, so rows land in case order. But two overlapping `run` invocations against the same eval directory — a CI matrix, or a developer running while CI runs — can interleave their rows in the file (`merge=union` resolves the *git merge*, not the *concurrent write*). `spec-tree-evals.yml` serializes its main/schedule runs (concurrency group per ref, `cancel-in-progress: false`), so the workflow's own runs don't interleave their appends. The file lock (`fcntl.flock` or a lockfile) is only needed if a developer runs the same eval while CI runs it, or if the workflow later fans out the same eval across a matrix.

The eval CI workflow (`spec-tree-evals.yml`) scopes to trusted triggers: `push` to `main`, `schedule`, and `workflow_dispatch` run unconditionally; `pull_request` runs only after the `authorize` job confirms the PR is same-repo (not a fork) and its author has `admin`/`maintain`/`write` permission. Fork PRs are skipped because GitHub withholds secrets from `pull_request` events triggered by a fork, so the `claude` subprocess would never receive `CLAUDE_CODE_OAUTH_TOKEN`. `_subprocess_env` forwards the full job environment to the `claude` subprocess, so an eval crafted in an untrusted PR could otherwise exfiltrate job secrets; the mitigation is the trigger scoping plus the authorization gate, not env filtering (auth resolution requires the inherited env).

## FOLLOW-UP: no PR-time guarantee that `dist/claude/spec-tree` matches `src/plugins/spec-tree` (RESOLVED)

`spec-tree-evals.yml` loads `--plugin-dir dist/claude/spec-tree` — the committed runtime tree, which is what consumers install, so grading the committed `dist` is the correct surface for the eval. But a PR that edits `src/plugins/spec-tree/**` while committing a stale `dist/` (a `--no-verify` bypass of the `build-skills` pre-commit hook) would have the eval grade the old runtime, hiding a source-only regression. The repo has no deterministic CI gate on PRs (`just check-full`'s `dist-diff` step runs only locally and in the pre-commit hook), so nothing on the PR independently enforces `dist == build(src)`.

The right fix is a repo-wide deterministic CI gate (run `just check-full`, including `dist-diff`, on `pull_request`), not a `dist`-freshness step bolted onto the eval workflow — the eval's job is to grade the shipped artifact, not to police build freshness. Track here until that gate exists.

Resolved 2026-06-16: `.github/workflows/check.yml` now runs the validation package on `pull_request` and `push` to `main`; the full gate recipe includes `build-skills` and `dist-diff`, so PR-time deterministic verification enforces `dist == build(src)`.

`.github/workflows/spec-tree-evals.yml` commits the appended `history.jsonl`
rows back to `main` using the org-level PAT secret `OUTCOMEENG_EVAL_STORE`
rather than the built-in `GITHUB_TOKEN`, so the push keeps working once `main`
is branch-protected (the built-in token cannot push to a protected branch). The
secret is visible to `outcomeeng/plugins`, and the token account can bypass
`main` branch protection for commit-back pushes.

## Independent uv project for `outcomeeng_evals`

`outcomeeng_evals` builds from the single repo `pyproject.toml`. Split into an independent uv project only when it is published to PyPI or its dependency surfaces diverge from the marketplace's.

## Prompt-template placeholder validation (stricter form)

`_render_prompt` (in `outcomeeng_evals/cli/commands/run.py`) emits a stderr warning when it meets an identifier-shaped `{token}` that isn't a known placeholder (catching `{casse_id}` and similar typos at render time). A stricter form — validating `prompt.md` against the known keys at `load_definition` time and *raising* rather than warning — would catch the typo before any model call. Deferred: the render-time warning covers the common case, and raising would need care so a template that legitimately contains a `{identifier}` literal (rare, but possible) is not rejected. Revisit if prompt authoring becomes a frequent operation.

## Version-keyed `claude` envelope extraction

`_assistant_text` (in `outcomeeng_evals/runner.py`) probes the parsed `claude --output-format json` envelope for `result`, then `response`, then `content`. If a future CLI release renames the key or adds one that collides with an unrelated field, the probe could succeed and return the wrong text rather than failing loudly. If `claude --output-format json` emits a version field (`cli_version`, `schema_version`, or similar), use it to select the extraction path instead of probing by key order. Deferred until the envelope shape actually shifts.

## Tilde-fenced code blocks in the link walker

`_strip_code_regions` (in `outcomeeng/validation/link_integrity.py`) blanks backtick fences (`` ``` ``) but not tilde fences (`~~~`), which CommonMark also allows. A `~~~`-fenced block containing a `[test](...)` or `[eval](...)` example would be treated as a real evidence reference and flagged broken. No marketplace spec markdown uses tilde fences today; if one does, add tilde-fence matching to `_strip_code_regions`.

## Partial-trial evidence in parallel-path errors

`_error_outcome` (in `outcomeeng_evals/suite.py`) replaces all of a case's trials with one synthetic `trial_index=0` failing trial when the worker raises. If trial 1 passed and trial 2 raised, the successful trial's evidence is lost from the report. A richer error outcome — successful trials kept, the error appended as the final trial — would preserve that evidence. Defer; today's runs use `trials_per_case = 1`, so the loss is moot until multi-trial parallel runs are common.

## Drop `[review]` once the `[audit]` migration completes

`spx/31-outcomeeng.enabler/31-verification.enabler/14-verification.pdr.md` introduces the `[audit]` verification type (backed by the auditing type) and runs it alongside the legacy `[review]` tag during migration. This validator (`outcomeeng/validation/eval_links.py` → `outcomeeng/validation/link_integrity.py`) resolves only the path-bearing `[test]` and `[eval]` links; `[audit]` and `[review]` are pathless and not resolved here. Once every assertion carrying `[review]` is reclassified — to `[audit]` (agentic checklist evidence) or to a reviewing gate (no lane) — drop `[review]` from the recognized evidence tags in inline `/understand` `<assertion_model>` and `<verification_model>`, and any validator or lint rule that enumerates the lane set.
