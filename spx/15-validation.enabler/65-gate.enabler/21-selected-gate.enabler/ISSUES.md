# Issues: Selected Gate

## Full-gate selection runs untargeted pytest

`just check` treats any path matching the selected-gate full-gate surface as
permission to run `CHECK_RECIPES`. `CHECK_RECIPES` includes the untargeted
pytest-backed `TEST_RECIPE`, so a local selected gate can pay full pytest cost
for a changeset whose changed surface is Markdown, spec text, skill prose, or
another non-test-bearing surface.

The selected local gate preserves time-to-value:

- Markdown, spec, and skill prose changes run the formatting, Markdown/spec,
  skill, docs, and generated-output validation steps that cover those files.
- Pytest runs only when changed paths include `[test]` evidence, test-runner
  wiring, implementation/runtime code that requires test evidence, or another
  source contract the governing node maps to pytest coverage.
- `just check-full` and CI remain the full validation-plus-full-pytest
  regression gate.

Revisit condition: update `outcomeeng.validation.selected_gate` and the
selected-gate tests so selecting a full validation surface does not
automatically imply untargeted pytest for Markdown-only or other
non-pytest-bearing changes.

## Gate-step path selection duplicates the generated-sources declaration

`outcomeeng/validation/selected_gate.py` selects gate steps from hardcoded `dist/claude/**`, `dist/codex/**`, and instruction-block path lists that duplicate relations 1 and 2 of `spx/local/generated-sources.toml`, while `spx/31-outcomeeng.enabler/31-verification.enabler/15-generated-attribution.pdr.md` makes the committed declaration the single source of generated-path knowledge for verifiers and consumers.

**Resolution shape**: derive the selector's generated-path patterns from `spx/local/generated-sources.toml`. The migration and the superseding `spx` verification scope projection are tracked in `spx/31-outcomeeng.enabler/31-verification.enabler/PLAN.md`.

## The live-discovery decision's premise does not support its conclusion locally

`15-live-discovery.pdr.md` closes its opening clause with

> nothing in the product sets a switch, so explicit full verification and CI prove every
> selected live row with their own credential

and its `## Verification` repeats the conclusion:

> NEVER: a harness, a skill, a generated instruction surface, or the CI workflow sets a
> disable switch — explicit full verification and CI require the successful execution of
> every selected live row with their own credential.

The premise is about the product's own source. The conclusion is about two runs. Nothing
carries the one to the other, because the switch is never read on the path that separates
them.

**What the source shows.** The skip is decided by the projection markers, and each is a
module-level reading of the ambient process environment taken once when its module is
imported: `runs_real_codex` and `runs_real_claude` in
`outcomeeng_testing/harnesses/installation.py` are each
`_disable_marker(<agent>_disabled_reason(os.environ))`. Nothing downstream distinguishes a
selected run from explicit full verification. The `justfile` names neither switch and no
workflow under `.github/workflows/` names either. `just check-full` runs
`python3 -m outcomeeng.validation check-full`, which dispatches to
`run_check(spawner=…, sink=…, recipes=CHECK_RECIPES)`; that path reads no switch and writes
no plan. `just check` runs `run_selected_check`, which reads
`read_agent_disable_states(os.environ)` into `SelectedGatePlan.agent_disable` — and that
field has exactly one reader, `plan.agent_disable.explanation_lines` in `_write_plan`, so the
reading is printed and gates nothing.

A contributor whose environment carries `DISABLE_CODEX_ENV` set to `DISABLE_VALUE` therefore
skips exactly the same rows under `just check-full` as under `just check`, and under the full
gate without even the plan line that would name the switch. The premise holds of the product's source and says
nothing about the environment the operator supplies, so the conclusion holds for CI alone,
and there only because nothing exports a switch into it.

**Impact.** A reader of the decision takes explicit local full verification for proof that
every selected live row executed. A switch left exported in a shell makes the full gate carry
the same declared skips the selected gate does, with no run-level signal that it did.

**Settlement condition.** The decision's guarantee belongs to CI rather than to local
explicit full verification, and its text says so. Only the operator amends a decision, and
that amendment is refinement held elsewhere rather than work for this Change. It is the same
sentence, and the same operator amendment, that the entry "The no-harness-sets-a-switch rule
is scoped to this repository's own selected live rows" in
`spx/15-validation.enabler/65-gate.enabler/ISSUES.md` awaits — for a different defect in it:
that entry concerns the NEVER's subject scope, this one the step from its premise to its
conclusion. Until the amendment lands, a reader who reaches either sentence reads both
entries.

