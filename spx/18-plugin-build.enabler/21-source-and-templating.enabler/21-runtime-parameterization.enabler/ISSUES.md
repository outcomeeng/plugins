# Issues: Runtime parameterization

Known defects, contradictions and gaps in this node. Coordination note; not spec truth.

## The node and its specs use the prohibited agent-concept term

[`spx/15-agent-terminology.pdr.md`](spx/15-agent-terminology.pdr.md) maps `runtime`, `per-runtime` and `runtime-specific` to `agent`, `per-agent` and `agent-specific` where the subject is a selectable coding agent. This node's name and its spec use the term in that sense: "runtime-divergent", "per-runtime registry" and "No runtime is the source language", which mean per-agent target rendering. "Runtime" stays valid for execution-time behavior and for an execution environment such as Python.

**Settlement condition.** The node and its spec align to the decision's required wording. The node name encodes the term, so the sweep includes a `/refactor` node rename and is structural, as the entry in `spx/18-plugin-build.enabler/ISSUES.md` records.

## The runtime-parameterization harness raises AssertionError for lifecycle failures

`outcomeeng_testing/harnesses/runtime_parameterization.py` raises `AssertionError` when a resource fails to start or a generated value has the wrong shape. The predicate-seam rule in `/test-evidence-standards` reserves assertion failures for the linked test; infrastructure raises only setup, dependency, lifecycle or execution errors, so raising `AssertionError` from infrastructure reports a failure away from every `assert` site and can read as a verdict the harness owns.

**Evidence.** The isolated test-evidence audit of `spx/13-infrastructure.enabler/13-host-readiness.enabler` on head `e3bf060ce4dd29ff34984b5d66f8302d9ca22e95` rejected the same shape in that node's harness (finding `f-001`), fixed there by raising a `RuntimeError` subclass from a harness-owned horizon.

**Settlement condition.** Each infrastructure `AssertionError` in the harness becomes a lifecycle or dependency error type the harness owns, with every behavioral predicate left in the linked tests, and the node passes its test-evidence audit.
