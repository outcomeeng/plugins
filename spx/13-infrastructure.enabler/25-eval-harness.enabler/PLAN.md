# Eval Harness Refactor Plan

Coordination notes for the refactor that moves `[eval]` evidence from a pytest-collectable model to a dedicated CLI with per-eval directories, and extracts the eval runner into its own marketplace-independent Python package.

## Decisions confirmed

1. **Eval runner is its own Python package: `outcomeeng_evals`.** Generic, marketplace-independent, the same role pytest plays for `[test]` evidence. `outcomeeng/evals/` is deleted; all runner code moves to `outcomeeng_evals/`. The `outcomeeng_` prefix is namespace; the contents encode nothing marketplace-specific.
2. **Definition format: TOML.** Each eval directory carries an `eval.toml` declaring `title`, `cases`, `prompt`, `threshold`, `trials`. Python escape hatch (a `script = "generator.py"` field) is deferred until an eval genuinely needs programmatic case generation or custom grading.
3. **`spx/15-test-language.adr.md` is amended in place** to scope its decision to `[test]` evidence and pytest. A new sibling ADR — `spx/16-evidence-execution-lanes.adr.md`, modeled on leoherd's `spx/18-test-evidence-architecture.adr.md` — declares the lanes themselves (pytest for `[test]`, `outcomeeng_evals` CLI for `[eval]`, future lanes named explicitly).
4. **CLI framework: Click.** `outcomeeng_evals` exposes subcommands (`run`, `history`, `view`, `discover`) through Click. `click>=8.0` joins the marketplace's runtime dependencies.
5. **Package layout: light hexagonal.** Inside `outcomeeng_evals/`, a `cli/` subdirectory holds Click commands and wiring; the rest stays flat. No premature `ports/`/`runners/`/`models/` split.
6. **Fakes ship inside `outcomeeng_evals.testing`.** `StubModelRunner`, `RecordingRunner`, and result/case factories live in a subpackage of the runner itself, so external consumers of `outcomeeng_evals` get test helpers without depending on `outcomeeng_testing`. Mirrors pytest's pattern.
7. **`outcomeeng_testing/evals/` holds marketplace-specific eval helpers**: slice-specific factories, link-integrity validators, anything that depends on the marketplace's spec tree.
8. **Single `pyproject.toml`.** All three packages (`outcomeeng`, `outcomeeng_testing`, `outcomeeng_evals`) build from the existing `pyproject.toml`. Split into independent uv projects only when `outcomeeng_evals` is published to PyPI or the dependency surfaces genuinely diverge.
9. **`spx/13-infrastructure.enabler/25-eval-harness.enabler/` stays flat as a spec node.** No sub-enablers in this round. If the spec grows past `/decomposing`'s threshold during authoring, split then.
10. **Link-integrity gate for `[eval]` links.** A new validator under `outcomeeng/scripts/` (or extension of an existing one) walks `spx/**/*.md` and asserts every `[eval](path)` resolves to an existing `eval.toml`. Wired into `just check`. Mirrors leoherd's `spx validation markdown` discipline.
11. **Two sequential `/applying` runs.** First on this node (the harness spec); then on the slice migration at `spx/43-typescript.enabler/25-typescript-standards.enabler/25-typescript-tests.enabler/32-test-data-ownership.enabler/`. Smaller diffs, cleaner audit gates.
12. **Test files for `outcomeeng_evals` stay under `spx/13-infrastructure.enabler/25-eval-harness.enabler/tests/`.** Spec-tree co-location wins; the runner is verified by tests next to its spec. A future extraction of `outcomeeng_evals` into its own repo takes those tests along.

## Python package topology

