# Issues: Test Infrastructure Enabler

## 1. Test-infrastructure governance inventory is incomplete

`spx/15-test-infrastructure.pdr.md` requires every test harness, generator, and
fixture to be governed by a naturally placed spec node. `outcomeeng_testing/`
ships harness modules, generators, and fixtures whose governing nodes should be
inventoried by following the evidence chain from spec assertion to test file to
imported artifact.

The gap is product-wide and unrelated to any single harness. `git_context.py`
surfaced it while adding hermetic session scenario tests.

**Required handling** (dedicated structural change):

- Inventory each `outcomeeng_testing/{harnesses,generators,fixtures}/` artifact.
- Identify the natural governing node for each artifact from the assertion, test,
  and import chain.
- Add or move assertions only where an artifact's behavior, policy, lifecycle, or
  reusable semantics are not already covered. Do not create category nodes solely
  for taxonomy.

Surfaced during the `fix/sessions-test-hermeticity` change review.

## 2. Gate-job-level soft-pass / skip is not covered by the workflow-contract test

`tests/test_ci_gate.compliance.l1.py` asserts no gate *step* carries
`continue-on-error`, a step-level `if:`, or a soft-passing `run:` shell, per the
`15-ci-gate.adr.md` NEVER rule (`a gate step is … soft-passed`). It does not
inspect the enclosing `check:` *job* for a job-level `if:` (which could skip the
gate on `pull_request`) or a job-level `continue-on-error` (which could let a
failed job report success). Today's `check.yml` carries neither, so nothing is
broken; a job-level condition would also surface in the `check.yml` diff under
review, so this is defense-in-depth rather than a silent hole.

**Resolution shape**: extend the `15-ci-gate.adr.md` NEVER rule and the node
assertion to cover the gate job as well as its steps, then add a job-level
assertion to `test_ci_gate.compliance.l1.py` (no `if`, no `continue-on-error` on
the `check` job dict). Surfaced by the changes-review on PR #139.
