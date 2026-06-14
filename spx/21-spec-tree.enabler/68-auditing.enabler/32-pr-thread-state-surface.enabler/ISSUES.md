# Issues: PR-Thread State Surface

## 1. Two assertions cross-link the parent node's shared test via `../tests/`

`pr-thread-state-surface.md` assertions for finding-identity keying and the
empty-prior case link `[test](../tests/test_auditing.scenario.l1.py)` — a test
that lives in and is owned by the parent `spx/21-spec-tree.enabler/68-auditing.enabler/tests/`
and is also linked by that parent's own `auditing.md`. Co-location convention is
that a node's assertions link tests in its own `tests/` directory; these two
assertions instead reach up into a shared parent test.

Unlike `test_audit_orchestrator_cli.scenario.l1.py` (exclusively this node's
concern, relocated into this node's `tests/`), `test_auditing.scenario.l1.py` is
genuinely shared, so the fix is not a file move. It is a test-evidence
restructuring: extract this node's scenarios (identity keying, empty-prior) into
a node-owned `tests/` file, or move the assertions to the node that owns the
test. That is a larger, separate concern than the cross-node-link cleanup that
relocated the orchestrator-CLI test.

Surfaced during the test-infrastructure governance inventory.
