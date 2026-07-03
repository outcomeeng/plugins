# ISSUES -- sync enabler

Coordination note; not spec truth.

## DEBT [structure]: split sync orchestration boundaries

Implementation audit `019f2777-97ab-7a03-89d3-30e61c4c820e` raised a decomposition finding: `spx/32-distribution.enabler/21-sync.enabler/sync.md` carries more than roughly seven assertions and mixes independently validated concerns:

- prerequisite tool checks
- marketplace source reconciliation
- distribution-change detection
- ordered sync-step orchestration
- named forbidden-step compliance

The audit cited `spx/21-spec-tree.enabler/54-decomposing.enabler/decomposing.md`, whose decomposition rule treats more than roughly seven assertions as a signal for analysis and separates independent concerns when each concern has a meaningful validation boundary.

Revisit condition: when structural work on `spx/32-distribution.enabler/21-sync.enabler` is scheduled, invoke `/decompose` on the sync node. Split prerequisite checks, reconciliation, change detection, and orchestration sequencing into focused child nodes when the ordering-evidence matrix supports the split.

Chosen handling: this branch records the structure debt and continues the generated Codex-agent config enforcement change. The branch does not move or rewrite the existing sync assertions.
