# Eval Harness: Deferred Items

Open items carried forward from the eval-harness refactor. None block the harness as shipped; each is a follow-up decision or enhancement.

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

## The link walker opens a backtick fence whose info string contains a backtick

CommonMark does not treat a line opening with three or more backticks as a fence when its info string contains another backtick; `_strip_code_regions` in `outcomeeng/validation/link_integrity.py` opens the fence regardless, so such a line would blank the rest of its file and hide every evidence link after it from the `eval-links` step. No spec markdown in the tree has that shape (``grep -rnE '^[ \t]{0,3}```[^``\n]*`' spx --include='*.md'` finds nothing), so the gap has no live instance.

**Resolution shape**: refuse the backtick-fence opener when the remainder of the line contains a backtick, and add a layout with such a line followed by a real evidence link to the link-integrity conformance evidence.

## Partial-trial evidence in parallel-path errors

`_error_outcome` (in `outcomeeng_evals/suite.py`) replaces all of a case's trials with one synthetic `trial_index=0` failing trial when the worker raises. If trial 1 passed and trial 2 raised, the successful trial's evidence is lost from the report. A richer error outcome — successful trials kept, the error appended as the final trial — would preserve that evidence. Defer; today's runs use `trials_per_case = 1`, so the loss is moot until multi-trial parallel runs are common.

## CI-trigger marker regex lacks line-start anchoring

`outcomeeng_evals/ci_triggers.py` compiles its `# BEGIN eval-trigger-paths` block-matching regex without a `^` anchor or `re.MULTILINE`, so it can match the marker text mid-line, unlike the `^...$`-anchored router and shared-region matchers in the instruction-block module. `spx/local/generated-sources.toml` declares line-start matching for this marker family and notes the deviation; the declared rule governs attribution, per `spx/31-outcomeeng.enabler/31-verification.enabler/15-generated-attribution.pdr.md`.

**Resolution shape**: anchor the block pattern to the start of a line and cover the anchoring in the node's ci-trigger tests, then drop the deviation note from `spx/local/generated-sources.toml`.

## Linked tests delegate their predicates to harnesses, and evidence spells literals no source exports

The test evidence of `spx/13-infrastructure.enabler/25-eval-harness.enabler` departs from `spx/31-outcomeeng.enabler/31-verification.enabler/31-test-verification.enabler/15-test-infrastructure.pdr.md` in four classes. In predicate ownership, a linked test's body is a call to a harness function named `assert_*`, and that function holds the behavioral predicates, the assertion calls, and for property evidence the invariant — where the decision gives every predicate and assertion call to the executed test and bars a harness from calling an assertion API or returning a verdict. In source ownership, test infrastructure or a second source module spells protocol values — CLI options, prompt placeholders, and payload keys — that another module owns. Two findings fall in test-owned data and one in oracle independence. Test paths below are relative to `spx/13-infrastructure.enabler/25-eval-harness.enabler/`; implementation paths are relative to the repository root.

**Evidence**: the `spec-tree:test-evidence-auditor` verdict on `spx/13-infrastructure.enabler/25-eval-harness.enabler`, whose finding identifiers the entries below carry, and finding `seq 69` of `spec-tree:implementation-auditor` run `2026-09-29_08-28-25-044-56943925c5c1`, with every line reference read against the files. The source-ownership entries have no finding identifier.

Predicate ownership:

- `f-002` — `tests/test_definition.property.l1.py` calls only `assert_owned_path_outside_the_alphabet_is_rejected()` (`outcomeeng_testing/harnesses/evals.py:131`), which applies Hypothesis `given` at lines 140–141 and delegates the rejection check to `_assert_owned_path_rejected` (line 158). The property's invariant lives in the harness rather than lexically in the linked test, as the Property section of `spx/31-outcomeeng.enabler/31-verification.enabler/31-test-verification.enabler/21-evidence-types.pdr.md` requires. Settled when the invariant and its assertion sit in the linked test and the harness owns only seed selection, run count, replay, and diagnostics.
- `f-005` — `tests/test_ci_triggers.mapping.l1.py` calls only `assert_ci_policy_controls_trigger_contribution` and `assert_universal_paths_always_contribute` (`outcomeeng_testing/harnesses/ci_triggers.py:111` and `:125`), which own the mapping predicates. Settled when the linked test states each mapping's expectation and assertion over observations the harness exposes.
- `f-006` — `tests/test_ci_triggers.property.l1.py` calls only `assert_minimization_preserves_coverage` and `assert_minimization_is_a_subset_of_its_input` (`outcomeeng_testing/harnesses/ci_triggers.py:256` and `:269`); `_minimization_property` (line 285) applies `given` at lines 293–294 and carries both invariants. Settled on the same condition as `f-002`.
- `f-007` — the five tests in `tests/test_ci_triggers.compliance.l1.py` call only `assert_*` functions of `outcomeeng_testing/harnesses/ci_triggers.py` (lines 135, 188, 201, 221, and 241), which own the exit-code and path-list predicates. Settled when each linked test asserts the exit code and path list itself.
- `f-008` — the 11 tests in `tests/test_eval_harness.compliance.l1.py` call only `assert_*` functions of `outcomeeng_testing/harnesses/eval_harness.py` (lines 41–266), which hold 32 `assert` and `pytest.raises` sites. Settled when those sites sit in the linked tests and the harness exposes fixture paths, handles, and observations only.
- `f-010` — the seven tests in `tests/test_report.compliance.l1.py` call only `assert_*` functions of `outcomeeng_testing/harnesses/eval_report.py` (lines 64–240), which hold 43 `assert` sites. Settled on the same condition as `f-008`.
- `f-011` — the single test in `tests/test_history.compliance.l1.py` calls `assert_history_compliance()` (`outcomeeng_testing/harnesses/eval_history.py:200`), which runs twelve private `_assert_*` checks (lines 61–238), so one test result stands for twelve compliance checks. Settled when each check is a linked test that owns its predicate.

Test-owned data:

- `f-016` — `outcomeeng_testing/harnesses/producer_section_prompt.py` declares author-chosen payloads and expected outputs at lines 31–47: `SECTION_NAME` (line 36), `SELECTED_RULE`, `UNRELATED_RULE`, `NESTED_STEP_BODY`, `STALE_PROMPT`, and `PRODUCER_RELATIVE_PATH`, which names the real shipped skill `dist/claude/spec-tree/skills/audit-adr/SKILL.md`. `tests/test_producer_prompt.conformance.l1.py` asserts on them. The test-infrastructure decision admits no bare string as a fixture and assigns expected outputs and edge-case sets to source contracts or generators. Settled when those values come from a generator or from a whole-payload fixture read by path, and no evidence depends on the content of a shipped skill.
- `seq 69` — `make_changed_paths_file_cases` (`outcomeeng_testing/evals/factories.py:447–469`) hand-picks five changed-paths file contents and the paths each must yield, and `make_changed_paths_file_error_cases` (line 472) hand-picks three contents that must be rejected, from author-chosen constants at lines 73–80 (`DEFAULT_CI_CHANGED_PATH`, `DEFAULT_CI_RENAMED_PATH`, `DEFAULT_CI_COPIED_PATH`, `DEFAULT_CI_WHITESPACE_PATH`, `DEFAULT_CI_TABBED_PATH`, `DEFAULT_CI_MALFORMED_STATUS_ROW`, and the `M`, `R100`, and `C100` status tokens). `spx/13-infrastructure.enabler/25-eval-harness.enabler/21-ci-execution.enabler/tests/test_ci_execution.mapping.l1.py` iterates both sets. Every case line and constant matches base commit `81e46263f15d3489378cda7f808fcf84757ccee4`; the `outcomeeng/changes#170` diff changes only the consuming predicate, which sits in that linked test. The git name-status row grammar `outcomeeng_evals/ci_plan.py` parses — the status codes it names in `SIMPLE_GIT_STATUS_CODES`, `RENAMED_GIT_STATUS_PREFIX`, and `COPIED_GIT_STATUS_PREFIX`, and a path alphabet — is a source-owned domain the cases do not derive from. Settled when the accepted and rejected rows come from a generator over that grammar, with the expected paths derived from each generated row's construction rather than listed beside it.

Oracle independence (warning):

- `f-019` — `owned_path_violating_characters` (`outcomeeng_testing/generators/evals.py:64`) filters its candidates through `OWNED_PATH_ALPHABET.fullmatch` (line 75), the loader's own acceptance pattern, which rejected case 42 of `spx/31-outcomeeng.enabler/31-verification.enabler/31-test-verification.enabler/21-evidence-types.pdr.md` names. A widened alphabet narrows the searched domain in step, so the property cannot expose the widening. Settled when the generator's violating domain derives from a source independent of the loader's pattern.

Source ownership — each module below spells a value another owner declares:

- `outcomeeng_testing/harnesses/eval_report.py` (lines 71–73, 104–105, 174–175, and 205) spells the result-payload keys `model`, `max_budget_usd`, and `timeout_seconds` that `outcomeeng_evals/report.py` exports as `RESULT_MODEL_KEY`, `RESULT_MAX_BUDGET_USD_KEY`, and `RESULT_TIMEOUT_SECONDS_KEY`.
- `outcomeeng_testing/harnesses/eval_history.py` (lines 97, 127–135, 172–174, and 234–235) spells the history-row keys `model`, `max_budget_usd`, and `timeout_seconds` that `outcomeeng_evals/history.py` exports as `HISTORY_MODEL_FIELD`, `HISTORY_MAX_BUDGET_USD_FIELD`, and `HISTORY_TIMEOUT_SECONDS_FIELD`.
- `outcomeeng_testing/harnesses/evals.py:118` and `outcomeeng_testing/harnesses/ci_triggers.py:95` write the prompt placeholder `{case_id}` that `outcomeeng_evals/cli/commands/run.py` exports as `CASE_ID_PLACEHOLDER`.
- `outcomeeng_evals/ci_execution.py` spells the `run` command's options `--plugin-dir` (`PLUGIN_DIR_FLAG`), `--workers` (in `CI_RUN_SETTING_OPTIONS`), and `--case-id` (`CASE_ID_FLAG`) beside `outcomeeng_evals/cli/commands/run.py`, which declares them as `PLUGIN_DIR_OPTION`, `WORKERS_OPTION`, and `CASE_ID_OPTION`. Importing the `run` command module into `ci_execution` closes an import cycle: `outcomeeng_evals/cli/__init__.py` imports the `ci` command, which imports `ci_execution`.

A Python owner's value is settled when every source, test, and test-infrastructure module imports it from the module that declares it; the `ci_execution` duplicates settle when one module below the CLI package owns the `run` command's option names and both the command and `ci_execution` import them.

**Impact**: the node declares `malleability: spec`, under which Passing requires Validate, reachability tests, and a result for every tagged assertion, and no evidence audit, so these findings gate no merge. Harness-held predicates fail the predicate-inversion check the test-infrastructure decision names — inverting one changes the harness, not the linked test — so a linked test does not show what it proves. `f-016`, `seq 69`, and `f-019` leave three assertions whose case source or oracle is not independent of the author or the code under test. A change to any source-owned value above leaves a restated copy that the evidence compares against in place of the owner's value. An `implementation` malleability makes the evidence audit a merge gate, and each finding above then blocks.

**Settlement condition**: every finding above meets its own settlement condition, and a test-evidence audit of `spx/13-infrastructure.enabler/25-eval-harness.enabler` raises none of these four classes.
