# Issues: Prowl environment

Known defects, contradictions and gaps in this node. Coordination note; not spec truth.

## The Prowl generator raises AssertionError for a generated value of the wrong shape

`outcomeeng_testing/generators/prowl_environment.py` raises `AssertionError` when a generated value has the wrong shape. The predicate-seam rule in `/test-evidence-standards` reserves assertion failures for the linked test; infrastructure raises only setup, dependency, lifecycle or execution errors, so raising `AssertionError` from infrastructure reports a failure away from every `assert` site and can read as a verdict the generator owns.

**Evidence.** The isolated test-evidence audit of `spx/13-infrastructure.enabler/13-host-readiness.enabler` on head `e3bf060ce4dd29ff34984b5d66f8302d9ca22e95` rejected the same shape in that node's harness (finding `f-001`), fixed there by raising a `RuntimeError` subclass from a harness-owned horizon.

**Settlement condition.** Each infrastructure `AssertionError` in the generator becomes a dependency or execution error type the generator owns, with every behavioral predicate left in the linked tests, and the node passes its test-evidence audit.
