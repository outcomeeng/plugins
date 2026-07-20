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

## DEBT [evidence]: harness hardcodes the published-manifest path literals

A test-evidence audit surfaced that `outcomeeng_testing/harnesses/agent_conversion.py` declares the
published Codex plugin manifest's path segments as fresh literals (`CODEX_PLUGIN_MANIFEST_PARTS`,
`CODEX_PLUGIN_MANIFEST_FILENAME`) rather than importing the production-owned constants
`CODEX_PLUGIN_SUBDIR_NAME` (`outcomeeng/distribution/contracts.py`) and `CODEX_PLUGIN_MANIFEST`
(`outcomeeng/distribution/marketplace_sources.py`). The compliance test that verifies generated
agents stay out of the published manifest builds its simulated target from these literals, so a
rename of the real manifest subdirectory or filename would leave the test green while it no longer
protects the real location. The sibling harness `outcomeeng_testing/harnesses/src_tree.py` already
imports its layout constants from production; this harness follows the same pattern when the test
infrastructure is next touched. Independent of the marketplace-state assertion alignment, which only
reduced the node's compliance assertion to the manifest-exclusion claim the test already verifies.
