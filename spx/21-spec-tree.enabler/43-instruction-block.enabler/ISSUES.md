# Issues: Instruction Block

## Root instruction terminology decision

The node concept is "instruction block" across this node, its decision, the generator, the skill and template, the recipes, the workflow, the root instruction-file prose, and `spx/15-validation.enabler/32-runtime-token.enabler/runtime-token.md`. The broader term "guide" remains internally consistent for these distinct surfaces:

- `spx/15-validation.enabler/32-reference-portability.enabler/reference-portability.md` and `outcomeeng/validation/reference_portability.py` — "retired generated guide paths `spx/CLAUDE.md` and `spx/AGENTS.md`".
- `spx/18-plugin-build.enabler/15-build-architecture.adr.md` — "the agent guide read as `CLAUDE.md`/`AGENTS.md`" and the `file`-kind token.
- `spx/21-spec-tree.enabler/76-merge.enabler/merge.md` and the merge skills — "never … editing a generated guide".
- The build runtime-token registry name `root_guide` (`outcomeeng/distribution/build.py`) and its ~60 `{{! file('root_guide') !}}` call sites across every plugin, governed by `spx/18-plugin-build.enabler/21-source-and-templating.enabler/21-runtime-parameterization.enabler`.

Renaming "the agent guide" and `root_guide` requires one product-vocabulary decision followed by a coordinated build-token migration. Revisit this issue before any change renames either term; until that decision, "guide" remains the general description of the root files and `root_guide` remains the build token.

## Generator migration awaits a published SPX CLI capability

`src/plugins/spec-tree/skills/update-instruction-block/scripts/instruction_block.py` runs to 1419 lines — parse, dotted-version compare, language/harness filtering, router rendering, shared-region parsing with whole-side git-recency reconcile, and biggest-identical-span bootstrap — imported as a module by `outcomeeng_testing/harnesses/instruction_block.py` and exercised by the four `l1` suites here. Past fifty lines `spx/12-shipped-scripting.adr.md` makes a shipped script debt whose logic moves into the SPX CLI once the script proves its value; this generator has proven its value many times over. The render model (router block plus shared regions, reconciled by git recency) keeps that obligation alive even though it deletes the earlier command-slot parser.

The migration requires an unpublished `@outcomeeng/spx` capability and a cross-repo port. Until that capability is published and the consuming floor advances, the generator ships as a stdlib script under `spx/13-plugin-and-runtime-conventions.adr.md`. The migration is filed in the spx CLI's session queue (`outcomeeng/spx`, handoff `2026-07-04_14-49-08`); revisit this issue when that handoff publishes the required capability.

## The router block carries no size ceiling

The rendered router block is read in full at the start of every session in every consumer repository, because the router instructs the reader to read the entire root instruction file. Its size is therefore an eager per-session cost paid by every installing project, whatever transport, language, or workflow that project uses. No ceiling bounds that cost, and no gate measures it: each methodology advance that adds a section grows the block for every consumer, while sections are removed only incidentally.

**Resolution shape.** Establishing a ceiling is a render-model decision rather than a content edit — it needs a stated budget in `spx/21-spec-tree.enabler/43-instruction-block.enabler/21-render-model.adr.md`, a deterministic measurement over the rendered block, a gate step that fails on breach, and a rule for what a breach requires (moving a section into a skill the router points at, or replacing prose with a reference). Sizing the budget also needs evidence across the harness renders and the enabled-language subsets, since the block a project receives varies with both.

**Evidence.** Named by the `skill-auditor` gate while auditing the added `## Autonomy Boundary` section, which observed the block growing by a whole section with no offsetting removal and no ceiling to measure the growth against.
