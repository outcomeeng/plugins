---
id: 01a1e1d3-9613-7094-b04a-20716a8f5df5
---

# Eval Harness

PROVIDES a generic Python evaluation runner — the `outcomeeng_evals` package — that replays curated case sets through Claude Code skills and grades structured verdicts against expected fields
SO THAT spec assertions about LLM-driven skill behavior across any project consuming this marketplace
CAN carry eval evidence bounded by per-eval expected-verdict structures declared in each case file, and gated by pass@k thresholds

## Assertions

### Test.Conformance: eval definitions

- [eval-toml-contract](tests/test_definition.conformance.l1.py): Each per-eval directory declares its contract through an `eval.toml` carrying `title`, `cases`, `prompt`, optional `threshold`, optional `trials`, and optional `model` defaulting to `sonnet`; `model = "inherit"` is rejected because eval evidence must not depend on the interactive session model, and the loader resolves `cases` and `prompt` paths relative to the TOML file's directory, as [the eval definition schema](contracts/eval-definition.schema.json) declares
- [producer-prompt-source](tests/test_producer-prompt.conformance.l1.py): Producer-coupled skill evals declare `prompt_source.kind = "producer-file"` for one whole skill or `prompt_source.kind = "producer-section"` for one named step, with a repository-relative producer path and an eval-directory-relative prompt template, so `outcomeeng-evals materialize-prompts` derives `prompt.md` from the complete producer or selected concern rather than a hand-copied simulation, per [spx/13-infrastructure.enabler/25-eval-harness.enabler/57-producer-coupled-skill-evals.adr.md](spx/13-infrastructure.enabler/25-eval-harness.enabler/57-producer-coupled-skill-evals.adr.md), with the `prompt_source` table [the eval definition schema](contracts/eval-definition.schema.json) declares
- [producer-files-source](tests/test_producer-files-prompt.conformance.l1.py): A composed-skill eval declares `prompt_source.kind = "producer-files"` with a non-empty, ordered, duplicate-free set of repository-relative whole-producer paths, and prompt materialization path-labels every complete producer in that order, with the `prompt_source` table [the eval definition schema](contracts/eval-definition.schema.json) declares
- [ci-selection-metadata](tests/test_definition.conformance.l1.py): Each `eval.toml` may declare CI-selection metadata — `plugin_dir`, `owned_paths`, `smoke_cases`, and `ci_policy` — so workflow planning selects the correct plugin runtime and narrows PR runs to affected suites and canary cases without changing local full-suite execution, with the types [the eval definition schema](contracts/eval-definition.schema.json) declares
- [owned-path-load](tests/test_definition.conformance.l1.py): An `owned_paths` entry loads when its body matches the source-owned path alphabet and its only glob is a trailing `/**`, by the `owned_paths` pattern [the eval definition schema](contracts/eval-definition.schema.json) declares

### Test.Compliance: definitions, prompts and links

- [owned-path-alphabet](tests/test_definition.compliance.l1.py): ALWAYS: the owned-path alphabet excludes every character the standard library reports as glob magic — evidence drawn from the alphabet proves only that the loader honors it, never that the alphabet is right, so an oracle outside the harness pins the contract the alphabet must keep
- [materialize-prompts](tests/test_materialize-prompts.compliance.l1.py): ALWAYS: the `outcomeeng-evals` CLI exposes `materialize-prompts`, which walks eval definitions under a root, writes generated prompts by default, and supports `--check` for drift detection without modifying files
- [eval-link-integrity](tests/test_link-integrity.compliance.l1.py): ALWAYS: link-integrity validation accepts an eval link in marketplace spec markdown only when it resolves to an existing `eval.toml` file under a sibling `evals/{rule}/` directory
- [test-link-integrity](tests/test_link-integrity.compliance.l1.py): ALWAYS: link-integrity validation accepts a test link in marketplace spec markdown only when it resolves to an existing pytest collectable (filename starts with `test_`, suffix `.py`) under a sibling `tests/` directory

### Test.Mapping: [format-suffix](tests/test_cli.mapping.l1.py)

The `run` CLI appends a format-instruction suffix, which declares the grader's two-step JSON-parse contract, to every rendered prompt before it passes the prompt to the model, so the model's structured-output behavior matches what the grader accepts.

| Case               | Rendered prompt                            | Prompt the model receives                              |
| ------------------ | ------------------------------------------ | ------------------------------------------------------ |
| every-trial-prompt | the prompt each trial of each case renders | that prompt, followed by the format-instruction suffix |

