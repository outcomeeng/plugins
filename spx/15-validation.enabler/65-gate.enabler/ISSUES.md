# Issues — Gate

Known follow-ups for the gate node. Coordination note; not spec truth.

## The no-harness-sets-a-switch rule is scoped to this repository's own selected live rows

`spx/15-validation.enabler/65-gate.enabler/21-selected-gate.enabler/15-live-discovery.pdr.md`
states without qualification: `NEVER: a harness, a skill, a generated instruction surface, or the
CI workflow sets a disable switch — explicit full verification and CI require the successful
execution of every selected live row with their own credential.`

**Settled scope.** The operator ruled on 2026-09-22 that the NEVER is scoped rather than literal:
it binds this repository's own selected live rows, which are the proof a switch must never be
allowed to suppress. A disposable child collecting rows a run generates in a temporary directory is
not this repository's live discovery, so `declared_skip_recording` in
`outcomeeng_testing/harnesses/gate.py` — which sets both switches in the environment of a pytest
child it spawns over four rows it generates itself — was never within the rule's subject. The
unqualified phrasing over-reached into a case the decision did not contemplate.

**Why the scope holds.** `confined_to` in `outcomeeng_testing/harnesses/gate.py` refuses before the
child starts unless the report target and the child's working directory lie in the disposable root
that run created, raising `UnconfinedDisposableState` with the offending path. That enforcement is
what makes "not this repository's live discovery" a checkable fact about every run rather than a
claim about one: a target outside the root never reaches a child at all, so no selected live row of
the surrounding repository is in reach of the environment the harness writes. The confinement is
the reason the scope holds, not a precaution held in case the ruling went the other way, and both
its branches are driven from this node's linked evidence in
`spx/15-validation.enabler/65-gate.enabler/tests/test_gate.compliance.l1.py`: a confined run that
proceeds, and an unconfined target that is refused by name.

**Disposition of the audit finding.** The implementation audit under run token
`2026-09-22_03-49-57-231-897034592bcc` raised the harness's switch write against the rule's text.
That finding is disposed on the settled scope rather than held pending an amendment: it read the
decision's text correctly, and the text is what is wrong.

**Settlement condition.** The PDR's own wording is unchanged and still states the rule without the
scope it carries, so what remains is amending that text to say what the rule now means. Only the
operator amends a decision, and that amendment is refinement held elsewhere rather than work for
this Change. Until it lands, a reader who reaches the unqualified sentence reads this entry for the
scope in force.

**Evidence.** The rule text quoted above against the `env=` mapping `declared_skip_recording`
passes to its child, and against the `confined_to` refusal that bounds every path that mapping can
reach.

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

## Two compliance cells read the conforming spawner source with no violating case

Two compliance assertions in `spx/15-validation.enabler/65-gate.enabler/gate.md` are exercised by
reading the production spawner's own source and nothing else:

> ALWAYS: each child subprocess is started with `start_new_session=True` so signal forwarding
> targets a process group, never a single PID — prevents orphaned grandchildren when the
> orchestrator is interrupted ([test](tests/test_gate.compliance.l1.py))

> ALWAYS: each production child subprocess unblocks SIGTERM, SIGINT, and SIGHUP before exec so the
> orchestrator's protected spawn window does not make validators inherit a blocked
> forwarded-signal mask ([test](tests/test_gate.compliance.l1.py))

**What each reads.** `test_subprocess_lives_only_in_the_production_spawner` in
`spx/15-validation.enabler/65-gate.enabler/tests/test_gate.compliance.l1.py` parses
`outcomeeng/validation/_spawner.py`, the one module that imports `subprocess`, and requires of
every `subprocess.Popen` call in it that `start_new_session` be the literal `True` and that
`preexec_fn` name `_restore_child_signal_mask`; it then requires the module's text to carry the
`signal.pthread_sigmask(signal.SIG_UNBLOCK` call and each of the three forwarded signal names.
Every input is the conforming source. Neither rule has a source that violates it passed to the
reading by path.

**Deferrable rather than unfalsifiable.** Production mutation still breaks each assertion: dropping
`start_new_session=True` from the `Popen` call fails the first, and removing the `preexec_fn`
argument or the child-side unblock call fails the second, so the evidence can falsify the behavior
it names. What is absent is the compliance cell's own requirement — at least one real violating
case, a whole source artifact that breaks the rule, handed to the reading by path. A reading that
returned nothing on a violating source would pass here unnoticed, so the cell proves the conforming
source conforms without proving the rule is detected.

**The shape to reach.** The no-polling evidence in the same file already has it.
`unbounded_polling_sites` is a reader the validation package owns, and
`test_a_while_true_sleep_is_reported`, `test_a_watch_invocation_is_reported`, and
`test_a_bounded_loop_is_not_reported` each write a real source file under `tmp_path` and hand it to
that reader by path — two violating and one conforming, so a reader reporting everything or nothing
fails. The two cells above have no reader separable from the test to hand a fixture to.

**Settlement condition.** Each cell reaches a reader the validation package owns over the spawn
call's arguments, exercised against a violating source fixture passed by path: for the session
rule, a spawner-shaped source whose `subprocess.Popen` call omits `start_new_session` and one that
passes it `False`; for the signal-mask rule, a spawner-shaped source whose `Popen` call carries no
`preexec_fn`, and one whose child-side function omits the `SIG_UNBLOCK` of the three forwarded
signals. Conforming sources beside them establish that the reader raises no false positive, as the
no-polling cases do.

**Why separate.** Both cells lie outside the Output this changeset carries — the per-agent disable
switch and the declared skip its report names. Reaching the settlement condition extracts a
spawn-argument reader out of the test into the validation package and authors its violating
fixtures, which rewrites evidence the switch work does not touch.

**Evidence.** The two assertions' text against the inputs of
`test_subprocess_lives_only_in_the_production_spawner`, which are the conforming spawner source
alone; and the same file's no-polling cases as the violating-source shape the compliance cell
requires.

## The summary-schema interpreter tolerates a keyword it does not evaluate

`assert_json_schema` in `outcomeeng/validation/_summary_schema.py` evaluates a fixed keyword
subset — `anyOf`, `const`, `enum`, `type` over object, array, string and integer, `required`,
`properties`, `additionalProperties`, `items`, and `minItems` — and its docstring now names that
subset. Nothing refuses a schema that declares another keyword, or one of these where the reader
does not look for it: a schema carrying `maxItems`, `pattern`, or `minimum`, or `minItems` on a
schema whose type is not `array`, would pass every instance the keyword was written to reject,
exactly as `minItems` did before it was interpreted. The oracle the node's conformance assertion links is
therefore only as strong as a reader's memory of which keywords it reads.

**Resolution shape**: refuse a schema declaring a keyword outside the evaluated set, so a
constraint that cannot fail is rejected where it is declared rather than shipped silent. The
refusal is a new observable behavior of the oracle, so it needs an assertion of its own in
`spx/15-validation.enabler/65-gate.enabler/gate.md` and a violating-schema case beside it; the
interpreter is reached only from this module's own constants and this node's conformance
evidence, so the change is bounded to the two.

**Why separate**: the repair that surfaced it interprets the one declared keyword that did
nothing, inside the conformance assertion that already governs the schema. Refusing an
unevaluated keyword declares a new property of the oracle, which is an authoring pass over the
node's assertions rather than a repair of this Change's implementation.

**Evidence**: the schema's `minItems: 1`, declared by this Change and evaluated by no branch of
`assert_json_schema` until it was interpreted; an empty list passed the schema it constrained.