**The other repair, and why it is not this one.** Making explicit full verification refuse a
set switch — reading the switch on the full-verification path and failing the run rather than
skipping — would make the conclusion true instead of narrowing it. That gives the full gate a
switch reading it does not take and a refusal it does not have, so it is a gate-selection
change outside this Change's Frame.

**Evidence.** The two quoted sentences against `outcomeeng_testing/harnesses/installation.py`
lines 187 and 189; a search for either declared switch's own text over `justfile` and
`.github/workflows/` returning no hit; the `check-full` branch of
`outcomeeng/validation/__main__.py`; and the single read of `SelectedGatePlan.agent_disable`
in `outcomeeng/validation/selected_gate.py`. Raised as finding `F-002` of changeset review
run `2026-09-22_14-07-16-429-851b4a371443`.

## The no-switch rule binds four subjects and its evidence sees one

`15-live-discovery.pdr.md` binds four subjects:

> NEVER: a harness, a skill, a generated instruction surface, or the CI workflow sets a
> disable switch

Three of the four reach no evidence.

**What the evidence covers.** Two assertions realize the rule, and both narrow it to Python
modules. `spx/32-distribution.enabler/21-installation.enabler/21-repository-installation.enabler/repository-installation.md`
line 55 states "no module outside the declaring one names a switch", linking
`tests/test_repository_installation.compliance.l1.py`;
`spx/15-validation.enabler/65-gate.enabler/gate.md` line 34 makes the same
declaration-versus-consumer claim over "the plan, this node's own report, and each row that
starts a real agent process", tagged `[audit]`. The reader behind the first is
`modules_naming_a_switch` in `outcomeeng/validation/agent_switch_enforcement.py`, which walks
`SWITCH_SCAN_ROOTS` through `python_modules`: a directory yields `rglob("*.py")`, a file
yields itself only when its suffix is `.py`, and every other path is refused by name with
`NotAPythonSource`. `SWITCH_SCAN_ROOTS` in `outcomeeng_testing/harnesses/installation.py`
resolves to `outcomeeng`, `outcomeeng_testing`, `outcomeeng_evals`, `spx`, and `src`.

So a skill body at `src/plugins/**/SKILL.md` sits inside a scanned root and is never read
because it is not a `.py` file; a generated instruction surface — the root `CLAUDE.md` and
`AGENTS.md`, and the `dist/claude/` and `dist/codex/` trees — and a workflow under
`.github/workflows/` sit outside every scanned root. Each could set a switch with nothing
detecting it. The one non-Python check anywhere near the rule is
`test_the_profile_execution_recipe_reads_no_disable_switch`, which reads a single justfile
recipe block through `native_profile_execution_recipe()` and so covers neither a skill, an
instruction surface, nor a workflow.

**Impact.** The rule reads as a guarantee over every surface that could suppress this
repository's live proof. What holds is the Python-module subject alone, so a switch set in a
shipped skill, in a generated guide, or in a workflow passes every gate the rule is meant to
stop it at — and the workflow case is the one the decision's own conclusion depends on,
since CI is the run the rule protects.

**Why this node.** The defect is the rule's own coverage rather than either realizing node's
test file: both linked surfaces narrow it identically, so neither is the wider home, and a
note under one would leave the other's reader to rediscover it. `15-live-discovery.pdr.md`
lives in this node, and this node is the only one whose context load reaches it — neither
`repository-installation.md` nor `gate.md` cites the decision by path, so a reader of either
never loads the rule this entry is about. Filing it beside the rule puts it where a reader of
the rule meets it, and beside the other open defect in the same sentence.

**Settlement condition.** Either the evidence reaches the surfaces the rule names — a
reading over skill bodies, the generated instruction surfaces, and the workflow files, with
the coverage asserted — or the rule states only the subject its evidence decides and the
remaining subjects carry evidence of their own. Which of the two is a change to the decision
and therefore the operator's, on the same sentence as the entry above.

**Evidence.** The quoted rule against `repository-installation.md` line 55 and `gate.md`
line 34; `python_modules` and `modules_naming_a_switch` in
`outcomeeng/validation/agent_switch_enforcement.py`; `SWITCH_SCAN_ROOTS` in
`outcomeeng_testing/harnesses/installation.py`; and
`test_the_profile_execution_recipe_reads_no_disable_switch` in
`spx/32-distribution.enabler/21-installation.enabler/21-repository-installation.enabler/tests/test_native_profile_execution.compliance.l1.py`
as the only non-Python reading. Raised as finding `F-003` of changeset review run
`2026-09-22_14-07-16-429-851b4a371443`, filed there against `repository-installation.md`
line 55.
