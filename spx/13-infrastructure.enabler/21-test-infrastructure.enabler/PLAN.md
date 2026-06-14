# Plan: quality-gate node — remaining operator step

The three-phase effort that landed the CI quality gate and brought
`spx/13-infrastructure.enabler/21-test-infrastructure.enabler` (and its child)
to a passing, non-excluded state is implemented. Reconcile this note against the
specs, decisions, tests, and `git log` before acting — it is coordination, not
truth.

- **Phase 1 — CI gate + un-exclude the parent**: complete. `tests/test_ci_gate.compliance.l1.py`
  and `.github/workflows/check.yml` exist; the parent is out of `spx/EXCLUDE`.
- **Phase 2 — complete `21-python-code-quality.enabler`**: complete. The child is
  out of `spx/EXCLUDE`; `mypy`/`pyright` package steps run in the gate.
- **Phase 3 — test-infrastructure governance inventory**: complete. The reworked
  `spx/15-test-infrastructure.pdr.md` governs harnesses, generators, and inert
  fixtures by naturally placed spec nodes. An inventory of every
  `outcomeeng_testing/{harnesses,generators,evals}` artifact confirmed each is
  governed by the node whose tests import it (no orphan infrastructure, no
  taxonomy-only nodes required), verified by the test-evidence audit.

## Remaining — operator-gated admin step (Phase 1 residue)

`main` carries no branch protection, so the CI gate (`check.yml`) is not yet a
required status check. Marking it `required` is a state-changing repository-config
action that needs an explicit operator instruction; the `[test]` covers the
workflow's existence and triggers, not the repo-level required-check setting.

- Operator action: mark the `check` workflow `required` on `main` (via `gh api`
  or repository settings), so a red gate blocks merge server-side.
