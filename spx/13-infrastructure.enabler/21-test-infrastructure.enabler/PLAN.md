# Plan: complete the quality-gate node and remove it from EXCLUDE

Coordination note for a three-phase effort that lands a CI quality gate and
brings `spx/13-infrastructure.enabler/21-test-infrastructure.enabler` (and its
child) to a passing, non-excluded state, then closes the PDR test-infrastructure
conformance gap. Each phase is its own PR. Reconcile this note against the specs,
decisions, tests, and `git log` before acting — it is coordination, not truth.

Approved scope: Phases 1 + 2 + 3. CI fidelity: full `just check`.

## Governing context

- Node charter: the unified quality gate (`just check`), verified before changes
  reach `main`. `just check` = `uv run python -m outcomeeng.validation`; the step
  list is the `STEPS` tuple in `outcomeeng/validation/_steps.py`:
  build-skills → dist-diff → build-orchestration → fmt-check(dprint) → ruff →
  manifests → skills → skill-injection → docs-check → markdown → pytest.
- CI toolchain for full `just check`: uv + Python 3.14 + dprint + git + the
  `claude` CLI (the `manifests` step runs `claude plugin validate` — confirmed in
  CI to need no auth) + the `@outcomeeng/spx` CLI (the `markdown` step runs
  `spx validation markdown`; `spx` is a globally pnpm-linked sibling repo on dev
  machines but a published npm package `@outcomeeng/spx` for CI). All four CLI
  versions are pinned in `.github/workflows/check.yml` and tracked by Renovate.
- Precedent for a workflow-conformance test: `spx/32-distribution.enabler/tests/
  test_distribution_workflow.compliance.l1.py` parses `.github/workflows/*.yml`
  with `yaml` + `tomllib`.
- EXCLUDE entries to remove: `13-infrastructure.enabler/21-test-infrastructure.enabler`
  (Phase 1) and `13-infrastructure.enabler/21-test-infrastructure.enabler/21-python-code-quality.enabler`
  (Phase 2).

## Phase 1 — CI gate + un-exclude the parent (session core goal)

- Declare: add a compliance assertion to `test-infrastructure.md` — ALWAYS the
  marketplace CI runs `just check` on `pull_request` and push-to-`main` as a
  required status check; a gate failure blocks merge
  (`[test](tests/test_ci_gate.compliance.l1.py)`).
- Re-home the pre-existing assertion (decided during Phase 1): the prior
  assertion "`just check` runs all quality steps defined by child enablers and
  exits 0 on a clean main branch" was redundant and ill-formed (the node's only
  child, `21-python-code-quality.enabler`, does not define the build/manifest/
  markdown steps), and a pytest asserting "`just check` exits 0" would recurse
  because pytest is itself a gate step. Its truth is re-homed: STEPS composition
  to `spx/15-validation.enabler/65-gate.enabler`, the static-analysis steps to
  the `21-python-code-quality.enabler` child, and "the gate passes before
  reaching `main`" to the new CI-gate assertion (carried operationally by the CI
  workflow). The assertion and its planned `test_test_infrastructure.compliance.l2.py`
  are therefore dropped, not deferred.
- Spec/apply (`/applying`): write only `tests/test_ci_gate.compliance.l1.py`
  (parse `.github/workflows/check.yml`: `on.pull_request`, push-to-`main`, a
  `just check` / `uv run python -m outcomeeng.validation` invocation, the Python
  version against `requires-python`, and no soft-passed step). Implement
  `.github/workflows/check.yml`.
- Remove the parent from `spx/EXCLUDE`.
- Audit gates: `test-evidence-auditor`, `python-code-auditor`, `python-test-auditor`,
  `/aligning` on the spec.
- Manual admin step (state-changing, needs explicit user action): mark the new
  check `required` in branch protection via `gh api`. The `[test]` covers the
  workflow's existence and triggers, not the repo-level required-check setting.
- Gate: `just check` green; PR via `/pr`.

## Phase 2 — complete the child `21-python-code-quality.enabler`

- Add `mypy --strict` and `pyright` steps to `STEPS` in
  `outcomeeng/validation/_steps.py`. This touches `spx/15-validation.enabler/65-gate.enabler`
  (its compliance test pins the step list) — contextualize and update that node's
  assertion + test in the same change.
- Fix all mypy/pyright/ruff findings across `outcomeeng*`. Known: mypy error at
  `outcomeeng/validation/_engine.py:113` (signal-restore loop, in the gate node's
  ISSUES.md) and the ruff drift in `spx/ISSUES.md` (5 errors + format on 4 files).
- Write `tests/test_python_code_quality.conformance.l2.py` and
  `tests/test_python_code_quality.compliance.l2.py`.
- Remove the child from `spx/EXCLUDE`. Resolve the `spx/ISSUES.md` ruff entry and
  the gate node's mypy ISSUES entry.
- Audit gates + `just check` green; PR.

## Phase 3 — PDR test-infrastructure subtree conformance

Resolves this node's `ISSUES.md`. `spx/15-test-infrastructure.pdr.md` mandates
`infrastructure → testing → {generators, fixtures, harnesses}` with those exact
slugs. The tree has no `testing` node; `outcomeeng_testing/` ships 20 harness
modules, 2 generators, and a fixtures tree with no governing node.

- STRUCTURAL FORK to resolve first (via `/refactoring` + a structured question):
  the current `21-test-infrastructure.enabler` charter is the *quality gate*, not
  the PDR's harness/generator/fixture categories — the names collide. Decide
  whether the PDR `testing → {generators, fixtures, harnesses}` subtree is a new
  node under `spx/13-infrastructure.enabler` distinct from the quality-gate node,
  or a restructure/rename of the existing node. The "exactly three children"
  constraint conflicts with keeping `python-code-quality` as a sibling.
- Author the subtree (`/authoring`) with per-category assertions; establish
  traceability from each `outcomeeng_testing/{harnesses,generators,fixtures}`
  artifact to its category node.
- Audit gates (`/auditing-python-architecture`, `test-evidence-auditor`, `/aligning`) + green; PR.