### Test.Mapping: [run-exit](tests/test_run-exit.mapping.l1.py)

The suite-level pass rate gates an exit-0 result against the threshold the eval definition declares, whose default sits next to the case set, so CI consumes the exit code rather than transcript text.

| Case            | Suite pass rate                      | Exit                 |
| --------------- | ------------------------------------ | -------------------- |
| meets-threshold | at or above the definition threshold | 0                    |
| below-threshold | below the definition threshold       | a non-zero exit code |

### Test.Mapping: [workers-range](tests/test_cli.mapping.l1.py)

The `run` CLI accepts a `--workers` value only inside the range `[1, 16]`; the upper bound caps concurrent `claude` subprocesses so a misconfigured worker count cannot fork-burst the Claude API, per [`spx/13-plugin-and-runtime-conventions.adr.md`](spx/13-plugin-and-runtime-conventions.adr.md).

| Case          | `--workers` value | Result        |
| ------------- | ----------------- | ------------- |
| below-minimum | below 1           | a usage error |
| above-cap     | above 16          | a usage error |

### Test.Mapping: [case-selection](tests/test_cli.mapping.l1.py)

The `run` CLI accepts repeatable `--case-id` selectors and runs only the named cases in case-file order, and it rejects a selector that resolves to no case in the suite.

| Case               | Selectors                                     | Result                                       |
| ------------------ | --------------------------------------------- | -------------------------------------------- |
| one-selector       | one `--case-id` naming a case of the suite    | only that case runs                          |
| repeated-selectors | several `--case-id` selectors in any order    | only the named cases run, in case-file order |
| unknown-selector   | a `--case-id` that names no case of the suite | the run is rejected                          |

### Test.Mapping: [subcommand-names](tests/test_cli.mapping.l1.py)

The `outcomeeng-evals` Click group exposes exactly these subcommand names in its help listing.

| Case                | Subcommand            |
| ------------------- | --------------------- |
| run                 | `run`                 |
| history             | `history`             |
| view                | `view`                |
| discover            | `discover`            |
| plan                | `plan`                |
| ci                  | `ci`                  |
| materialize-prompts | `materialize-prompts` |

### Test.Mapping: [history-row-versions](tests/test_cli.mapping.l1.py)

The `history` subcommand renders a complete summary for every version-1 history row, and the additive ceiling fields retain schema version 1.

| Case             | History row                                         | Rendered summary                      |
| ---------------- | --------------------------------------------------- | ------------------------------------- |
| without-ceilings | a version-1 row without the additive ceiling fields | complete                              |
| with-ceilings    | a version-1 row with the additive ceiling fields    | complete, and the row reads version 1 |

### Test.Mapping: [ci-planning](tests/test_cli.mapping.l1.py)

CI planning maps the changed paths of a PR to suites through each eval's `owned_paths`, and full mode runs every suite whose `ci_policy` is not manual.

| Case                       | Change                                             | Plan                                 |
| -------------------------- | -------------------------------------------------- | ------------------------------------ |
| owned-path-change          | a path an eval's `owned_paths` holds               | that suite's `smoke_cases`           |
| renamed-owned-path         | a rename onto a path an eval's `owned_paths` holds | that suite's `smoke_cases`           |
| harness-after-owned-path   | an owned path, then a harness path, in one PR      | the full suite                       |
| harness-change             | a path of the eval harness                         | the full suite                       |
| copied-harness-path        | a copy onto a path of the eval harness             | the full suite                       |
| test-harness-change        | a test harness of the eval harness                 | the full suite                       |
| test-generator-change      | a test generator of the eval harness               | the full suite                       |
| absolute-definition-change | an eval definition named by its absolute path      | the full suite                       |
| definition-change          | an eval definition                                 | the full suite                       |
| unrelated-change           | a path no eval owns and no harness holds           | no suite                             |
| full-mode                  | full mode, with one manual and one automatic eval  | the automatic eval's full suite only |

### Test.Property: owned paths and prompts

- [owned-path-complement](tests/test_definition.property.l1.py): An `owned_paths` entry never carries a character outside that alphabet — the rejected domain is the alphabet's open complement rather than an enumerable set of globs
- [producer-change-detection](tests/test_producer-prompt.property.l1.py): Producer-derived prompt materialization changes when any selected whole producer changes

