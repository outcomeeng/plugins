# Issues: Instruction Block

## `/update-instruction-block` Step 5 reads as one paragraph over six topologies

Step 5 of `src/plugins/spec-tree/skills/update-instruction-block/SKILL.md` verifies six distinct first-encounter topologies — an established surface with a valid region, the bootstrap span mapping, one file missing, both files missing, a delegating body adopted, and tracked-versus-untracked recoverability — in one unbroken paragraph. An operator scanning it after a run parses the whole block to find the branch matching their topology. Step 3's ambiguity reports already use the per-branch bullet shape this section wants.

`<examples>` covers stale-router regeneration, delegation adoption, and a recency tie. The one-file-missing seeding topology that Step 4 and Step 5 both name carries no worked example.

**Resolution shape**: restructure Step 5's verification into one bullet per topology, mirroring Step 3, and add a fourth example showing a repository with only one root instruction file present, its seeded counterpart, and the resulting region wrap.

**Why it is large**: the restructure rewords all six topology branches, not the one clause a delegation change appends, and the missing example is for a topology no delegation change touches. Both are editorial passes over the whole skill body whose surface is the file's structure rather than any one behavior, and each invalidates the skill-authoring gate for the entire surface — best taken in one pass gated by `skill-auditor` rather than folded into an unrelated behavior change.

**Evidence**: surfaced by `instructions:audit-skills` on the changeset that added delegating-root-file adoption, as two `worth-improving` findings on an otherwise approved surface.

## Root instruction terminology decision

The node concept is "instruction block" across this node, its decision, the generator, the skill and template, the recipes, the workflow, the root instruction-file prose, and `spx/15-validation.enabler/32-runtime-token.enabler/runtime-token.md`. The broader term "guide" remains internally consistent for these distinct surfaces:

- `spx/15-validation.enabler/32-reference-portability.enabler/reference-portability.md` and `outcomeeng/validation/reference_portability.py` — "retired generated guide paths `spx/CLAUDE.md` and `spx/AGENTS.md`".
- `spx/18-plugin-build.enabler/15-build-architecture.adr.md` — "the agent guide read as `CLAUDE.md`/`AGENTS.md`" and the `file`-kind token.
- `spx/21-spec-tree.enabler/76-merge.enabler/merge.md` and the merge skills — "never … editing a generated guide".
- The build runtime-token registry name `root_guide` (`outcomeeng/distribution/build.py`) and its ~60 `{{! file('root_guide') !}}` call sites across every plugin, governed by `spx/18-plugin-build.enabler/21-source-and-templating.enabler/21-runtime-parameterization.enabler`.

Renaming "the agent guide" and `root_guide` requires one product-vocabulary decision followed by a coordinated build-token migration. Revisit this issue before any change renames either term; until that decision, "guide" remains the general description of the root files and `root_guide` remains the build token.

## Evidence-run modules hold the predicates their linked tests should own

Four modules — `outcomeeng_testing/harnesses/instruction_block_{scenario,mapping,property,compliance}_evidence.py` — carry every behavioral predicate for this node, while each linked test file asserts only that a case-name list of executed checks equals a declared list. That inverts the predicate seam `spec-tree:test-evidence-standards` `<predicate_seam>` requires: a reader cannot see the pass/fail predicate from the linked test, and inverting any behavioral claim changes a harness rather than the linked test. The same standard's litmus 1 and litmus 2 both fail. `spx/31-outcomeeng.enabler/31-verification.enabler/31-test-verification.enabler/15-test-infrastructure.pdr.md` states the same rule as an audit assertion: infrastructure exposes observations and never calls an assertion API.

The pattern is confined to this node; no other node in the tree uses it, and no decision records it as an accepted shape. `outcomeeng_testing/harnesses/property_evidence.py` is not part of this issue — it owns replayable property-run configuration, which is legitimate harness ownership.

**Resolution shape**: move each `_assert_*` body into its linked test file as a named test function, reduce the evidence modules to observation and resource providers returning the documents, exit codes, and parsed regions the tests judge, and delete the declared/executed case-name bookkeeping once no test depends on it.

**Why it is large**: roughly sixty assertions across four evidence modules and six linked test files, none of which changes product behavior. It is a test-architecture migration whose scope is the node's whole evidence chain, independent of any single generator change, and it is best gated by `test-evidence-auditor` in one pass rather than folded into an unrelated change.

**Evidence**: surfaced while adding delegating-stub evidence for the bootstrap render model. The two scenario cases and one mapping case added in that change are written in the corrected shape — predicates in the linked test, `observe_bootstrap_outcome` returning observations only — so the node now carries both shapes until this migration lands.

## Generator migration awaits a published SPX CLI capability

`src/plugins/spec-tree/skills/update-instruction-block/scripts/instruction_block.py` runs to 1419 lines — parse, dotted-version compare, language/harness filtering, router rendering, shared-region parsing with whole-side git-recency reconcile, and biggest-identical-span bootstrap — imported as a module by `outcomeeng_testing/harnesses/instruction_block.py` and exercised by the four `l1` suites here. Past fifty lines `spx/12-shipped-scripting.adr.md` makes a shipped script debt whose logic moves into the SPX CLI once the script proves its value; this generator has proven its value many times over. The render model (router block plus shared regions, reconciled by git recency) keeps that obligation alive even though it deletes the earlier command-slot parser.

The migration requires an unpublished `@outcomeeng/spx` capability and a cross-repo port. Until that capability is published and the consuming floor advances, the generator ships as a stdlib script under `spx/13-plugin-and-runtime-conventions.adr.md`. The migration is filed in the spx CLI's session queue (`outcomeeng/spx`, handoff `2026-07-04_14-49-08`); revisit this issue when that handoff publishes the required capability.

## The router block carries no size ceiling

The rendered router block is read in full at the start of every session in every consumer repository, because the router instructs the reader to read the entire root instruction file. Its size is therefore an eager per-session cost paid by every installing project, whatever transport, language, or workflow that project uses. No ceiling bounds that cost, and no gate measures it: each methodology advance that adds a section grows the block for every consumer, while sections are removed only incidentally.

**Resolution shape.** Establishing a ceiling is a render-model decision rather than a content edit — it needs a stated budget in `spx/21-spec-tree.enabler/43-instruction-block.enabler/21-render-model.adr.md`, a deterministic measurement over the rendered block, a gate step that fails on breach, and a rule for what a breach requires (moving a section into a skill the router points at, or replacing prose with a reference). Sizing the budget also needs evidence across the harness renders and the enabled-language subsets, since the block a project receives varies with both.

**Evidence.** Named by the `skill-auditor` gate while auditing the added `## Autonomy Boundary` section, which observed the block growing by a whole section with no offsetting removal and no ceiling to measure the growth against.
