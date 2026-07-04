# ISSUES -- sync enabler

Coordination note; not spec truth.

## DEBT [structure]: split sync orchestration boundaries

Implementation audit `019f2777-97ab-7a03-89d3-30e61c4c820e` raised a decomposition finding: `spx/32-distribution.enabler/21-sync.enabler/sync.md` carries more than roughly seven assertions and mixes independently validated concerns:

- prerequisite tool checks
- marketplace source reconciliation
- distribution-change detection
- Codex cache topology health checks
- file-backed single-flight coordination
- ordered sync-step orchestration
- named forbidden-step compliance

The audit cited `spx/21-spec-tree.enabler/54-decomposing.enabler/decomposing.md`, whose decomposition rule treats more than roughly seven assertions as a signal for analysis and separates independent concerns when each concern has a meaningful validation boundary.

Revisit condition: when structural work on `spx/32-distribution.enabler/21-sync.enabler` is scheduled, invoke `/decompose` on the sync node. Split prerequisite checks, reconciliation, change detection, topology/single-flight coordination, and orchestration sequencing into focused child nodes when the ordering-evidence matrix supports the split.

Triggered again: PR #402 added topology health inspection and single-flight repair coordination to this node, increasing the assertion count and adding another independently validated concern. The current branch keeps the behavior change in place and updates this tracking note; the next structural pass should run `/decompose` before adding more sync orchestration concerns.
