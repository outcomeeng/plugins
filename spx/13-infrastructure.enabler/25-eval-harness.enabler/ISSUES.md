# Eval Harness: Deferred Items

Open items carried forward from the eval-harness refactor. None block the harness as shipped; each is a follow-up decision or enhancement.

## Cross-suite parallelism

The harness supports `--workers` for parallelism within a suite. `run --all` could also parallelize across suites. Defer; today's use case is one eval at a time.

## CI integration

The CI workflow `.github/workflows/product-tree-evals.yml` starts only on
`workflow_dispatch`. A dispatched run executes the full plan through
`outcomeeng-evals ci`: it discovers each `eval.toml` under the configured
root, filters out `ci_policy = "manual"` suites, and runs every remaining
suite through the Python CI executor, which constructs the
`outcomeeng-evals run` command using the suite's `plugin_dir` or the workflow
fallback. The job gates on the aggregate exit code. The `plan` and `ci`
subcommands still map a changed-path list to suites through each eval's
`owned_paths` on a developer's machine.

The dispatcher's write access authorizes a run. The runner follows the auth mode already provisioned in the
inherited environment per `eval-harness.md`: a non-empty `ANTHROPIC_API_KEY`
selects the `--bare` path, and an absent or empty `ANTHROPIC_API_KEY` keeps the
non-bare path while preserving the inherited environment, including
`CLAUDE_CODE_OAUTH_TOKEN` when present. Agents use the provisioned mode as found
and do not ask the operator to add, remove, or switch auth secrets for an eval
run.

CI owns the canonical appends on main: `product-tree-evals.yml`'s commit-back step pushes them with `[skip ci]` via the `OUTCOMEENG_EVAL_STORE` PAT. Developer-machine runs still append local rows that show up as `git diff` noise. Staging discipline: do not stage `**/evals/**/history.jsonl` unless the commit's purpose *is* an eval run — restore it (`git checkout -- <path>`) before committing unrelated changes. The repo's `.gitattributes` marks these files `merge=union` so concurrent appends from different branches merge cleanly instead of conflicting; that covers merges, not the staging hygiene, which still wants the CI step (or a pre-commit guard) to fully solve.

`append_history_row` (in `outcomeeng_evals/history.py`) opens the file in append mode and writes one line. Within a single `outcomeeng-evals run` the GIL serializes the workers, so rows land in case order. But two overlapping `run` invocations against the same eval directory — a CI matrix, or a developer running while CI runs — can interleave their rows in the file (`merge=union` resolves the *git merge*, not the *concurrent write*). `product-tree-evals.yml` serializes its main/schedule runs (concurrency group per ref, `cancel-in-progress: false`), so the workflow's own runs don't interleave their appends. The file lock (`fcntl.flock` or a lockfile) is only needed if a developer runs the same eval while CI runs it, or if the workflow later fans out the same eval across a matrix.

The eval CI workflow (`product-tree-evals.yml`) starts only on `workflow_dispatch`, which requires write access to the repository. `_subprocess_env` forwards the full job environment to the `claude` subprocess, so an eval crafted in an untrusted PR could otherwise exfiltrate job secrets; the mitigation is that no pull-request, push, or schedule event starts the workflow, not env filtering (auth resolution requires the inherited env).

## FOLLOW-UP: no PR-time guarantee that `dist/claude/product-tree` matches `src/plugins/product-tree` (RESOLVED)

