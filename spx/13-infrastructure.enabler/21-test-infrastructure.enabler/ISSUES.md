# Issues: Test Infrastructure Enabler

## 1. Gate-job-level soft-pass / skip is not covered by the workflow-contract test

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