### Test.Compliance: cases and grading

- [case-record](tests/test_eval-harness.compliance.l1.py): ALWAYS: each eval case is a JSONL record carrying an `id`, an input payload, and the expected structural verdict fields — the case file is the durable ground truth for the assertion that links to it, under the eval lane [`spx/31-outcomeeng.enabler/31-verification.enabler/14-verification.pdr.md`](spx/31-outcomeeng.enabler/31-verification.enabler/14-verification.pdr.md) declares
- [placeholder-render](tests/test_eval-harness.compliance.l1.py): ALWAYS: the prompt renderer substitutes `{case_id}` and `{input_json}` in a single forward pass, and passes any other `{token}` through as literal text — an identifier-shaped `{token}` that is not a recognized placeholder produces a stderr warning, so a template typo surfaces at render time rather than only as a downstream grading failure
- [json-grading](tests/test_eval-harness.compliance.l1.py): ALWAYS: graders parse the assistant response as a single JSON document — `json.loads()` on the raw response first, then a single retry on the response with one surrounding markdown code fence (no language tag or the `json` tag) stripped — and compare against each case's expected structural fields by recursive subset matching; prose interpretation never participates in the pass/fail decision
- [sentinel-matchers](tests/test_eval-harness.compliance.l1.py): ALWAYS: graders treat the sentinel strings `#string`, `#notnull`, and `#present` at expected-value positions as type/presence matchers — `#string` matches when actual is a string, `#notnull` matches when actual is not null, `#present` matches any value (including null) — so a case pins a field as present and of a type without specifying its value
- [pass-at-k](tests/test_eval-harness.compliance.l1.py): ALWAYS: each case is replayed `k >= 1` trials and counted as passing when the per-case threshold is met (default majority of trials) — non-determinism is bounded by pass@k
- [ordered-workers](tests/test_eval-harness.compliance.l1.py): ALWAYS: a `workers >= 1` knob parallelizes case execution through a bounded thread pool, and outcomes follow case-file order regardless of thread finish order — interleaving is invisible to downstream consumers
- [expected-list-bound](tests/test_eval-harness.compliance.l1.py): NEVER: the loader loads a case whose expectation contains a list longer than `MAX_EXPECTED_LIST_LENGTH` — `is_subset` matches expected lists against actual lists in O(expected × actual) time, so the loader rejects an oversized expectation with a clear error rather than running slowly

### Test.Compliance: runner and records

- [claude-invocation](tests/test_runner.compliance.l1.py): ALWAYS: the runner invokes Claude Code through `claude [--bare] --print --output-format json --no-session-persistence --settings '{"advisorModel":""}' --model <model> --plugin-dir <plugin-path>`, reads the assistant message from the parsed JSON envelope, and disables the Advisor server tool at this single model-process boundary; it passes `--bare` when `ANTHROPIC_API_KEY` is set to a non-empty value, and otherwise omits `--bare` and preserves the inherited environment, including `CLAUDE_CODE_OAUTH_TOKEN` when present; a caller forces the flag on or off by passing `bare=True` or `bare=False` to the constructor
- [claudecode-stripped](tests/test_runner.compliance.l1.py): ALWAYS: the subprocess environment passed to `claude` strips the `CLAUDECODE` marker before invocation — nested calls from inside a Claude Code session run as ordinary print-mode subprocesses, not as guarded interactive sessions
- [trial-metadata](tests/test_runner.compliance.l1.py): ALWAYS: every trial captures observability metadata — `duration_ms`, `total_cost_usd`, `input_tokens`, `output_tokens`, `cache_read_input_tokens`, `cache_creation_input_tokens`, `num_turns`, `stop_reason` — parsed from the claude JSON envelope; missing fields surface as `null` rather than fabricated zeros
- [trial-stability](tests/test_report.compliance.l1.py): ALWAYS: every case outcome carries `trial_pass_count`, `trial_count`, and `trial_pass_rate`, and the suite-level `trial_stability` block reports `mean_trial_pass_rate`, `stddev_trial_pass_rate` (null when fewer than two cases), and `min`/`max` pass rates — single-shot conclusions are never the only signal when `k > 1`
- [results-document](tests/test_report.compliance.l1.py): ALWAYS: every suite run serializes a JSON results document under each eval's `runs/{timestamp}.json` carrying a `schema_version`, the selected `model`, the configured per-trial `max_budget_usd` and `timeout_seconds`, the suite summary, a `cost_summary` aggregating trial-level cost, duration, and token counts — including the prompt-cache read and creation token totals — and per-case input, expectations, trial prompts, raw responses, parsed verdict JSON, grade reasons, and trial metadata, so failed cases remain inspectable without rerunning the LLM
- [json-authoritative](tests/test_report.compliance.l1.py): ALWAYS: the JSON results document is the authoritative artifact for downstream tooling; the sibling HTML viewer reads the same JSON payload (embedded in a `<script type="application/json">` tag for `file://` opens) and adds no fields beyond what the JSON contains
- [history-row](tests/test_history.compliance.l1.py): ALWAYS: every suite run appends one summary row to the per-eval `history.jsonl` carrying timestamp, schema version, git SHA, selected model, configured per-trial `max_budget_usd` and `timeout_seconds`, suite verdict, pass rate, case counts, total cost, total duration, the aggregate input, output, prompt-cache read, and prompt-cache creation token counts, and the run's transcript path; the file is the durable trend record

