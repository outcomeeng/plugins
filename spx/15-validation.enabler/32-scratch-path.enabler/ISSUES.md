# ISSUES — scratch-path enabler

## DEBT [evidence]: expected diagnostic values come from the production scanner (f-001)

Finding f-001 (REJECT, oracle independence) at
`spx/15-validation.enabler/32-scratch-path.enabler/tests/test_scratch_path.scenario.l1.py:19`:
the expected line number and path reference come from `observed.violations`,
which the harness takes from `scan_file` in
`outcomeeng/validation/scratch_paths.py`, the production scanner. The test checks
only that the printed diagnostic repeats those values, so an off-by-one line or
a truncated reference would pass. The same audit raised WARNING f-002 at
`outcomeeng_testing/generators/scratch_paths.py:38`: several violating shapes
(the `2>` redirect, the `--destination=` flag, the `https://tmp.<plugin>.example.com`
host, and the `<plugin>_tmp/` prefix) mirror the implementation's regex comments
and are not stated by the spec.

The audit is a `product-tree:test-evidence-auditor` verdict on this node at head
`6ef55dd4d93b24b8fa701b8779116bbe7c9bbc04`. The verdict carries no sealed run
token.

**Resolution shape**: compute the expected line and path from the generated
source the harness writes, so the oracle is independent of `scan_file`.

**Evidence that the text lies outside the change.** `git diff -U0 origin/main...HEAD`
reports no hunk in the cited files, against merge base
`149a55f71befdf61e88be9bda2aae725db1f2381`.

**Invalidation check.** The cited text neither cites, restates, nor depends on
anything this changeset changed. The changeset adds symbols to
`outcomeeng/distribution/profiles.py`, narrows the guard in
`outcomeeng/validation/profile_configuration.py`, and adds model-price and
profile-binding generators, harnesses, and tests. The cited test drives
`outcomeeng/validation/scratch_paths.py`, which the changeset does not change.

**Settlement condition**: the test derives the expected line and path from the
generated source it writes, so an off-by-one line or a truncated reference fails
it.

## `l1` tests cross an `l2` boundary

**Evidence:** A run of every `l1` test file of the Product Tree at commit `744cf8cf23`, traced through the Python audit events of each test's setup, call and teardown, records that these `l1` files cross a boundary [`l1-boundaries`](spx/31-outcomeeng.enabler/31-verification.enabler/31-test-verification.enabler/21-evidence-types.pdr.md) places at `l2`:

- `tests/test_scratch_path.scenario.l1.py`: write a file, make a temporary directory

**Impact:** Each run of these files starts processes or writes into temporary trees on the host every Position shares, so local and CI gates spend that load on every run.

**Settlement condition:** Each listed file covers the same linked Assertions in process, with no lower line or branch coverage of this Node's code, or the evidence that needs the boundary stands in an `l2` file written for it.
