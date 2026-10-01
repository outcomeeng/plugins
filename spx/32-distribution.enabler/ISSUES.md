# ISSUES -- distribution enabler

Coordination note; not spec truth.

## DEBT [structure]: split distribution workflow boundaries

Implementation audit `019f2777-97ab-7a03-89d3-30e61c4c820e` raised a decomposition finding: `spx/32-distribution.enabler/distribution.md` carries more than roughly seven assertions and mixes independently validated concerns:

- skill collection and metadata extraction
- target cleanup and copy behavior
- workflow compliance for distribution triggers and interpreter selection

The audit cited `spx/21-spec-tree.enabler/54-decomposing.enabler/decomposing.md`, whose decomposition rule treats more than roughly seven assertions as a signal for analysis and separates independent concerns when each concern has a meaningful validation boundary.

Revisit condition: when structural work on `spx/32-distribution.enabler` is scheduled, invoke `/decompose` on the distribution node. Split the skill-copying behavior and workflow-compliance concerns into focused child nodes when the ordering-evidence matrix supports the split.

Chosen handling: this branch records the structure debt and continues the generated Codex-agent config enforcement change. The branch does not move or rewrite the existing distribution assertions.