### Test.Compliance: execution surfaces

- [just-recipes](tests/test_eval-just-recipes.compliance.l1.py): ALWAYS: repository-local eval execution is exposed through Just recipes — `just eval`, `just eval-case`, and `just eval-node` — that wrap `uv run outcomeeng-evals run`, run node suites serially, read `plugin_dir` and `model` from each `eval.toml` unless `PLUGIN_DIR` or `EVAL_MODEL` overrides them, default to `model = "sonnet"`, `MAX_BUDGET_USD=0.75`, `WORKERS=1`, and `TIMEOUT_SECONDS=180`, and print the expanded command before execution so model and cost-affecting settings are visible
- [dispatch-only-trigger](tests/test_eval-workflow-triggers.compliance.l1.py): NEVER: the eval workflow declares a `pull_request`, `push`, or `schedule` trigger — `workflow_dispatch` is its only trigger, so CI starts an eval only when an operator dispatches it
- [dispatch-defaults](tests/test_eval-workflow-defaults.compliance.l1.py): ALWAYS: the eval workflow's dispatch inputs and runtime fallbacks for `max_budget_usd` and `timeout_seconds` take the defaults `outcomeeng_evals.settings` declares — a dispatched run spends no more than a local run by default

### Audit: authoring and execution

- auth-as-found: Agents use the provisioned authentication mode as found and do not ask the operator to add, remove, or switch authentication secrets for an eval run.
- local-history-restore: Developer-machine eval runs produce local `history.jsonl` appends that contributors restore before committing unrelated changes, while CI workflows own canonical baseline appends when wired.
- coupled-expectations: Every eval case carries at least two structurally coupled expectations — one on a verdict-level attribute (e.g., `status="rejected"`) and one on a finding-level attribute (e.g., `rule="X" present="true"`) — paired so that a hallucinated verdict status without a matching finding, or a matching finding without the correct verdict status, fails the case.
- bounded-invocation: No eval spawns a long-lived `claude` subprocess or a polling loop; each case is a single bounded invocation per [`spx/13-plugin-and-runtime-conventions.adr.md`](spx/13-plugin-and-runtime-conventions.adr.md).
- no-prose-grading: No grader grades a case by interpreting free-form LLM prose; structural verdict fields are the only source of pass/fail signal.
- l3-for-network: No eval case depends on the audited skill running over network or credentialed services without the `l3` level token; case level is the runner's escalation gate.

### Audit: artifacts and packaging

- schema-version-stable: The `schema_version` of the JSON results document or history row changes only with an incompatible contract change and a corresponding consumer migration; additive fields retain the current version so older artifacts remain readable by tolerant consumers.
- coupled-must-contain: No `must_contain` expectation is satisfied by a single rule-name attribute without a coupled verdict-status check; a single-attribute match is non-discriminating because a hallucinated finding mentioning the rule name passes it trivially.
- sentinel-paired: No case relies on a sentinel matcher (`#string`, `#notnull`, `#present`) as its only finding-level discriminator; every sentinel pairs with at least one coupled discriminating field — `severity` or `concern` — that pins a specific value.
- no-runs-directory: No `runs/` directory under any `evals/{rule}/` is committed — full transcripts are per-developer ephemeral artifacts; `history.jsonl` is the shared trend record.
- no-runtime-fakes: No shipped runtime package holds a test-only fake — runtime imports never pull in test infrastructure.
