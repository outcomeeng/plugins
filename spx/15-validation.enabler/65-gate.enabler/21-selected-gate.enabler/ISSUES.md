# Issues: Selected Gate

## Changed-path collection has evidence and no assertion

Seven cases in `tests/test_selected_gate.mapping.l1.py` and one in the sibling compliance file
verify how the node collects changed paths before it selects anything:
`test_changed_paths_collect_from_all_four_git_surfaces`,
`test_whitespace_paths_survive_collection`, `test_a_rename_collects_both_sides`,
`test_a_copy_collects_both_sides`, `test_a_deleted_then_modified_test_still_runs_when_present`,
`test_deleted_assertion_tests_never_select_pytest`,
`test_a_renamed_test_source_never_reaches_pytest`, and
`test_an_empty_changeset_selects_no_steps`.

`selected-gate.md` declares no assertion about collection. Its five mapping assertions all
take a changed-path set as given and declare what that set selects; nothing declares where
the set comes from, which git surfaces contribute to it, or how a rename, a copy, a deletion,
or a path carrying whitespace resolves into it. So eight cases verify behavior the spec does
not claim, and the node's declared assertions would all still hold if collection changed
under them.

**The assertion the evidence implies.** A changed-path set is collected from the four git
surfaces the module reads — the branch diff against the resolved base, the staged diff, the
unstaged diff, and untracked files — as the union of their paths, with a rename and a copy
each contributing both sides, a path preserved verbatim including surrounding whitespace, and
a deleted path present in the set while absent from the working tree. Two of the eight cases
are about what collection then selects rather than collection itself
(`test_deleted_assertion_tests_never_select_pytest`,
`test_a_renamed_test_source_never_reaches_pytest`), so they may belong under the existing
assertion-path mapping rather than a new one.

**Which node owns it.** This one. Collection is `collect_changed_paths`,
`collect_changed_path_entries`, `deleted_paths_after_status_resolution`, and the
`GIT_DIFF_*` argv constants in `outcomeeng/validation/selected_gate.py`, which this node
declares, and the canonical changeset-scope helper they call is already the subject of this
node's git-discovery-failure assertion. No other node's spec reaches the collection path.

**Why this is filed rather than repaired.** The evidence is correct and the cases are worth
keeping; what is missing is the declaration above them. Writing that assertion from the
evidence would derive the declaration from the test, which inverts the layer order the
methodology exists to hold. Deleting the evidence would lose real verification of real
behavior. So the assertion is the operator's to author, and the evidence waits for it.

**Settlement condition**: `selected-gate.md` declares collection — the four surfaces, the
union, and the rename, copy, deletion, and verbatim-path resolutions — and each of the eight
cases links that assertion or the existing one it properly belongs to.

**Evidence**: the eight case names above against the five mapping assertions and eight
compliance assertions in `selected-gate.md`, none of which names collection; and the node's
test-evidence audit on head `3d1dbffd76393c71dbbaf455f5c81c81bf015064`, whose finding
`f-001` recorded the same absence as an assertion-type mismatch.

## Two harness case inputs carry an unstated property

`SELECTED_GATE_RENAMED_TARGET_ARG` and `SELECTED_GATE_WHITESPACE_PATH` in
`outcomeeng_testing/harnesses/gate.py` are the inputs three rename cases, one copy case, and
the whitespace case in `tests/test_selected_gate.mapping.l1.py` are driven with. Each carries
a property the case depends on and nothing declares.

The rename target's value is load-bearing only because it matches no selection pattern: that
is what makes `test_a_renamed_test_source_never_reaches_pytest` prove the renamed source
reaches no pytest step rather than proving nothing. Change it to a path under one of the
source's categories and the case passes for the wrong reason. The whitespace path's value is
load-bearing because it carries leading and trailing spaces that collection must preserve
verbatim. Neither property is stated in the harness, in the cases, or in any assertion.

**The assertion the evidence implies.** The same collection assertion the entry above needs,
whose verbatim-path clause states what the whitespace input is for; and, for the rename
target, that a renamed path matching no selection category selects no step, which is the
negative half of the category mapping this node already declares.

**Why this is filed rather than repaired.** The fix is not moving the two values into a
generator: a generated value cannot carry "matches no source category" unless something
declares that property, and once it is declared the value derives from the declaration. So
the declaration comes first and the derivation follows it, in that order.

**Settlement condition**: both properties are declared — the verbatim-path clause in the
collection assertion, and the no-category-match clause beside the category mapping — and each
input is then derived from the source category set rather than chosen, as
`changed_path_domain` in `outcomeeng_testing/generators/gate.py` now derives its own domain.

**Evidence**: the two constants and their five call sites in
`tests/test_selected_gate.mapping.l1.py`; and the node's test-evidence audit on head
`3d1dbffd76393c71dbbaf455f5c81c81bf015064`, finding `f-004`, whose message records that the
rename target's load-bearing property is stated nowhere.

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
the rule meets it.

**Settlement condition.** Either the evidence reaches the surfaces the rule names — a
reading over skill bodies, the generated instruction surfaces, and the workflow files, with
the coverage asserted — or the rule states only the subject its evidence decides and the
remaining subjects carry evidence of their own. Which of the two is a change to the decision
and therefore the operator's, on the rule's own sentence.

**Evidence.** The quoted rule against `repository-installation.md` line 55 and `gate.md`
line 34; `python_modules` and `modules_naming_a_switch` in
`outcomeeng/validation/agent_switch_enforcement.py`; `SWITCH_SCAN_ROOTS` in
`outcomeeng_testing/harnesses/installation.py`; and
`test_the_profile_execution_recipe_reads_no_disable_switch` in
`spx/32-distribution.enabler/21-installation.enabler/21-repository-installation.enabler/tests/test_native_profile_execution.compliance.l1.py`
as the only non-Python reading. Raised as finding `F-003` of changeset review run
`2026-09-22_14-07-16-429-851b4a371443`, filed there against `repository-installation.md`
line 55.