```
repo-root/
├── outcomeeng/                       # marketplace-specific runtime
│   ├── scripts/                      # validate_plugins, build_plugins, eval-link validator
│   └── …                             # NO eval code here (current outcomeeng/evals/ is deleted)
├── outcomeeng_evals/                 # NEW: generic eval runner, marketplace-independent
│   ├── __init__.py
│   ├── case.py                       # Case, ExpectedElement, load_cases
│   ├── definition.py                 # EvalDefinition + TOML loader (new)
│   ├── grader.py                     # extract_verdict, grade (deterministic)
│   ├── history.py                    # append_history_row (new)
│   ├── report.py                     # serialize_result, write_json_report, write_html_report
│   ├── runner.py                     # ModelRunner Protocol + ClaudeCliRunner
│   ├── suite.py                      # TrialResult, CaseOutcome, SuiteResult, run_suite
│   ├── cli/                          # Click CLI
│   │   ├── __init__.py               # `main` Click group
│   │   ├── commands/
│   │   │   ├── run.py                # `outcomeeng-evals run <path>`
│   │   │   ├── history.py            # `outcomeeng-evals history <path>`
│   │   │   ├── view.py               # `outcomeeng-evals view <path>`
│   │   │   └── discover.py           # `outcomeeng-evals discover <root>`
│   │   └── wiring.py                 # concrete adapters (ClaudeCliRunner factory, …)
│   └── testing/                      # shipped with the runner
│       ├── __init__.py
│       ├── fakes.py                  # StubModelRunner, RecordingRunner
│       └── factories.py              # make_case, make_trial_result, make_suite_result
└── outcomeeng_testing/                # marketplace-scoped test helpers
    └── evals/                        # eval-specific marketplace helpers
        ├── __init__.py
        └── link_integrity.py         # spx/[eval](path) link walker (used by validator script)
```

