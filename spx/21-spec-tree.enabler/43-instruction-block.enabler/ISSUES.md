# Issues: Instruction Block

## Topology mapping evidence owns its cases in the linked test

`tests/test_instruction_block.mapping.l1.py:13` declares `_TopologyCase`, and
`_topology_cases()` selects the finite topology cases and expected region bodies
inside the linked test. The Python test standards require case data to come from
its semantic owner and expected results to follow an independent construction law.
The case table leaves the evidence dependent on the test author's selected examples.

**Evidence**: the isolated test-evidence audit of this node at
`4d1bd7bba4f66612ae57221295b624b215c65f5e` returned `REJECTED`, finding `f-001`,
for test-owned data. Its trace reaches the instruction-block mapping harness,
generator, distribution module, and shipped instruction-block script.

**Settlement condition**: the mapping evidence covers the complete finite topology
domain through a source-owned enumeration or meaningful generator and derives
expected region bodies independently, with every comparison in the linked test.
Moving the same hand-picked table into a generator alone does not settle the issue.

**Disposition**: Change #41 modifies the separate compliance test's exception
boundaries. The mapping test is outside that changeset's diff. The auditor-verdict
rule in `spx/15-merging.pdr.md` requires this finding to be recorded here and keeps
it from blocking that corrective merge; its rejected verdict remains recorded.

## Existing evidence re-declares production vocabulary and author-chosen expectations

The isolated test-evidence audit of this node on head `df87dc4ffbe8f209a10f75aa86874b7503ef60a0` rejected five artifacts the router-narrowing changeset did not touch, beside the topology-table finding recorded above:

- `tests/test_instruction_block.scenario.l1.py` hand-writes the status tokens `absent`, `stale`, and `current` that `InstructionStatus` in the shipped generator owns, and passes the harness keys `claude` and `codex` as literals where the generator's `AGENT_HARNESS_INSTRUCTION_FILENAMES` mapping and the harness constants already own them.
- `tests/test_instruction_block.compliance.l1.py` copies the module invocation, the lefthook path, the pre-commit build command, and the two retired direct-template arguments that `outcomeeng/distribution/instruction_block.py` declares as named constants, and its refresh-workflow tests choose their shell tokens and the digest width themselves, so no production behavior exists whose mutation fails them.
- `outcomeeng_testing/fixtures/instruction_block/near-identical-shared.md` stores the author's own computation of the expected common span over the two near-identical inputs and is consumed as a mapping expectation; the node's property harness already carries the independent oracle for that span.

**Evidence.** Findings `f-002` through `f-006` of that audit; each subject lies outside the changeset's diff, so the merging decision routes them here rather than to the merge.

**Settlement condition.** The scenario and compliance tests import every status token, harness key, and build constant from its owning module; the refresh-workflow assertions read their expected tokens from a source-owned workflow contract or reclassify; the near-identical expectation derives from the property harness's oracle instead of a stored answer; and a test-evidence audit of the node approves.

The isolated test-evidence audit on head `2d1dc4179cc047d0b0404e4b16ac90f3f941406e` (artifact-registry changeset, whose diff touched only the extension-mapping test and its harness in this node) re-raised the topology table, the near-identical fixture, and the scenario and compliance vocabulary as `REJECT` findings `f-001` to `f-004`, and added three subjects outside that diff:

- `tests/test_instruction_block.property.l1.py` copies the reconcile winner tokens `a` and `b`, which the generator spells only inline in `main()`; no source contract exports the winner domain.
- `tests/test_instruction_block.scenario.l1.py::test_symlinked_root_file_becomes_regular_file` asserts that `CLAUDE.md` is a regular file and both files open with the router marker, but never that the shared root body survives — a write that drops the body leaves the linked test passing while the assertion's `then` clause is unfulfilled.
- `tests/test_budget_gate.compliance.l1.py::test_budget_baseline_prefers_the_default_branch_merge_base` hand-rolls the git remote and branch topology inside the test body; that setup policy belongs to the harness that owns `init_git_identity` and `git_commit_at`.
- The four refresh-workflow compliance tests evidence their assertions by reading the authored workflow YAML and asserting conforming substrings only; no violating workflow is exercised, so disabling the checkout, download-verification, or dprint step in the source would not fail a test that reads the same file it guards. The re-audit on head `128a605e5be114220d6f043360a878c73fb92208` raised this beside the nine findings above after the extension-mapping repair landed.

**Settlement condition (extended).** The generator exports the winner domain and the property test imports it; the symlink scenario asserts the shared root body in both files; the budget-gate topology setup moves into the harness. Each rejected verdict is recorded; the merging decision routes a Verifier finding whose subject lies outside the diff here rather than to the merge.

## `/update-instruction-block` Step 5 reads as one paragraph over six topologies

Step 5 of `src/plugins/spec-tree/skills/update-instruction-block/SKILL.md` verifies six distinct first-encounter topologies — an established surface with a valid region, the bootstrap span mapping, one file missing, both files missing, a delegating body adopted, and tracked-versus-untracked recoverability — in one unbroken paragraph. An operator scanning it after a run parses the whole block to find the branch matching their topology. Step 3's ambiguity reports already use the per-branch bullet shape this section wants.

`<examples>` covers stale-router regeneration, delegation adoption, and a recency tie. The one-file-missing seeding topology that Step 4 and Step 5 both name carries no worked example.

**Resolution shape**: restructure Step 5's verification into one bullet per topology, mirroring the nested detection/recommendation/apply shape Step 3's five report kinds now carry, and add a further example showing a repository with only one root instruction file present, its seeded counterpart, and the resulting region wrap.

