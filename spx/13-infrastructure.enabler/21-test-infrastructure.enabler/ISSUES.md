# Issues: Test Infrastructure Enabler

## 1. Canonical test-infrastructure category subtree is absent

`spx/15-test-infrastructure.pdr.md` mandates the canonical subtree
`infrastructure → testing → {generators, fixtures, harnesses}` with those exact
slugs, and requires every test-infrastructure artifact to be traceable to a
category node (covered by the node's assertions, or by a child spec).

This product's `spx/13-infrastructure.enabler/21-test-infrastructure.enabler/`
has only a `21-python-code-quality.enabler` child — no `harnesses`,
`generators`, or `fixtures` category nodes. Meanwhile `outcomeeng_testing/`
already ships `harnesses/` (15 harness modules, including `git_context.py`),
`generators/`, and `fixtures/` with no governing category node.

The gap is pre-existing and product-wide: it predates and is unrelated to any
single harness. `git_context.py` (added for the sessions scenario-test
hermeticity fix) only surfaced it.

**Required handling** (out of scope for a single harness change):

- Author the `generators`, `fixtures`, and `harnesses` category nodes under
  `spx/13-infrastructure.enabler/21-test-infrastructure.enabler/` via
  `/authoring`, declaring the category-wide contract each enforces per
  `spx/15-test-infrastructure.pdr.md`.
- Establish traceability from each `outcomeeng_testing/{harnesses,generators,fixtures}/`
  artifact to the matching category node.

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
