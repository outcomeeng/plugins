# Issues: Changeset Scope

## Changeset-primitive extraction awaits a published SPX CLI capability

`src/plugins/product-tree/skills/scope-changeset/scripts/changeset_scope.py` exceeds
fifty lines — branch identity, the on-disk addressing slug, base-ref
resolution, committed selector resolution, the remote-tracking ref form, and merge-base diff scope. Past fifty
lines [`spx/12-shipped-scripting.adr.md`](spx/12-shipped-scripting.adr.md) makes a shipped script debt whose logic
moves into the SPX CLI once the script proves its value; these primitives have
proven their value in use, so extraction is what they owe.

This module is the single home the audit, review-changes, sync-base, merge, and
coherence-audit skills all import rather than re-deriving, so its extraction
also removes the shipped-script debt those consumers inherit through it.

The extraction is a cross-repo port into `@outcomeeng/spx`, a separate product,
and the plugins product may depend on the resulting capability only once it is
published to npm and `REQUIRED_SPX_VERSION` advances to it. That sequencing puts
the fix outside any changeset confined to this repository.

**Resolution shape**: port the derivation primitives into the SPX CLI as a
consumable command surface, publish it, advance the floor, and repoint every
consuming skill at the published capability. Keep the one-derivation invariant
across the move — no consumer re-implements base-ref resolution or diff scope.
Revisit when the capability publishes.

## `l1` tests cross an `l2` boundary

**Evidence:** A run of every `l1` test file of the Product Tree at commit `744cf8cf23`, traced through the Python audit events of each test's setup, call and teardown, records that these `l1` files cross a boundary [`l1-boundaries`](spx/31-outcomeeng.enabler/31-verification.enabler/31-test-verification.enabler/21-evidence-types.pdr.md) places at `l2`:

- `tests/test_changeset_scope.scenario.l1.py`: write a file, start a process, make a temporary directory
- `tests/test_changeset_scope_remediation.mapping.l1.py`: write a file, start a process, make a temporary directory
- `tests/test_stale_base.compliance.l1.py`: write a file, start a process, make a temporary directory
- `tests/test_stale_base.scenario.l1.py`: write a file, start a process, make a temporary directory

**Impact:** Each run of these files starts processes or writes into temporary trees on the host every Position shares, so local and CI gates spend that load on every run.

**Settlement condition:** Each listed file covers the same linked Assertions in process, with no lower line or branch coverage of this Node's code, or the evidence that needs the boundary stands in an `l2` file written for it.
