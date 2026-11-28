# Issues: Verification Enabler

## Review still uses the legacy journal surface

Audit implementation moves to `spx verification run` in the active slice. Review still has source and tests that refer to `spx journal --type review`, including the review-run inspection helper and project-run-journal skill.

Required handling:

- Specify the review verification-run contract before replacing review journal helpers.
- Preserve the current `changes-reviewer` raw-token integration until the review verification-run replacement exists.

## Downstream enforcement for `[audit]` decision-rule modes

[`spx/31-outcomeeng.enabler/31-verification.enabler/14-verification.pdr.md`](spx/31-outcomeeng.enabler/31-verification.enabler/14-verification.pdr.md) carries `[audit]` rules under `## Verification` / `### Audit`. Establish how `[audit]` decision-rule modes are enforced downstream: either author node-spec `[audit]` assertions an audit skill checks against each rule, or refine `spx/21-product-tree.enabler/32-decisions.enabler/decisions.md` so it recognizes audit/eval enforcement for `[audit]`/`[eval]` modes.

## Missing `[eval]` evidence on verification skill judgment surfaces

Verification skills that produce LLM-driven judgment need `[eval]` evidence where they emit structurally validatable verdicts. Apply the eval evidence pattern used by existing review-change evals to remaining verification skills as each surface is migrated.

## `l1` tests cross an `l2` boundary

**Evidence:** A run of every `l1` test file of the Product Tree at commit `744cf8cf23`, traced through the Python audit events of each test's setup, call and teardown, records that these `l1` files cross a boundary [`l1-boundaries`](spx/31-outcomeeng.enabler/31-verification.enabler/31-test-verification.enabler/21-evidence-types.pdr.md) places at `l2`:

- `tests/test_unread_scope.compliance.l1.py`: write a file, start a process

**Impact:** Each run of these files starts processes or writes into temporary trees on the host every Position shares, so local and CI gates spend that load on every run.

**Settlement condition:** Each listed file covers the same linked Assertions in process, with no lower line or branch coverage of this Node's code, or the evidence that needs the boundary stands in an `l2` file written for it.