## The live-discovery clause claims two surfaces this node does not own

The compliance assertion in `selected-gate.md` reads:

> ALWAYS: local selection includes live discovery for installation, subagent-definition
> generation and placement, discovery, and their governing contracts and verification
> infrastructure; explicit full verification and CI include it

Its first clause is this node's own subject and is reached: `build_selected_gate_plan`
selects the live rows for each declared surface, and `test_each_declared_discovery_surface_requires_the_live_check`
drives it. The second clause names two surfaces the selection layer never touches.

**What the second clause would have to read.** Explicit full verification is the
`check-full` branch of `outcomeeng/validation/__main__.py`, which calls
`run_check(recipes=CHECK_RECIPES)` and bypasses `run_selected_check` entirely, so no code
path can apply `LIVE_DISCOVERY_EXCLUSION` to it. CI is the full-gate invocation in
`.github/workflows/check.yml`. No linked test in this node references either; the four
full-gate cases drive `full_gate=True` inside `build_selected_gate_plan`, which is the
selected full-gate plan rather than either named surface. Applying the exclusion on either
path leaves all seven linked files passing.

**Why this is a declaration defect rather than an evidence gap.** Both surfaces are governed
elsewhere — `outcomeeng/validation/__main__.py` is one of the six modules
`spx/15-validation.enabler/21-subprocess-execution.adr.md` enumerates as the gate
orchestrator, and the workflow belongs to the CI-gate decision under
`spx/13-infrastructure.enabler/21-test-infrastructure.enabler`. Evidence under this node
reading either would assert a contract another node declares. The clause claims more than the
node's subject carries, so narrowing it or rehoming it is the repair, and the same sentence
appears in `15-live-discovery.pdr.md`, which only the operator amends.

**Impact.** A reader of the assertion takes it for a guarantee that the two runs which are
supposed to prove every live row do include them. Neither run is observed, so the guarantee
rests on nothing: the exclusion could be applied to the `check-full` dispatch or to the CI
invocation and every linked file would still pass. The surfaces the clause claims are exactly
the two the live-discovery decision leans on to justify letting a local selected run skip a
row, so an unobserved clause here is what a switched-off local row is traded against.

**Settlement condition**: either both enumerations narrow the clause to the selection layer's
own full-gate plan, or each named surface carries evidence under the node that governs it —
the `check-full` dispatch under the gate node, the workflow under the CI-gate node.

**Related entries.** The workflow's absence from every scanned root is recorded above under
"The no-switch rule binds four subjects and its evidence sees one". This entry is the spec
assertion's own scope, which that entry does not cover.

**Evidence**: the quoted assertion against the `check-full` branch of
`outcomeeng/validation/__main__.py`; the four full-gate cases in
`tests/test_selected_gate.compliance.l1.py`, each driving `build_selected_gate_plan`; and a
search over this node's seven linked files returning no reference to the dispatch or the
workflow. Raised as finding `f-001`, REJECT, by the node's test-evidence audit.

## The import-form domain names five forms and the reader carries a sixth

Two surfaces declare the import forms the static index resolves, and both enumerate
exactly five. The mapping assertion in `selected-gate.md` reads:

> Every import statement form an executed test or test-infrastructure module can carry —
> `import a.b`, `from a.b import c` naming a submodule, `from a.b import c` naming an
> attribute, `from . import c`, and `from .c import d` — maps to the test-infrastructure
> module names the static import index records for it

and the testing verification in `21-test-infrastructure-reach.adr.md` reads:

> ALWAYS: every import statement form — `import a.b`, `from a.b import c` naming a
> submodule, `from a.b import c` naming an attribute, `from . import c`, and
> `from .c import d` — resolves to the test-infrastructure module names it depends on

Every one of the five is level 0 or level 1. `_resolve_import_from_base` in
`outcomeeng/validation/infrastructure_index.py` carries two branches neither enumeration
names: the multi-level ascend for `node.level >= 2`, reached by a form such as
`from .. import c`, and its `ascend >= len(base_parts)` refusal for an import climbing
above the package.

**What the evidence reaches.** The test-evidence audit of this node states that the five
declared forms are all reached, and that the two branches are reached by no linked test:
`import_statement_cases()` in `outcomeeng_testing/generators/infrastructure_index.py`
supplies only level 0 and level 1 forms, and no module under `outcomeeng_testing/`
carries a relative import, so the real-checkout index in `repository_reach` never reaches
them either.

**Why this is not a coverage gap of the declaration.** Reality exceeds the declaration
here rather than the evidence falling short of it. Supplying the generator case alone
would make the evidence the only statement of a branch no assertion declares, which
inverts the truth hierarchy from the declaring side.

**Resolution shape**: widen both enumerations to name the multi-level relative form, then
supply the generator case for it and for the refusal. The enumerations are a decision and
a spec assertion, so the amendment is the operator's; the generator case follows it.

**Settlement condition**: the two enumerations name the form, and
`import_statement_cases()` supplies it along with an import climbing above its package.

**Evidence**: the two quotations above against `_resolve_import_from_base`'s
`node.level >= 2` and `ascend >= len(base_parts)` branches; and the test-evidence audit's
finding `f-001`, WARNING, whose own words separate the two routes — "widening the declared
domain is a spec change while supplying the case is a generator change".
