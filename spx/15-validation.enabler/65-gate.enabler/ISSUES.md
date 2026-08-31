# Issues — Gate

Known follow-ups for the gate node. Coordination note; not spec truth.

## The signal harness owns the predicates its linked tests should own

`spx/31-outcomeeng.enabler/31-verification.enabler/31-test-verification.enabler/15-test-infrastructure.pdr.md`
requires that the executed test own every behavioral predicate and assertion API
call, and that a harness expose observations, resource handles, or callback
inputs without calling an assertion API, returning a pass/fail verdict, or
exposing verdict-shaped helpers.

`outcomeeng_testing/harnesses/gate_signal.py` inverts that seam. It exports four
verdict-shaped entry points — `assert_signals_terminate_process_groups_within_grace`,
`assert_spawn_window_signals_reach_child_groups`,
`assert_production_spawner_captures_child_output`, and
`assert_production_spawner_signal_terminates_child` — and holds every predicate
for the node's level-2 scenarios: the process-liveness checks, the
delivered-signal comparison in `_assert_grandchild_received_group_signal`, and
the exit-code and summary-record checks in `_assert_failed_signal_summary`. Each
of the four linked test functions in
`spx/15-validation.enabler/65-gate.enabler/tests/test_gate.scenario.l2.py` is a
bare delegating call whose body owns no predicate, so the harness rather than the
executed test decides pass and fail for the grace-period, escalation,
process-group delivery, and exit-code claims the assertions make.

The evidence still reaches real behavior — each scenario drives the production
orchestrator and spawner in a real subprocess — so what the inversion costs is
locality: a reader of the test file cannot see what the scenario claims, and a
harness change can alter a verdict without any edit to the file that names the
assertion.

**Resolution shape**: convert the four entry points to return observations —
process-liveness readings, the delivered signal value, the orchestrator return
code, and the parsed summary record — and move each predicate into
`spx/15-validation.enabler/65-gate.enabler/tests/test_gate.scenario.l2.py`
beside the assertion it verifies. Keep the marker publication, subprocess
lifecycle, and cleanup in the harness, which is the resource management it is
entitled to own. Re-run `test-evidence-auditor` over the repaired seam.

**Why this is separate**: the changeset that surfaced it fixes a marker
publication race in the same harness, an eight-line change that leaves the seam
exactly as it found it. Restructuring the seam rewrites four harness entry
points and the whole linked test file in code that drives real subprocess signal
delivery, so it carries regression risk that belongs on its own reviewed diff
rather than bundled into a bug fix.

**Revisit condition**: resolve before the next behavioral change to
`outcomeeng_testing/harnesses/gate_signal.py`, so the seam is repaired while that
harness is already in context.

## The property tests declare Hypothesis settings the harness owns

`spx/31-outcomeeng.enabler/31-verification.enabler/31-test-verification.enabler/15-test-infrastructure.pdr.md`
places property-run execution configuration — seed selection, run counts, replay
input, and failure diagnostics — in a property-test harness.
`tests/test_gate.property.l1.py` declares `@settings(max_examples=MAX_EXAMPLES,
deadline=None)` and the module-level `MAX_EXAMPLES` constant in the test file
instead. The replayable-property wrapper pattern already exists in
`outcomeeng_testing/harnesses/gate.py` (`selected_gate_property`), so the fix is
to route both property tests through a harness-owned wrapper of that shape.

The same pattern sits in two other nodes' property files, each tracked in its
own `ISSUES.md`; one shared wrapper in `outcomeeng_testing/harnesses/` can serve
all three.

**Resolution shape**: add a harness-owned property wrapper for this node's
generated step-list domain, move the settings into it, and re-run
`test-evidence-auditor` over the node.

**Evidence**: test-evidence audit on the gate predicate-seam changeset
(PR #549, head `23ebaa5d7e56ab311a40641151c5c048382efba2`), findings f-001 and
f-002, WARNING severity — non-blocking because Hypothesis's default failure
report carries the replay hint.

**Revisit condition**: resolve with the next behavioral change to this node's
test evidence, alongside the signal-harness seam entry above.