**Why it is large**: the restructure rewords all six topology branches, not the clauses a delegation change appends, and the missing example is for a topology no delegation change touches. Step 3's five ambiguity bullets are no longer part of this entry: a change edited one of them, which exhausted their deferral, and all five were restructured in that changeset. Both are editorial passes over the whole skill body whose surface is the file's structure rather than any one behavior, and each invalidates the skill-authoring gate for the entire surface — best taken in one pass gated by `skill-auditor` rather than folded into an unrelated behavior change.

**Evidence**: surfaced by `instructions:audit-skills` on the changeset that added delegating-root-file adoption, as `worth-improving` findings on an otherwise approved surface. The same audit's two other findings are resolved in that changeset: the three stop conditions carry explicit `GATE` labels, and the two success criteria that asked for a confirmation now name the diff that decides them.

## `/update-instruction-block` carries three unresolved prose findings

`instructions:skill-auditor`, run on the artifact-registry changeset (which touched only the skill's script and its rendered data file), approved `src/plugins/spec-tree/skills/update-instruction-block/SKILL.md` with three `worth-improving` findings beside the Step 5 restructure recorded above:

- Step 2 states that a budget breach is resolved by shrinking the surface and never by raising a consumer's harness budget, but no step names who shrinks it, what content is eligible, or whether the run stops on a breach; the only action is to relay the line in the closing report.
- The staleness and ambiguity catalogue — diverged, one-sided, malformed fence, unresolved delegation candidate — is restated near-verbatim in `<context>`, the argument section, and Step 2, and the "writes both files, bootstraps a shared region, removes retired `spx/` files" sentence repeats Step 4 and the constraints.
- Success criterion 4 opens by requiring an empty diff outside the router and `shared` bounds between Step 1 and Step 5, while Step 5 describes topologies — an adopt answer, a seeded missing file — where that diff is non-empty by design.

The re-audit on head `26f033c28c6c8a612ec34718950faba6c239725d` (the provider-skill round of the same changeset, which touched only `<dependencies>` and GATE 1) approved the skill and held the catalogue restatement beside two further `worth-improving` findings: `<context>` item 1 and the constraints name "the reading agent" as the subject that reaches a product's commands, where `spx/15-agent-terminology.pdr.md` names Claude; and the third failure mode's lesson — keep every bundled path under this skill's own `${CLAUDE_SKILL_DIR}` — reads against the `select-artifacts` dependency the same round added, although that dependency is a `__file__`-relative import inside the script, the form `spx/13-plugin-and-runtime-conventions.adr.md` prescribes, and not a prose path into another skill.

**Resolution shape**: state the breach disposition explicitly (report-only, or a named remediation step and its owner); state each catalogue definition once in `<context>` and reference it from the workflow; make criterion 4 conditional per topology or state the invariant that holds in every case; name Claude as the reader; and let the third failure mode distinguish a prose path into another skill from a script's provider import. One editorial pass with the Step 5 restructure above, gated by `skill-auditor`.

**Why separate**: each finding is in prose the changeset did not touch, and the merging decision routes a Verifier finding whose subject lies outside the diff here rather than to the merge.

## Root instruction terminology decision

The node concept is "instruction block" across this node, its decision, the generator, the skill and template, the recipes, the workflow, the root instruction-file prose, and `spx/15-validation.enabler/32-runtime-token.enabler/runtime-token.md`. The broader term "guide" remains internally consistent for these distinct surfaces:

- `spx/15-validation.enabler/32-reference-portability.enabler/reference-portability.md` and `outcomeeng/validation/reference_portability.py` — "retired generated guide paths `spx/CLAUDE.md` and `spx/AGENTS.md`".
- `spx/18-plugin-build.enabler/15-build-architecture.adr.md` — "the agent guide read as `CLAUDE.md`/`AGENTS.md`" and the `file`-kind token.
- `spx/21-spec-tree.enabler/76-merge.enabler/merge.md` and the merge skills — "never … editing a generated guide".
- The build runtime-token registry name `root_guide` (`outcomeeng/distribution/build.py`) and its ~60 `{{! file('root_guide') !}}` call sites across every plugin, governed by `spx/18-plugin-build.enabler/21-source-and-templating.enabler/21-runtime-parameterization.enabler`.

Renaming "the agent guide" and `root_guide` requires one product-vocabulary decision followed by a coordinated build-token migration. Revisit this issue before any change renames either term; until that decision, "guide" remains the general description of the root files and `root_guide` remains the build token.

## Generator migration awaits a published SPX CLI capability

`src/plugins/spec-tree/skills/update-instruction-block/scripts/instruction_block.py` runs well past the fifty-line threshold — parse, dotted-version compare, language/harness filtering, router rendering, shared-region parsing with whole-side git-recency reconcile, and biggest-identical-span bootstrap — imported as a module by `outcomeeng_testing/harnesses/instruction_block.py` and exercised by the four `l1` suites here. Past fifty lines `spx/12-shipped-scripting.adr.md` makes a shipped script debt whose logic moves into the SPX CLI once the script proves its value; this generator has proven its value many times over. The render model (router block plus shared regions, reconciled by git recency) keeps that obligation alive even though it deletes the earlier command-slot parser.

The migration requires an unpublished `@outcomeeng/spx` capability and a cross-repo port. Until that capability is published and the consuming floor advances, the generator ships as a stdlib script under `spx/13-plugin-and-runtime-conventions.adr.md`. The migration is filed in the spx CLI's session queue (`outcomeeng/spx`, handoff `2026-07-04_14-49-08`); revisit this issue when that handoff publishes the required capability.
