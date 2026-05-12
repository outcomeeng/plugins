# Eval Harness: Deferred Items

Open items carried forward from the eval-harness refactor. None block the harness as shipped; each is a follow-up decision or enhancement.

## Just recipe naming

Confirm `just eval-run` vs. `just eval` aligns with the existing Justfile pattern when the eval recipes are added.

## Optional per-eval model pin

`claude --print` uses the user's default model. An optional `model` field in `eval.toml` would let an eval pin against a specific model for reproducibility. Defer until a real need arises.

## Cross-suite parallelism

The harness supports `--workers` for parallelism within a suite. `run --all` could also parallelize across suites. Defer; today's use case is one eval at a time.

## CI integration

A scheduled CI workflow that runs `outcomeeng-evals run --all` and posts results is not yet wired. The CLI's exit codes make this straightforward to add later.

Until CI owns the canonical appends, every developer-machine run appends a row to `history.jsonl`, which shows up as `git diff` noise. Staging discipline: do not stage `**/evals/**/history.jsonl` unless the commit's purpose *is* an eval run — restore it (`git checkout -- <path>`) before committing unrelated changes. The repo's `.gitattributes` marks these files `merge=union` so concurrent appends from different branches merge cleanly instead of conflicting; that covers merges, not the staging hygiene, which still wants the CI step (or a pre-commit guard) to fully solve.

## Independent uv project for `outcomeeng_evals`

`outcomeeng_evals` builds from the single repo `pyproject.toml`. Split into an independent uv project only when it is published to PyPI or its dependency surfaces diverge from the marketplace's.

## `outcomeeng_evals.testing` public-API contract

The runner ships fakes and factories under `outcomeeng_evals.testing`. Whether that subpackage is a stable, versioned surface or an internal helper with no compatibility guarantees is not yet declared. Decide when the first external consumer appears.

## Prompt-template placeholder validation

`_render_prompt` (in `outcomeeng_evals/cli/commands/run.py`) substitutes `{case_id}` and `{input_json}` and passes any other `{…}` run through verbatim. A typo like `{casse_id}` reaches the model as literal text with no warning. Validating placeholders — at `load_definition` time or at render time — would surface authoring errors before a paid run. The constraint: prompt templates legitimately contain literal `{` (JSON examples, code), so a validator must warn only on `{<identifier-shaped token>}` that is not one of the known keys, not on every brace. Defer until prompt-authoring mistakes actually bite.

## Partial-trial evidence in parallel-path errors

`_error_outcome` (in `outcomeeng_evals/suite.py`) replaces all of a case's trials with one synthetic `trial_index=0` failing trial when the worker raises. If trial 1 passed and trial 2 raised, the successful trial's evidence is lost from the report. A richer error outcome — successful trials kept, the error appended as the final trial — would preserve that evidence. Defer; today's runs use `trials_per_case = 1`, so the loss is moot until multi-trial parallel runs are common.
