# Decomposing

PROVIDES structured composition analysis from a target address, durable spec content, and node-local coordination notes
SO THAT all spec authors
CAN compose top-level product children or split nodes into focused children with clear scope boundaries and explicit ordering evidence

## Assertions

### Compliance

- ALWAYS: treat more than roughly 7 assertions as a signal requiring decomposition analysis, not as an automatic split ([audit])
- ALWAYS: separate independent concerns into separate child nodes when each concern has a meaningful validation boundary ([audit])
- ALWAYS: accept `spx/` as the product-root target for top-level composition and normal node addresses for child decomposition ([audit])
- ALWAYS: load root product context, ancestor constraints, target spec when present, existing children and siblings, and local `PLAN.md` or `ISSUES.md` before proposing child structure ([audit])
- ALWAYS: own decision-placement scoping when a requested ADR/PDR location depends on concept ownership, node renaming, node splitting, parent/child boundaries, or context-loading reach, returning the owning directory and scope boundary before `/author` writes the decision record ([audit])
- ALWAYS: verify completeness across scope boundary, decision placement, delivery substrate, evidence strategy, architecture, enabler/outcome typing, ordering evidence, index budget, and refactor issues before proposing child nodes; use `/interview` with decomposition-specific coverage when any area is unclear ([audit])
- ALWAYS: assign different sibling indices only when ordering evidence proves a predecessor constrains a successor; provider/consumer service flow, logical prerequisites, vertical-slice construction dependencies, shared substrate, and feature-extension dependencies are valid evidence ([audit])
- ALWAYS: keep roadmap priority, chronology, theme grouping, and explanation order unordered or same-index unless they also provide concrete ordering evidence ([audit])
- ALWAYS: record an ordering-evidence matrix before index assignment, naming predecessor, evidence type, constraining contribution, successor, required assertion or workflow, and consequence if absent ([audit])
- ALWAYS: state the context-loading consequence of an index at assignment time — a child assigned a higher index than a sibling makes context loading read that lower-index sibling as constraining context for it, while a same-index sibling is an independent peer — so a different-index assignment stands only when the ordering-evidence matrix proves the predecessor constrains the successor ([audit])
- ALWAYS: state every proposed sibling pair as ordered, same-index, or unordered before assigning any index, naming the ordering-evidence matrix row that proves each different-index pair ([audit])
- NEVER: treat an existing lower-index sibling as a precedent for the next sparse slot — a new child takes the same index as an existing sibling unless ordering evidence proves one constrains the other ([audit])
- ALWAYS: allocate sparse index space according to the decomposition horizon — full decomposition may use the full range; the first slice of a larger concern uses the first half or quarter and records the reserved horizon in `PLAN.md` ([audit])
- ALWAYS: reference nodes, ADRs, and PDRs by full path from `spx/` in plans, matrices, issues, and generated specs — bare names and bare decision filenames are ambiguous because numeric prefixes are sibling-local ([audit])
- NEVER: decompose a node with fewer than 4 assertions unless the assertions cover independent concerns ([audit])
