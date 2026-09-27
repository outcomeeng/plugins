# Issues — Gate

Known follow-ups for the gate node. Coordination note; not spec truth.

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

## The level-two scenario file declares a cell heavier than its dependencies

`tests/test_gate.scenario.l2.py` declares `l2`, but every executable its evidence exercises classifies `l1` under the executable discriminator: the interpreter comes from the declared development environment, and the wrapper programs run `outcomeeng.validation` directly from the checkout rather than from an installed or bootstrapped artifact. Real subprocesses and a multi-second grace deadline are execution pain, and level derives from dependency class alone.

**Resolution shape**: rename the file to its `l1` cell and confirm no linked assertion depends on the heavier declaration.

**Why separate**: the rename moves a file whose evidence the changeset does not otherwise touch, and the two scenario assertions linking it would need their links re-pointed in the same pass.

**Evidence**: the gate node's test-evidence audit recorded it as a warning against the execution-level rule.

## The signal scenarios' termination deadline leaves no margin over full-suite load

`TERMINATION_DEADLINE_SECONDS` in `outcomeeng_testing/harnesses/gate_signal.py` bounds the wait
for a real orchestrator subprocess to die after a forwarded signal at six seconds, over a
grace period of `SIGNAL_GRACE_SECONDS`. Run alone the four scenarios of
`tests/test_gate.scenario.l2.py` finish in about twenty-four seconds and pass. Inside the
full pytest surface, where the same run drives real subprocess groups for the whole
repository, the deadline is reachable: one full-gate run reported
`test_signal_terminates_process_group_within_grace` failing with `TimeoutExpired` after 6.0
seconds, and the next run of the same surface on the same tree passed every case.

The deadline is a wall-clock bound on a process the host schedules, so it measures the host's
scheduling latency alongside the orchestrator's own escalation. Under a loaded run the two are
not separable, and the case reports the sum against a budget sized for the second alone.

**Impact.** A starved run reads as a defect in signal forwarding, which is the one claim the
scenario exists to make. The cost lands on whoever next reads a red full gate: the failure
names the grace period, so the first reading is that escalation regressed, and separating that
from scheduling latency costs a second full-surface run.

**Resolution shape**: bound the wait by the orchestrator's own observable progress rather than
by wall-clock alone — or size the deadline from the grace period plus a margin the harness
derives, and record the host-load observation alongside a timeout so a starved run is
distinguishable from a regression without re-running the surface.

**Why separate**: the deadline belongs to `outcomeeng_testing/harnesses/gate_signal.py`, whose
seam this node already records as needing restructuring under "The signal harness owns the
predicates its linked tests should own" above. Both changes rewrite the same harness entry
points against real subprocess signal delivery, so they belong on one reviewed diff rather
than inside an unrelated repair.

**Evidence**: two runs of `just check` over the same tree, the first reporting
`subprocess.TimeoutExpired` after 6.0 seconds at
`outcomeeng_testing/harnesses/gate_signal.py:270` with 1721 other cases passing, the second
passing the whole pytest step in 743 seconds; and the same four cases passing in 23.61 seconds
when that file is run alone. The load waiter observed the host at 0.41 normalized before each
run, so neither started above capacity.

## The skipped-row nodeid shape is built in two places and published in neither

`SKIPPED_ROW_ID_SHAPE` in `outcomeeng_testing/harnesses/gate.py` states the nodeid shape
`{path}::{name}` that the harness builds each generated row's identity from, and
`modules_naming_a_switch`'s caller in `outcomeeng/validation/agent_switch_enforcement.py`
builds the same shape inline as `f"{path}::{node.name}"`. The production module publishes
no constant for it, so the harness states a shape production also states, and the two are
free to drift: a change to the separator in the validation package leaves the harness
shaping a nodeid the recorder no longer writes, with nothing failing.

**Resolution shape**: publish the nodeid shape from the validation module that builds it,
read it at that module's own site, and import it in the harness in place of
`SKIPPED_ROW_ID_SHAPE`.

**Why this is filed rather than repaired**: `agent_switch_enforcement.py` builds the shape
for its own report, and publishing a contract from it is a change to the producer for a
claim no assertion of this node makes. The harness half cannot be repaired first — the
source-ownership rule requires the name to be imported from the source complying with the
declaration, and there is no published name to import — so the harness keeps its own
constant until a Change carries the producer.

**Settlement condition**: `outcomeeng/validation/agent_switch_enforcement.py` publishes the
nodeid shape, its own site reads it, and `outcomeeng_testing/harnesses/gate.py` imports it.

