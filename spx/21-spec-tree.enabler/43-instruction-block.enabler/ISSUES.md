# Issues: Instruction Block

## Repo-wide "guide" → "instruction" terminology sweep pending

The rename of this node's concept from "guide" to "instruction block" propagated across this node, its decision, the generator, the skill/agent/template, the recipes, the workflow, the root instruction-file prose, and the one lower layer the rename made inconsistent within its own node (`spx/15-validation.enabler/32-runtime-token.enabler/runtime-token.md`, whose assertion described the exemption as the "guide-generation node" while its code already used instruction-block paths).

The broader concept is still named "guide" in nodes and surfaces this change did not touch, each internally consistent (spec ↔ implementation agree), so none is a truth-flows-down violation this change introduced:

- `spx/15-validation.enabler/32-reference-portability.enabler/reference-portability.md` and `outcomeeng/validation/reference_portability.py` — "retired generated guide paths `spx/CLAUDE.md` and `spx/AGENTS.md`".
- `spx/18-plugin-build.enabler/15-build-architecture.adr.md` — "the agent guide read as `CLAUDE.md`/`AGENTS.md`" and the `file`-kind token.
- `spx/21-spec-tree.enabler/76-merging.enabler/merging.md` and the merge skills — "never … editing a generated guide".
- The build runtime-token registry name `root_guide` (`outcomeeng/distribution/build.py`) and its ~60 `{{! file('root_guide') !}}` call sites across every plugin, governed by `spx/18-plugin-build.enabler/21-source-and-templating.enabler/21-runtime-parameterization.enabler`.

Deciding whether "the agent guide" (the CLAUDE.md/AGENTS.md files themselves) and the `root_guide` token should also become "instruction" terminology — versus keeping "guide" as an acceptable general description of those files — is an operator call, and the `root_guide` sweep in particular is a large change to the build token registry and a different governing node. Track as a separate follow-up rather than expanding this changeset.
