# ISSUES — native agent recovery

Coordination note; not spec truth.

## DEBT [evidence]: the reassessment mapping assertion resolves to the compliance lane

The Mappings assertion covering reassessment planning links
`tests/test_native_agent_recovery.mapping.l1.py`, but every reassessment predicate — the read
barrier, the per-recipient delivery correspondence, and the judged-intact record — is computed in
`verify_native_agent_recovery_compliance` in `outcomeeng_testing/harnesses/native_agent_recovery.py`
and therefore executes only through `tests/test_native_agent_recovery.compliance.l1.py`. The linked
mapping file never calls `plan_reassessment`, so the assertion's declared evidence does not exercise
its own subject.

**Resolution shape**: move the reassessment state-correspondence checks into
`verify_native_agent_recovery_mappings` so the mapping link resolves to the lane its assertion type
names, leaving the compliance function the boundary and settlement rules that are genuinely
compliance-shaped.

**Deferral reason**: `verified` is built in the compliance function from a chain of pane, agent, and
correlation fixtures assembled across roughly fifty preceding lines, so relocating the reassessment
checks means extracting that chain into a shared fixture rather than moving a few statements. That
extraction lands inside the harness inversion the entry below already defers as one migration across
three files, and doing it separately would rewrite the same setup twice.

## DEBT [evidence]: this node's linked tests hold every predicate in their harness

`test-evidence-auditor` raised fifteen blocking findings, one per `[test]`-tagged assertion on this
node, all of a single class. Each of the three linked test files is
a single `assert <harness function>() == []` call, so no behavioral predicate is lexically visible in
any executed test: `tests/test_native_agent_recovery.mapping.l1.py` delegates to
`verify_native_agent_recovery_mappings`, `tests/test_native_agent_recovery.compliance.l1.py` to
`verify_native_agent_recovery_compliance`, and `tests/test_native_agent_recovery.property.l1.py` to
`verify_native_agent_recovery_properties`. All three live in
`outcomeeng_testing/harnesses/native_agent_recovery.py`, where every pass/fail comparison is computed
and aggregated into a returned failure list — including the two Hypothesis inner callbacks, whose
invariants append to an outer list rather than calling an assertion API.

`spx/31-outcomeeng.enabler/31-verification.enabler/31-test-verification.enabler/15-test-infrastructure.pdr.md`
governs the opposite arrangement: the linked executed test owns every behavioral predicate and
assertion API call, while a harness exposes observations and never returns a verdict. A function that
returns a failure list is a verdict-shaped helper, so a mutation to any governed rule is caught by
editing the harness rather than the test that claims to verify it.

**Resolution shape**: give each assertion an observation helper that returns the observed value beside
its independently derived expectation, then move every comparison into its own test function in the
linked file. The oracle independence the harness already supplies through its generators is preserved
by the inversion — the harness keeps producing the independent expectation and stops rendering the
verdict.

**Revisit condition**: the pattern spans several nodes rather than this one, so the inversion is one
migration with a shared harness contract rather than a per-node repair. This node's three files are
among the spec test files whose every assertion is a bare comparison of a harness return value against
an empty failure list; a wider set delegates to `assert_*` helpers in the same way. `spx/15-validation.enabler/65-gate.enabler/21-selected-gate.enabler/ISSUES.md` and
`spx/18-plugin-build.enabler/54-conversion.enabler/21-agents.enabler/ISSUES.md` track the same class
for their own nodes. Schedule the three together as that migration.

**Deferral reason**: the changeset that surfaced this widens one return annotation in the harness so
its declared type matches the type its single consumer already declares, unblocking a type check that
was failing for every branch. The auditor confirmed the widening is annotation-only and weakens no
assertion. Inverting an eight-hundred-line harness and fifteen assertions to land that one line would
replace a bounded repair with the first unit of a migration the other two nodes defer by the same
reasoning.