**Evidence**: `SKIPPED_ROW_ID_SHAPE` in `outcomeeng_testing/harnesses/gate.py` against the
inline `f"{path}::{node.name}"` in `outcomeeng/validation/agent_switch_enforcement.py`;
surfaced by the source-ownership sweep over this Change's changed evidence and harness
lines, which found no other unpublished shape among them.

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

## The spawner's docstring names a compliance test that does not exist

`outcomeeng/validation/_spawner.py` opens by naming `TestSubprocessImportContainment`
as the compliance test enforcing the subprocess boundary. No class of that name exists
anywhere in the evidence chain. The enforcing evidence is
`test_subprocess_lives_only_in_the_production_spawner` in
`spx/15-validation.enabler/65-gate.enabler/tests/test_gate.compliance.l1.py`, which
parses the spawner's own source for the `subprocess.Popen` arguments the boundary
requires.

**Resolution shape**: name the existing case in the docstring, or drop the reference and
let the assertion's `[test]` link carry it.

**Why separate**: `_spawner.py` lies outside this changeset's diff, and the reference is
prose rather than behavior, so no evidence changes with it.

**Evidence**: the gate node's test-evidence audit recorded it as finding `f-008`, INFO,
against the stale-evidence-reference rule.

## The gate cannot tell a package's declared dependencies from this host's installed ones

`pyproject.toml` declares two runtime dependencies for this product, `click` and `jinja2`,
and carries pytest in the `dev` dependency group alone. Five justfile recipes — `test`,
`test-v`, `validation`, `check`, and `check-full` — start the orchestrator as
`python3 -m outcomeeng.validation` under the bare interpreter. A module of that package
importing pytest at module scope therefore breaks the orchestrator for any environment
whose interpreter does not happen to carry pytest, and every deterministic lane on this
host reports success, because this host has pytest installed.

The gate's one dependency reading is the `preflight-uv-import` step, whose argv is
`uv run python -c "import outcomeeng"`. It imports the top-level package under the
development environment, so it reaches neither `outcomeeng.validation` nor the interpreter
the five recipes use. Between the two, nothing the gate runs distinguishes a package that
imports its declared dependencies from one that imports whatever this machine happens to
have.

**How it surfaced.** Relocating the skip-report recorder into `outcomeeng/validation/`
brought `import pytest` to module scope in a module `__init__.py`, `_engine.py`, and
`_summary_schema.py` all import. The full gate passed. The repair is a `TYPE_CHECKING`
guard, proven by mutation: with the import at module scope, importing
`outcomeeng.validation` under a meta-path finder that refuses pytest raises
`ImportError`; under the guard it imports, because `from __future__ import annotations`
leaves all three uses — `pytest.TestReport`, `pytest.Parser`, `pytest.Config` — as strings.
What the mutation also shows is that no gate step observes the difference.

**Resolution shape**: give the gate a step that imports the orchestrator package under the
declared runtime dependencies alone and nothing else — the interpreter the five recipes
use, with the dev group absent — so an undeclared import fails the gate on the host that
introduced it. The step list is enumerated by a compliance assertion in
`spx/15-validation.enabler/65-gate.enabler/gate.md`, so the new step is declared there
beside the others.

**Why separate**: adding a gate step and naming it in the node's step-list assertion is an
authoring pass over this node's assertions, not a repair of the misplaced import; and the
step needs a dependency-only environment this repository's recipes do not currently build.

**Settlement condition**: a gate step imports `outcomeeng.validation` under the declared
runtime dependencies alone, the step-list assertion in `gate.md` names it, and a case
establishes that an undeclared module-scope import fails it.

**Evidence**: the repaired import at `outcomeeng/validation/skip_report.py` against
`pyproject.toml`'s `[project] dependencies` and its `dev` group; the five recipe lines in
`justfile`; the `preflight-uv-import` argv in `outcomeeng/validation/_steps.py`; and a full
gate that exited 0 over the module-scope import.

## The skip-report channel's split home is closed

`outcomeeng/validation/skip_report.py` states the skip-report channel as its subject and declares the option, its configuration name, the two record fields, the report file's prefix and suffix, the recorded row's status, the printed line form, and the recorder that writes the records. Both ends read every name from it, and the repository's pytest configuration registers the plugin from there.

Before this, the option and the record fields were declared in the module whose subject is the per-agent switches, the file naming and the printed line in the orchestrator, and the recorder in the test-infrastructure package — one channel with three homes and no module stating it as its subject.

The move removed `outcomeeng_testing/harnesses/skip_report.py` rather than leaving a re-export, which this repository forbids.

**Evidence**: the gate node's test-evidence audit finding `f-007` on the recorder's placement, and the implementation audit's debt finding on the vocabulary split between `outcomeeng/validation/agent_disable.py` and `outcomeeng/validation/_engine.py`. Both are closed.
