# Issues

## The gate recipe body has no evidence

The compliance assertion that CI runs the full gate "never an inlined or
filtered subset" is verified from two ends that do not meet. One end reads
`.github/workflows/check.yml` and confirms a step runs `just check-full`. The
other reads `VALIDATION_STEPS` and confirms each declared step, including the
workflow and shell linters, belongs to the composed gate.

Between them sits the `check-full` recipe in the repository `Justfile`, which
dispatches to `python3 -m outcomeeng.validation check-full`. No evidence reads
that recipe body. Narrowing it — to `check`, which composes only the validation
recipe and drops the test recipe, or to any filtered invocation — leaves every
test in this node green while CI runs a subset.

Closing this needs an assertion naming the recipe-to-module dispatch and a
harness that reads the recipe body, so it reaches beyond the evidence surfaces
the current changeset touches.

## No workflow job declares a timeout

`spx/13-infrastructure.enabler/21-test-infrastructure.enabler/15-ci-gate.adr.md`
forbids two ways the gate can stop gating: a job-level `if:` that skips it, and
a truthy job-level `continue-on-error` that lets a failed job report success.
Both rest on the same reason — "a non-blocking gate is not a gate". An
unbounded job is a third way to reach that state and no rule covers it. A job
that never terminates never reports a conclusion, so it never blocks a merge,
and it holds a hosted runner for the GitHub Actions default of 360 minutes
before the platform reclaims it.

No `timeout-minutes` key exists anywhere in `.github/workflows/`. Every job in
`check.yml`, `distribute-skills.yml`, `refresh-instruction-blocks.yml`, and
`spec-tree-evals.yml` runs unbounded. `spec-tree-review.yml` and
`spec-tree.yml` pass a `timeout_minutes` input to reusable workflows in
`outcomeeng/gh-actions`, but that input lands as a step-level `timeout-minutes`
on the single Claude Code Action step; the upstream input documentation states
the `authorize` and `validate-workflow` jobs are not gated by it, so those jobs
and the checkout, tool-install, and post-steps around the timed step stay
unbounded too.

**Evidence.** Surfaced while diagnosing why a `check` job's status record was
stuck: the run and all seventeen of its steps reported success while the
check-run record held `in_progress`, which prompted an inventory of what bounds
these jobs. Nothing does. Wall-clock over the last 25 runs of each workflow:
`check` max 8.7 min, `spec-tree-evals` max 14.6 min, `spec-tree-review` max
10.9 min, and the remaining three under 1 min. The widest observed run is 14.6
minutes.

**Resolution shape**: decide whether an unbounded job belongs in the ci-gate
decision's family of gate-integrity rules. If it does, amend
`spx/13-infrastructure.enabler/21-test-infrastructure.enabler/15-ci-gate.adr.md`
with the rule, add the matching assertion to
`spx/13-infrastructure.enabler/21-test-infrastructure.enabler/test-infrastructure.md`,
and extend `tests/test_ci_gate.compliance.l1.py` with a violating fixture —
every other rule in that decision is verified that way — before adding
`timeout-minutes` to the workflows. A cap of 30 minutes leaves every workflow
at least double its observed worst case. The reusable workflows live in another
repository, so the rule reaches their jobs only through the inputs this
repository passes, and the assertion states what it can check here.

**Revisit condition**: resolve before the next change to
`spx/13-infrastructure.enabler/21-test-infrastructure.enabler/15-ci-gate.adr.md`,
so the rule family is settled while that decision is already in context.
