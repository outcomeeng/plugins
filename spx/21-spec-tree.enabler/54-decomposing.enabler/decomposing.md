# Decomposing

PROVIDES structured composition analysis from a target address, durable spec content, and node-local coordination notes
SO THAT all spec authors
CAN compose top-level product children or split nodes into focused children with clear scope boundaries and explicit ordering evidence

## Assertions

### Compliance

- ALWAYS: treat more than roughly 7 assertions as a signal requiring decomposition analysis, not as an automatic split ([review])
- ALWAYS: separate independent concerns into separate child nodes when each concern has a meaningful validation boundary ([review])
- ALWAYS: accept `spx/` as the product-root target for top-level composition and normal node addresses for child decomposition ([review])
- ALWAYS: load root product context, ancestor constraints, target spec when present, existing children and siblings, and local `PLAN.md` or `ISSUES.md` before proposing child structure ([review])
- ALWAYS: verify completeness across scope boundary, delivery substrate, evidence strategy, architecture, enabler/outcome typing, ordering evidence, index budget, and refactor issues before proposing child nodes; use `/interviewing` with decomposition-specific coverage when any area is unclear ([review])
- ALWAYS: assign different sibling indices only when ordering evidence proves a predecessor constrains a successor; provider/consumer service flow, logical prerequisites, vertical-slice construction dependencies, shared substrate, and feature-extension dependencies are valid evidence ([review])
- ALWAYS: keep roadmap priority, chronology, theme grouping, and explanation order unordered or same-index unless they also provide concrete ordering evidence ([review])
- ALWAYS: record an ordering-evidence matrix before index assignment, naming predecessor, evidence type, constraining contribution, successor, required assertion or workflow, and consequence if absent ([review])
- ALWAYS: allocate sparse index space according to the decomposition horizon — full decomposition may use the full range; the first slice of a larger concern uses the first half or quarter and records the reserved horizon in `PLAN.md` ([review])
- ALWAYS: reference nodes, ADRs, and PDRs by full path from `spx/` in plans, matrices, issues, and generated specs — bare names and bare decision filenames are ambiguous because numeric prefixes are sibling-local ([review])
- NEVER: decompose a node with fewer than 4 assertions unless the assertions cover independent concerns ([review])
