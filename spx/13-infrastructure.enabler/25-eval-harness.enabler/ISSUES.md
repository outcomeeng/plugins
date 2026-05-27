# Eval Harness: Deferred Items

Open items carried forward from the eval-harness refactor. None block the harness as shipped; each is a follow-up decision or enhancement.

## Just recipe naming

Confirm `just eval-run` vs. `just eval` aligns with the existing Justfile pattern when the eval recipes are added.

## Optional per-eval model pin

`claude --print` uses the user's default model. An optional `model` field in `eval.toml` would let an eval pin against a specific model for reproducibility. Defer until a real need arises.

## Cross-suite parallelism

The harness supports `--workers` for parallelism within a suite. `run --all` could also parallelize across suites. Defer; today's use case is one eval at a time.

## CI integration

A scheduled CI workflow that runs `outcomeeng-evals run --all` and posts results is not yet wired. The CLI's exit codes make this straightforward to add later. The runner invokes `claude --bare`, whose auth is strictly `ANTHROPIC_API_KEY` or an `apiKeyHelper` (never OAuth or keychain), so the workflow must export `ANTHROPIC_API_KEY` into the job environment; this is also why a developer can only run evals locally by exporting a key, not from an OAuth-only session.

Until CI owns the canonical appends, every developer-machine run appends a row to `history.jsonl`, which shows up as `git diff` noise. Staging discipline: do not stage `**/evals/**/history.jsonl` unless the commit's purpose *is* an eval run — restore it (`git checkout -- <path>`) before committing unrelated changes. The repo's `.gitattributes` marks these files `merge=union` so concurrent appends from different branches merge cleanly instead of conflicting; that covers merges, not the staging hygiene, which still wants the CI step (or a pre-commit guard) to fully solve.

`append_history_row` (in `outcomeeng_evals/history.py`) opens the file in append mode and writes one line. Within a single `outcomeeng-evals run` the GIL serializes the workers, so rows land in case order. But two overlapping `run` invocations against the same eval directory — a CI matrix, or a developer running while CI runs — can interleave their rows in the file (`merge=union` resolves the *git merge*, not the *concurrent write*). Acceptable for now; if CI ever runs the same eval concurrently, give `append_history_row` a file lock (`fcntl.flock` or a lockfile).

When the eval CI workflow is wired, scope it to trusted triggers only — `push` to `main` or a `workflow_dispatch`/`schedule`, not an unrestricted `pull_request` from forks. `_subprocess_env` forwards the full job environment (including any job-level secrets) to the `claude` subprocess; an eval crafted in a fork PR could exfiltrate those secrets if the workflow ran with them in scope. Auth resolution requires the inherited env, so the mitigation is trigger scoping, not env filtering.

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
