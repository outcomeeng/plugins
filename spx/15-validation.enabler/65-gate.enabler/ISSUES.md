# Issues — Gate

Known follow-ups for the gate node. Coordination note; not spec truth.

## Two readings of the no-harness-sets-a-switch rule stand side by side

`spx/15-validation.enabler/65-gate.enabler/21-selected-gate.enabler/15-live-discovery.pdr.md`
states without qualification: `NEVER: a harness, a skill, a generated instruction surface, or the
CI workflow sets a disable switch — explicit full verification and CI require the successful
execution of every selected live row with their own credential.`

`declared_skip_recording` in `outcomeeng_testing/harnesses/gate.py` sets both switches in the
environment of a pytest child it spawns, over four rows it generates itself, so the recorder the
gate registers writes the records a real gate step would leave. Two readings of the NEVER apply to
that write:

- **Literal reading.** The rule admits no exception, so a harness that sets a switch in any
  environment violates it, and the evidence for the declared-skip summary must be produced some
  other way.
- **Scoped reading.** The rule was written about this repository's own selected live rows — the
  proof a switch must not be allowed to suppress. A disposable child over generated rows reaches no
  such row, so the write is outside the rule's subject.

**Reading in force.** The scoped reading, while the amendment below is pending.

**Enforced by.** `confined_to` in `outcomeeng_testing/harnesses/gate.py` refuses before the child
starts unless the report target and the child's working directory lie in the disposable root that
run created, raising `UnconfinedDisposableState` with the offending path. The confinement is
enforced in code rather than asserted in prose, and both branches are driven from this node's
linked evidence in `spx/15-validation.enabler/65-gate.enabler/tests/test_gate.compliance.l1.py`: a
confined run that proceeds, and an unconfined target that is refused.

**Settlement condition.** The reading in force is product truth and belongs in the PDR, which only
the operator amends — carrying both readings above and the evidence that the write reaches no
selected live row of this repository. A ruling for the literal reading repairs the harness rather
than the evidence built on it: the write moves out of the harness, and the declared-skip evidence
keeps its assertions.

**Evidence.** The rule text quoted above against the `env=` mapping `declared_skip_recording`
passes to its child.

## The no-polling rule's subject was read as the whole validation package

The implementation audit under run token `2026-09-22_03-49-57-231-897034592bcc` raised a third
blocking finding: that the no-polling rule must scan every module of the `outcomeeng/validation`
package, `selected_gate.py` among them, and that a subject narrower than the package leaves modules
unscanned.

The premise does not hold. `spx/15-validation.enabler/21-subprocess-execution.adr.md` enumerates the
gate orchestrator as exactly `_engine.py`, `_model.py`, `_spawner.py`, `_steps.py`, `__init__.py`,
and `__main__.py`, and the assertion the rule backs, in
`spx/15-validation.enabler/65-gate.enabler/gate.md`, takes the orchestrator source as its subject:

> NEVER: the orchestrator source contains a literal `gh run watch` invocation or a `while True:`
> loop containing `time.sleep` — unbounded polling waits are forbidden across the marketplace per
> `spx/13-plugin-and-runtime-conventions.adr.md` ([test](tests/test_gate.compliance.l1.py))

Widening the subject to the package would pull
`selected_gate.py`, whose behavior the child node
`spx/15-validation.enabler/65-gate.enabler/21-selected-gate.enabler` declares, under the parent
node's assertion. The finding is wrong on its premise, not merely unbacked or unfiled.

The defect the same round did carry was in the predicate rather than in the subject:
`_imports_the_declaration` in `outcomeeng/validation/agent_switch_enforcement.py` recognised two of
the five import forms that bind `outcomeeng/validation/agent_disable.py`, missing
`from outcomeeng.validation import agent_disable`, `from . import agent_disable`, and
`from .agent_disable import codex_disabled_reason` — the first of which is the form the rule's own
module uses to reach the declaration.

**Settlement condition.** None; the subject stays at the decision's enumeration, and
`ORCHESTRATOR_MODULE_NAMES` in `outcomeeng/validation/__init__.py` publishes it so a rule reads the
enumeration rather than a naming pattern. A later auditor raising the wider subject reads this entry
first; a change of subject is an amendment to
`spx/15-validation.enabler/21-subprocess-execution.adr.md`.

**Evidence.** The five import forms driven against `modules_reading_the_switch_predicate`, two
reported and three missed; and the decision's six-file enumeration against the finding's expected
package-wide subject.

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

## The level-two scenario file declares a cell heavier than its dependencies

`tests/test_gate.scenario.l2.py` declares `l2`, but every executable its evidence exercises classifies `l1` under the executable discriminator: the interpreter comes from the declared development environment, and the wrapper programs run `outcomeeng.validation` directly from the checkout rather than from an installed or bootstrapped artifact. Real subprocesses and a multi-second grace deadline are execution pain, and level derives from dependency class alone.

**Resolution shape**: rename the file to its `l1` cell and confirm no linked assertion depends on the heavier declaration.

**Why separate**: the rename moves a file whose evidence the changeset does not otherwise touch, and the two scenario assertions linking it would need their links re-pointed in the same pass.

**Evidence**: the gate node's test-evidence audit recorded it as a warning against the execution-level rule.