`product-tree-evals.yml` loads `--plugin-dir dist/claude/product-tree` — the committed runtime tree, which is what consumers install, so grading the committed `dist` is the correct surface for the eval. But a PR that edits `src/plugins/product-tree/**` while committing a stale `dist/` (a `--no-verify` bypass of the `build-skills` pre-commit hook) would have the eval grade the old runtime, hiding a source-only regression. The repo has no deterministic CI gate on PRs (`just check-full`'s `dist-diff` step runs only locally and in the pre-commit hook), so nothing on the PR independently enforces `dist == build(src)`.

The right fix is a repo-wide deterministic CI gate (run `just check-full`, including `dist-diff`, on `pull_request`), not a `dist`-freshness step bolted onto the eval workflow — the eval's job is to grade the shipped artifact, not to police build freshness. Track here until that gate exists.

Resolved 2026-06-16: `.github/workflows/check.yml` now runs the validation package on `pull_request` and `push` to `main`; the full gate recipe includes `build-skills` and `dist-diff`, so PR-time deterministic verification enforces `dist == build(src)`.

`.github/workflows/product-tree-evals.yml` commits the appended `history.jsonl`
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

## The link walker opens a backtick fence whose info string contains a backtick

CommonMark does not treat a line opening with three or more backticks as a fence when its info string contains another backtick; `_strip_code_regions` in `outcomeeng/validation/link_integrity.py` opens the fence regardless, so such a line would blank the rest of its file and hide every evidence link after it from the `eval-links` step. No spec markdown in the tree has that shape (``grep -rnE '^[ \t]{0,3}```[^``\n]*`' spx --include='*.md'` finds nothing), so the gap has no live instance.

**Resolution shape**: refuse the backtick-fence opener when the remainder of the line contains a backtick, and add a layout with such a line followed by a real evidence link to the link-integrity conformance evidence.

## Partial-trial evidence in parallel-path errors

`_error_outcome` (in `outcomeeng_evals/suite.py`) replaces all of a case's trials with one synthetic `trial_index=0` failing trial when the worker raises. If trial 1 passed and trial 2 raised, the successful trial's evidence is lost from the report. A richer error outcome — successful trials kept, the error appended as the final trial — would preserve that evidence. Defer; today's runs use `trials_per_case = 1`, so the loss is moot until multi-trial parallel runs are common.

## The shipped harness retires its producer-coupling assertions at the cutover

The eval-harness redesign re-homes this concern: eval-verification governance moves to `spx/31-outcomeeng.enabler/31-verification.enabler/31-eval-verification.enabler/`, with harness vocabulary under its `21-eval-harness.enabler` child, and the runtime adapter contract the redesigned harness delegates to lives under `spx/31-outcomeeng.enabler/31-verification.enabler/21-agentic-verification.enabler/`. This node's specs, decisions and evidence stay authoritative for the shipped harness until the implementation cutover, after which the node retires.

[`spx/31-outcomeeng.enabler/31-verification.enabler/31-eval-verification.enabler/15-adapter-derived-evals.adr.md`](spx/31-outcomeeng.enabler/31-verification.enabler/31-eval-verification.enabler/15-adapter-derived-evals.adr.md) decides eval coupling for the methodology through the adapter contract, in place of materializing producer text into a prompt. [`spx/13-infrastructure.enabler/25-eval-harness.enabler/57-producer-coupled-skill-evals.adr.md`](spx/13-infrastructure.enabler/25-eval-harness.enabler/57-producer-coupled-skill-evals.adr.md) is scoped to the `outcomeeng_evals` harness alone, so the two decisions govern disjoint subjects while the shipped harness stands. At cutover this node's producer-coupling assertions (the `prompt_source` kind conformance rules, the `materialize-prompts` CLI rule and the producer-derived materialization property) retire with the `outcomeeng_evals/producer_prompt.py` machinery and the generated `prompt.md` files they govern, replaced by the adapter-invoked case shape the new decision declares.

**Settlement condition.** The cutover completes as `spx/31-outcomeeng.enabler/31-verification.enabler/31-eval-verification.enabler/ISSUES.md` records it, and this node retires.

## The cache-amortization prototype stays as the measurement record

[`spx/13-infrastructure.enabler/25-eval-harness.enabler/15-prompt-caching.adr.md`](spx/13-infrastructure.enabler/25-eval-harness.enabler/15-prompt-caching.adr.md) keeps prefix reuse as the cost lever and records the corrected mechanism: capture the amortization on the subscription `claude --print` path through a base session that loads every plugin once and is forked per case, so each case reads the shared prefix warm and writes only its case-specific suffix, keeping the rule against routing to a metered API. `prototypes/eval-cache-amortization/` holds the investigation (`investigation.md`) and the measurement (`FINDINGS.md`: 5.45 times per call, about 73 to 80 percent per suite). The fork-session cache regression persists: since Claude Code v2.1.69 (`anthropics/claude-code#34629`, closed without resolution), `claude --print --resume` and `--fork-session` stop reusing the cached conversation history, so a forked case cold-writes the prefix as the current single-turn shape does, and the harness keeps its single-turn invocation. The telemetry that makes caching observable ships: the per-run cache read and creation token aggregates in `cost_summary` and `history.jsonl`.

No fork-per-case implementation happens in this node. The caching decision re-derives under the agentic-verification node, whose `ISSUES.md` records the open realization paths.
**Settlement condition.** The relocated subtree absorbs the prototype or retires it, per the prove-then-migrate-or-remove lifecycle in [`spx/12-shipped-scripting.adr.md`](spx/12-shipped-scripting.adr.md).

## The eval harness raises AssertionError for lifecycle failures

`outcomeeng_testing/evals/factories.py` and `outcomeeng_testing/harnesses/evals.py` raise `AssertionError` when a resource fails to start or a generated value has the wrong shape. The predicate-seam rule in `/test-evidence-standards` reserves assertion failures for the linked test; infrastructure raises only setup, dependency, lifecycle or execution errors, so raising `AssertionError` from infrastructure reports a failure away from every `assert` site and can read as a verdict the harness owns.

**Evidence.** The isolated test-evidence audit of `spx/13-infrastructure.enabler/13-host-readiness.enabler` on head `e3bf060ce4dd29ff34984b5d66f8302d9ca22e95` rejected the same shape in that node's harness (finding `f-001`), fixed there by raising a `RuntimeError` subclass from a harness-owned horizon.

**Settlement condition.** Each infrastructure `AssertionError` in these modules becomes a lifecycle or dependency error type the harness owns, with every behavioral predicate left in the linked tests, and the node passes its test-evidence audit.

## Harness-owned assertions in the CLI mapping tests

The linked tests in `spx/13-infrastructure.enabler/25-eval-harness.enabler/tests/test_cli.mapping.l1.py` delegate their predicates to `assert_*` functions in `outcomeeng_testing/evals/cli.py`, for example `assert_run_subcommand_rejects_workers_above_cap` and `assert_run_command_filters_cases_by_case_id`. The harness owns the `assert` calls and the expected values, so each linked test hides its predicate and the same harness cannot serve an opposite claim.

**Evidence.** The isolated test-evidence audit of this node on head `ee127962419b7923f6255c614b94ba942c0b6662` filed the pattern as `spx/13-infrastructure.enabler/25-eval-harness.enabler/tests/test_cli.mapping.l1.py:assertion-seam`. The test for the subcommand-name assertion was repaired in that round.

**Settlement condition.** Each delegating `assert_*` harness function returns the observed result, and the linked test owns the comparison, and the node passes its test-evidence audit.

The same pattern holds in six further linked tests of this node. The isolated test-evidence audit of this node on head `9569c99f65bf67acd2b8b004bf82c86953a4e4f3` filed each as a standing finding outside the changeset: `git diff 898a77ee089dbb512ebaf1ec9630a3941fc6fff6..HEAD` shows these files unchanged. Each filed finding carries the severity `FILED`.

- **`f-003`**, key `spx/13-infrastructure.enabler/25-eval-harness.enabler/tests/test_run_exit.mapping.l1.py:assertion-seam`. Evidence: the harness `outcomeeng_testing/harnesses/eval_run_exit.py` owns the assertion and the expected exit values, and the linked test holds no predicate. Settlement condition: the harness returns the observed exit values, the linked test owns the comparison and the expected values, and the node passes its test-evidence audit.
- **`f-004`**, key `spx/13-infrastructure.enabler/25-eval-harness.enabler/tests/test_history.compliance.l1.py:assertion-seam`. Evidence: one wrapper delegates the whole compliance predicate and its expectations to the harness `outcomeeng_testing/harnesses/eval_history.py`. Settlement condition: the harness returns the observed history result, the linked test owns the compliance predicate and its expectations, and the node passes its test-evidence audit.
- **`f-005`**, key `spx/13-infrastructure.enabler/25-eval-harness.enabler/tests/test_report.compliance.l1.py:assertion-seam`. Evidence: the harness `outcomeeng_testing/harnesses/eval_report.py` owns every `assert` and expected value, and every `test_report_*` and `test_run_command_*` function delegates to an `assert_*` function. Settlement condition: each `assert_*` function returns the observed report result, every linked test owns its comparison, and the node passes its test-evidence audit.
- **`f-006`**, key `spx/13-infrastructure.enabler/25-eval-harness.enabler/tests/test_runner.compliance.l1.py:assertion-seam`. Evidence: the harness `outcomeeng_testing/harnesses/eval_runner.py` owns every `assert` and expected value, and every test function delegates to an `assert_*` function. Settlement condition: each `assert_*` function returns the observed runner result, every linked test owns its comparison, and the node passes its test-evidence audit.
- **`f-007`**, key `spx/13-infrastructure.enabler/25-eval-harness.enabler/tests/test_eval_harness.compliance.l1.py:assertion-seam`. Evidence: the harness `outcomeeng_testing/harnesses/eval_harness.py` owns every `assert` and expected value, and every test function delegates to an `assert_*` function. Settlement condition: each `assert_*` function returns the observed result, every linked test owns its comparison, and the node passes its test-evidence audit.
- **`f-008`**, key `spx/13-infrastructure.enabler/25-eval-harness.enabler/tests/test_eval_just_recipes.compliance.l1.py:assertion-seam`. Evidence: the harness `outcomeeng_testing/evals/just_recipes.py` owns the `assert` calls and expected values for seven of eight tests, and only the materialize-prompts writing test keeps its predicate in the test. Settlement condition: the seven delegating `assert_*` functions return the observed results, their linked tests own the comparisons, and the node passes its test-evidence audit.
- **`f-009`**, key `spx/13-infrastructure.enabler/25-eval-harness.enabler/tests/test_definition.property.l1.py:assertion-seam`. Evidence: the harness `outcomeeng_testing/harnesses/evals.py` owns the invariant, so the property invariant is not lexically in the linked test. Settlement condition: the property invariant is stated in the linked test over values the harness generates or returns, and the node passes its test-evidence audit.
