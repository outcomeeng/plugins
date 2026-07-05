# Issues: Instruction Block

## Repo-wide "guide" → "instruction" terminology sweep pending

The rename of this node's concept from "guide" to "instruction block" propagated across this node, its decision, the generator, the skill/agent/template, the recipes, the workflow, the root instruction-file prose, and the one lower layer the rename made inconsistent within its own node (`spx/15-validation.enabler/32-runtime-token.enabler/runtime-token.md`, whose assertion described the exemption as the "guide-generation node" while its code already used instruction-block paths).

The broader concept is still named "guide" in nodes and surfaces this change did not touch, each internally consistent (spec ↔ implementation agree), so none is a truth-flows-down violation this change introduced:

- `spx/15-validation.enabler/32-reference-portability.enabler/reference-portability.md` and `outcomeeng/validation/reference_portability.py` — "retired generated guide paths `spx/CLAUDE.md` and `spx/AGENTS.md`".
- `spx/18-plugin-build.enabler/15-build-architecture.adr.md` — "the agent guide read as `CLAUDE.md`/`AGENTS.md`" and the `file`-kind token.
- `spx/21-spec-tree.enabler/76-merging.enabler/merging.md` and the merge skills — "never … editing a generated guide".
- The build runtime-token registry name `root_guide` (`outcomeeng/distribution/build.py`) and its ~60 `{{! file('root_guide') !}}` call sites across every plugin, governed by `spx/18-plugin-build.enabler/21-source-and-templating.enabler/21-runtime-parameterization.enabler`.

Deciding whether "the agent guide" (the CLAUDE.md/AGENTS.md files themselves) and the `root_guide` token should also become "instruction" terminology — versus keeping "guide" as an acceptable general description of those files — is an operator call, and the `root_guide` sweep in particular is a large change to the build token registry and a different governing node. Track as a separate follow-up rather than expanding this changeset.

## Generator complexity belongs in the SPX CLI (accepted debt)

`src/plugins/spec-tree/skills/update-instruction-block/scripts/instruction_block.py` carries complex, isolation-tested logic — parse, dotted-version compare, language/harness filtering, router rendering, shared-region parsing with whole-side git-recency reconcile, and biggest-identical-span bootstrap — imported as a module by `outcomeeng_testing/harnesses/instruction_block.py` and exercised by the four `l1` suites here. Per `spx/12-shipped-scripting.adr.md`, once a shipped script's complexity is proven it belongs in the SPX CLI (tested there, consumed as a trusted third party), not carried in a shipped script. The render model (router block plus shared regions, reconciled by git recency) keeps this tension alive even though it deletes the earlier command-slot parser.

Accepted debt: the migration is blocked on an unpublished `@outcomeeng/spx` capability and a cross-repo port, so the generator ships as a stdlib script under `spx/13-plugin-and-runtime-conventions.adr.md` in the interim. The migration is filed into the spx CLI's own session queue (`outcomeeng/spx`, handoff `2026-07-04_14-49-08`). Resolving the standing tension between `spx/12-shipped-scripting.adr.md` (extract to the CLI) and `spx/13-plugin-and-runtime-conventions.adr.md` (ship Python under `scripts/`) for this component is an operator call tracked with that follow-up.