Import direction (one-way, mirrors leoherd's ADR 19):

- `outcomeeng_evals` imports neither `outcomeeng` nor `outcomeeng_testing`.
- `outcomeeng` may consume `outcomeeng_evals`.
- `outcomeeng_testing` may consume both.
- Runtime packages never import testing packages.

CLI entry point: `[project.scripts]` in `pyproject.toml` adds `outcomeeng-evals = "outcomeeng_evals.cli:main"`.

## Per-eval directory layout

```
spx/{path}/{node}.enabler/
├── {slug}.md                              # spec: [eval](evals/{rule}/eval.toml)
├── tests/                                 # pytest [test] evidence (unchanged)
│   └── …
└── evals/
    └── {rule}/                            # one directory per [eval] assertion
        ├── eval.toml                      # durable: definition (committed)
        ├── cases.jsonl                    # durable: case data (committed)
        ├── prompt.md                      # durable: prompt template (committed)
        ├── history.jsonl                  # durable: summary per run (committed, append-only)
        └── runs/                          # ephemeral: gitignored
            ├── {timestamp}.json
            └── {timestamp}.html
```

`history.jsonl` is append-only. Each line carries: `timestamp`, `schema_version`, `git_sha`, `passed`, `pass_rate`, `cases_total`, `cases_passed`, `total_cost_usd`, `total_duration_ms`, `transcript` (relative path to the run JSON under `runs/`).

`eval.toml` schema:

```toml
title = "shared-test-owned-constant-bag"
cases = "cases.jsonl" # relative to eval.toml
prompt = "prompt.md" # relative to eval.toml
threshold = 0.85 # default 0.85 if omitted
trials = 1 # default 1 if omitted
```

## Scope

### What changes

- **ADRs**:
  - Amend `spx/15-test-language.adr.md` — narrow scope to `[test]` evidence and pytest. Title may shift from "Test Language Selection" to a tighter framing.
  - Author new `spx/16-evidence-execution-lanes.adr.md` — declares the lanes (pytest for `[test]`, `outcomeeng_evals` CLI for `[eval]`, future lanes named explicitly when added). Modeled on leoherd's `spx/18-test-evidence-architecture.adr.md`.
- **Eval-harness spec** (`eval-harness.md` in this directory): drop assertions that reference pytest collectables; add CLI contract, TOML schema, per-eval layout invariants, `history.jsonl` append-only invariant, `runs/` gitignored invariant, link-integrity guarantee.
- **Methodology references**:
  - `plugins/spec-tree/skills/understanding/references/assertion-types.md` — rewrite the `[eval]` paragraph to describe the per-eval directory and `eval.toml`-as-target convention. The current text still implies a pytest file.
  - `plugins/spec-tree/skills/understanding/references/node-types.md` — extend `<common_structure>` to list `evals/` alongside `tests/` as a per-node directory.
- **Python implementation**:
  - Delete `outcomeeng/evals/` entirely.
  - Create `outcomeeng_evals/` package with the layout above.
  - Move `case.py`, `grader.py`, `report.py`, `runner.py` (production parts only), `suite.py` from `outcomeeng/evals/` to `outcomeeng_evals/`. Adjust internal imports.
  - Move `StubRunner`, `RecordingRunner` (and `StubModelRunner` if renamed) from runtime code into `outcomeeng_evals/testing/fakes.py`. Move test factories into `outcomeeng_evals/testing/factories.py`.
  - New: `outcomeeng_evals/definition.py` — `EvalDefinition` dataclass, `load_definition` reading TOML via stdlib `tomllib`, paths resolved relative to the TOML file.
  - New: `outcomeeng_evals/history.py` — `append_history_row` writer; row schema fixed in the eval-harness spec.
  - New: `outcomeeng_evals/cli/` — Click group + four subcommand modules + `wiring.py` for concrete adapters. The `main` group is the entry point.
  - Refactor: `suite.run_suite` accepts an `EvalDefinition` directly so the CLI never re-implements path resolution.
  - Refactor: existing l1 meta-test imports (`from outcomeeng.evals.* import …`) become `from outcomeeng_evals.* import …`. Fakes imports become `from outcomeeng_evals.testing.fakes import …`.
- **`pyproject.toml`**:
  - Add `outcomeeng_evals` to `[tool.hatch.build.targets.wheel].packages`.
  - Add `click>=8.0` to runtime dependencies.
  - Add `[project.scripts] outcomeeng-evals = "outcomeeng_evals.cli:main"`.
- **`outcomeeng/scripts/` link validator**: new script (e.g., `validate_eval_links.py`) that walks `spx/**/*.md`, finds every `[eval](path)`, asserts the target resolves to an existing `eval.toml`. Wired into `just check`.
- **`.gitignore`**: add `**/evals/*/runs/`.
- **`just` recipes**: add `just eval-run <path>`, `just eval-all`, `just eval-history <path>` (final names defer to the Justfile's existing patterns).

### What stays

- The five `[eval]` evidence mechanism additions to the methodology (assertion-types.md mention, `spx/15-spec-coverage.adr.md` amendment, JSON schema version contract) — all stay unchanged.
- The `CLAUDECODE` env strip, per-trial metadata capture, variance reporting, cost summary, and parallel-case ordering — all preserved in the new package.
- All existing l1 meta-tests in `spx/13-infrastructure.enabler/25-eval-harness.enabler/tests/` — moved to the new import paths but the test logic stays.
- The case data, prompt template, and verdict-format expectations for the slice — unchanged in content; only their disk layout moves.

### What gets deleted in the slice migration (phase 2)

- `spx/.../32-test-data-ownership.enabler/tests/test_shared_constant_bag.eval.l3.py` — the pytest collectable.
- `spx/.../32-test-data-ownership.enabler/tests/shared_constant_bag.eval.cases.jsonl` — moves to `evals/shared-constant-bag/cases.jsonl`.
- `spx/.../32-test-data-ownership.enabler/tests/shared_constant_bag.prompt.md` — moves to `evals/shared-constant-bag/prompt.md`.
- `.spx/evals/transcripts/shared_constant_bag.{html,json}` — runs now land under the per-eval `runs/` directory.

## Phase 1: `/applying` on this node

Target: `spx/13-infrastructure.enabler/25-eval-harness.enabler/`

### Declare gate

- Amend `spx/15-test-language.adr.md` in place.
- Author new `spx/16-evidence-execution-lanes.adr.md`.
- Rewrite `eval-harness.md` assertions to match the new contract (TOML schema, CLI surface, per-eval layout, `history.jsonl`, `runs/` gitignored, link-integrity guarantee, `outcomeeng_evals` package boundary).
- Update `plugins/spec-tree/skills/understanding/references/assertion-types.md` and `node-types.md` to match.
- Audits: `/auditing-product-decisions` on both ADRs (the amendment and the new sibling); `/aligning` on the rewritten spec and methodology references.

### Spec gate

- New l1 meta-tests in `tests/`:
  - `test_definition.scenario.l1.py` — TOML parse, path resolution relative to the TOML file, default values, missing-field errors.
  - `test_history.scenario.l1.py` — append-only behavior, schema row, file creation, atomicity considerations.
  - `test_cli.scenario.l1.py` — Click dispatch, exit codes for `run`/`history`/`view`/`discover`, path resolution via `discover`.
  - `test_link_integrity.scenario.l1.py` — link walker recognizes `[eval](path)`, resolves to existing `eval.toml`, fails on broken links.
- Existing tests (`test_eval_harness.scenario.l1.py`, `test_report.scenario.l1.py`, `test_runner.scenario.l1.py`) keep their assertions; imports migrate to `outcomeeng_evals.*` and `outcomeeng_evals.testing.fakes.*`.
- Audit: `/auditing-python-tests`.

### Apply gate

- Implementation as listed under "What changes" above.
- `mypy --strict` and `ruff check` clean across `outcomeeng_evals/` and `outcomeeng_testing/evals/`.
- `just check` passes, including the new `[eval]` link integrity step.
- Audit: `/auditing-python`.

## Phase 2: `/applying` on the slice migration

Target: `spx/43-typescript.enabler/25-typescript-standards.enabler/25-typescript-tests.enabler/32-test-data-ownership.enabler/`

### Declare gate

- Update `[eval]` link in `test-data-ownership.md` from `tests/test_shared_constant_bag.eval.l3.py` to `evals/shared-constant-bag/eval.toml`.
- Audit: `/aligning`.

### Spec gate

- Create `evals/shared-constant-bag/` with `eval.toml`, `cases.jsonl` (moved), `prompt.md` (moved), `history.jsonl` (empty initially).
- Delete the pytest collectable `tests/test_shared_constant_bag.eval.l3.py`.
- The link integrity validator confirms the new `[eval]` link resolves.
- Audit: `/aligning` confirms the per-eval directory matches the layout invariant declared in the eval-harness spec.

### Apply gate

- Run the eval through the new CLI: `outcomeeng-evals run spx/.../32-test-data-ownership.enabler/evals/shared-constant-bag/eval.toml`.
- First run populates `history.jsonl` with one row and writes `runs/{timestamp}.{html,json}`.
- Confirm the HTML viewer renders the same data shape as before the refactor.

## Open items

- **Just recipe names**: confirm `just eval-run` vs. `just eval` aligns with the existing Justfile pattern.
- **Default model selection**: `claude --print` uses the user's default model. Should `eval.toml` carry an optional `model` field so an eval can pin against a specific model for reproducibility? Worth considering during phase 1 spec authoring; defer until a real need arises.
- **Concurrent eval runs**: the harness already supports `--workers` for parallelism within a suite. The CLI's `run --all` could also parallelize across suites. Defer past phase 1; today's use case is one eval at a time.
- **CI integration**: a scheduled CI workflow that runs `outcomeeng-evals run --all` and posts results is out of scope for both phases. The CLI's exit codes make this trivial to add later.
- **Independent uv project for `outcomeeng_evals`**: keep single `pyproject.toml` until/unless `outcomeeng_evals` is published to PyPI or the dependency surfaces diverge. Revisit on publication.
- **`outcomeeng_evals.testing` as a public surface**: the runner ships fakes and factories, but the public-API contract for that subpackage is not yet declared. Decide whether `outcomeeng_evals.testing` is a stable surface (versioned with the runner) or an internal helper (no compatibility guarantees) when the first external consumer appears.
