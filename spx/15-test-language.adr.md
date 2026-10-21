# Test Language Selection

Python (pytest) is the language and runner for all `[test]` evidence in the spec tree. Test files follow `test_{subject}.{evidence}.{level}[.{runner}].py` and live under each node's `tests/` directory. The `[test]` lane is one of the evidence-execution lanes declared in [`spx/31-outcomeeng.enabler/31-verification.enabler/14-verification.pdr.md`](spx/31-outcomeeng.enabler/31-verification.enabler/14-verification.pdr.md); this decision selects its language and runner. `[eval]` evidence lives in a separate lane this decision does not govern.

## Rationale

Two categories of artifact produce `[test]` evidence: infrastructure scripts (validation, distribution, xml-spacing, eval-harness internals), which are Python tested with pytest; and skill behavior verified through observable side effects — file outputs, structured verdicts, link-integrity checks — where pytest verifies the harness contract and the lane stays deterministic because the grader is code, not an LLM. LLM-driven skill behavior, where the assertion is about what the model concludes rather than what observable artifact it produces, belongs in the `[eval]` lane. Implementation code in the marketplace is Python, the marketplace ships a single quality gate, and orphaned test files that no runner collects create phantom evidence — a single language and runner makes collection deterministic. Spec-tree node directories are kebab-case while Python modules require snake_case imports, so one file-naming rule reconciles both. A single runner spanning all evidence mechanisms collapses cost profiles into one gate; shell runners lose import-mode discovery and parametrization; per-node runner configuration drifts when a node moves.

A pytest run creates temp files through `tempfile`, through `tmp_path`, and through every harness, fixture, and shipped script under test. Without a bound, pytest retains `tmp_path` directories in the user temp folder across runs, and a run killed before teardown leaves its files behind. One run root under the worktree the run executes from bounds every temp file the run creates: environment variables carry the root to child processes without the creating code naming it, the run removes the root when it ends, and the next run sweeps any root a killed run left. A Git ceiling at the run root keeps Git started in a temp directory from resolving the enclosing worktree as its repository.

## Verification

- ALWAYS: every temp file and directory that a test, a harness, a fixture, or a shipped script under test creates lives under one run root that the pytest run creates; the run removes that root when it ends, whether its tests pass, fail, or time out
- ALWAYS: before its first test starts, the run creates its run root under `.spx/worktree/test-runs/` in the worktree it runs from, and points `TMPDIR` and Python's default temp directory at that root, so a temp file created in the test process or in any process it starts lands under that root without the creating code naming it
- ALWAYS: before its first test starts, the run sets `GIT_CEILING_DIRECTORIES` to its run root, so Git started in a temp directory never resolves the enclosing worktree as its repository
- ALWAYS: before its first test starts, a pytest run removes every run root left under `.spx/worktree/test-runs/` in its own worktree, and never reads or removes a path outside that worktree
- NEVER: pytest keeps a `tmp_path` directory after its test ends, whether the test passed or failed

### Audit

- ALWAYS: use Python (pytest) for all `[test]` evidence in the spec tree — the quality gate runs a single runner for this lane ([audit])
- ALWAYS: reference Python test files with a `[test]` link whose path matches `tests/test_{subject}.{evidence}.{level}.py` ([audit])
- ALWAYS: `pytest.ini` (or `pyproject.toml` `[tool.pytest.ini_options]`) declares `testpaths` covering `spx/` so pytest discovers every `test_*.py` under any `spx/**/tests/` directory ([audit])
- NEVER: use a non-pytest runner for `[test]` evidence in the spec tree — the lane is single-runner by decision ([audit])
- NEVER: route `[eval]` evidence through pytest as its primary execution surface — `[eval]` belongs to the lane governed by [`spx/31-outcomeeng.enabler/31-verification.enabler/14-verification.pdr.md`](spx/31-outcomeeng.enabler/31-verification.enabler/14-verification.pdr.md) ([audit])
- NEVER: reference a `[test]` link from a spec assertion to a path outside `spx/**/tests/` — co-location is mandatory for `[test]`-lane evidence ([audit])
