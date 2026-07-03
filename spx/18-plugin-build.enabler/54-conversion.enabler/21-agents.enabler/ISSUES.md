# ISSUES — agents conversion enabler

Coordination note; not spec truth.

## DEBT [structure]: split overloaded agent-conversion boundaries

`changes-reviewer` runs `2026-07-03_08-02-43-874-6887784d925b` and `2026-07-03_09-26-23-414-a5d4fd1ca5be` raised debt finding `F-001`: `spx/18-plugin-build.enabler/54-conversion.enabler/21-agents.enabler/agents.md` carries more than roughly seven assertions and mixes independently validated concerns:

- agent conversion output shape
- tool and policy inference
- duplicate-filename installation behavior

The reviewer cited `spx/21-spec-tree.enabler/54-decomposing.enabler/decomposing.md`, whose decomposition rule treats more than roughly seven assertions as a signal for analysis and separates independent concerns when each concern has a meaningful validation boundary.

Revisit condition: when structural work on `spx/18-plugin-build.enabler/54-conversion.enabler/21-agents.enabler` is scheduled, invoke `/decompose` on the agents node. Split the remaining conversion and policy-inference concerns into focused child nodes when the ordering-evidence matrix supports the split.

Deferral reason: this branch targets the bounded generated Codex-agent config enforcement change. The sync-order assertion was re-scoped to `spx/32-distribution.enabler/21-sync.enabler` in this branch; the remaining proposed fix is a tree-structure refactor inside the agents node.

## DEBT [consistency]: reassess `permissionMode` mapping for plugin-shipped agents

`changes-reviewer` run `2026-07-03_15-20-18-970-ba8ba57733e4` and CI review comment `2026-07-03T15:40:38Z` raised that Claude Code plugin-shipped agents do not support `permissionMode` frontmatter, while this node still specifies and tests `permissionMode` to Codex `sandbox_mode` mapping.

Revisit condition: when structural work on `spx/18-plugin-build.enabler/54-conversion.enabler/21-agents.enabler` is scheduled, decide whether `permission_mode`, `PERMISSION_MODE_MAPPINGS`, and the associated mapping tests belong in the plugin-agent conversion path or should be removed in favor of tool-derived Codex policy config only.

Deferral reason: this branch fixes the generated Codex-agent policy enforcement for fields and tool declarations that can appear in the current Claude plugin agent source. Removing or re-scoping `permissionMode` changes the converter's declared frontmatter surface and belongs with the planned agent-conversion boundary split.
