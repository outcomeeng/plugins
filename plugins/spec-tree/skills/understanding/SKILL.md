---
name: understanding
description: >-
  ALWAYS invoke this skill before any spec-tree work to load methodology.
  NEVER create, read, or modify spec tree files without loading this foundation first.
allowed-tools: Read, Glob, Grep
---

<objective>

Load the Spec Tree methodology into the conversation so all subsequent skills operate from a shared foundation. This is a foundation skill — it loads once and emits a marker that other skills check before starting work.

</objective>

<principles>

1. **TRUTH FLOWS DOWN** — Specs declare. Tests derive from specs. Code derives from tests. When layers disagree, the lower layer is in violation. Never weaken a spec to match code or tests. Read `references/durable-map.md`.
2. **FOUNDATION, NOT CONTEXT** — This skill loads methodology; it does not load project-specific artifacts. Use `/contextualizing` for target-specific context injection.
3. **LOAD ONCE** — Check for `<SPEC_TREE_FOUNDATION>` marker before loading. If present, skip.
4. **SPECS ARE DECLARATIONS** — The Spec Tree is a durable, declarative map. Nothing moves, nothing closes. Specs declare product truth.
5. **TWO NODE TYPES** — Enablers (infrastructure) and outcomes (hypothesis + assertions). No other node types exist. Read `references/node-types.md`.
6. **ASSERTIONS SPECIFY OUTPUT** — Assertions specify what the software does, locally verifiable by automated tests or agent review. Assertions derive from PDRs/ADRs, not from code or tests.
7. **DETERMINISTIC CONTEXT** — The tree structure defines what context an agent receives. No keyword search, no heuristics. This is handled by `/contextualizing`.
8. **ATEMPORAL VOICE** — Specs state product truth. Never narrate history. Flag temporal language as a quality issue.
9. **ESCAPE HATCHES ARE EPHEMERAL** — PLAN.md and ISSUES.md are non-durable files placed in node directories by `/handing-off`. They record deferred plans and known issues. They are coordination artifacts, not spec truth — discoverable via `/contextualizing` but excluded from conformance checks.
10. **LOCAL OVERLAYS** — `spx/local/` holds project-specific overlays for coding, architecting, and testing skills. They supplement marketplace skill defaults without modifying the shared plugin. Enumerated by `/contextualizing`; consumed by the relevant language skill.

</principles>

<stop_triggers>

About to reason about index placement, sparse integer ordering, dependency direction, same-index sibling independence, unified sibling number space, midpoint insertion, or fractional indexing without `references/ordering-rules.md` loaded -> STOP. Read it before making any placement claim.

</stop_triggers>

<workflow>

1. Check conversation for `<SPEC_TREE_FOUNDATION>` marker. If present, skip — already loaded.
2. Read core references (always loaded):
   - `references/durable-map.md` — truth hierarchy, declarative model, atemporal voice, node states
   - `references/node-types.md` — enabler vs outcome, directory structure
   - `references/assertion-types.md` — scenario, mapping, conformance, property, compliance
   - `references/ordering-rules.md` — sparse integer ordering, dependency direction, unified sibling number space, insertion rules
3. Note operational references (loaded on demand by other skills):
   - `references/decomposition-semantics.md` — when to nest, depth heuristics (used by `/decomposing`)
   - `references/what-goes-where.md` — ADR/PDR/spec/test content taxonomy (used by `/aligning`)
   - `references/excluded-nodes.md` — `spx/EXCLUDE` convention, quality gate integration (used by `/authoring`, `/testing`)
   - PLAN.md / ISSUES.md inside node directories — non-durable escape hatches; ephemeral coordination artifacts (used by `/contextualizing`, `/handing-off`)
   - `spx/local/*.md` — project-specific overlays for `/coding-*`, `/architecting-*`, and `/testing-*` skills (enumerated by `/contextualizing`)
4. Note template and example locations (read only when authoring):
   - `templates/product/product-name.product.md`
   - `templates/decisions/decision-name.adr.md`
   - `templates/decisions/decision-name.pdr.md`
   - `templates/nodes/enabler-name.md`
   - `templates/nodes/outcome-name.md`
   - `examples/` — concrete filled specs (read when you need to see what a completed spec looks like)
5. Emit the `<SPEC_TREE_FOUNDATION>` marker:

```text
<SPEC_TREE_FOUNDATION>
Loaded: durable-map, node-types, assertion-types, ordering-rules
Operational references available: decomposition-semantics, what-goes-where, excluded-nodes
Templates available: product, adr, pdr, enabler, outcome
Examples available in: examples/
</SPEC_TREE_FOUNDATION>
```

</workflow>

<success_criteria>

- [ ] Four core reference files read and understood
- [ ] Operational reference, template, and example locations known
- [ ] `<SPEC_TREE_FOUNDATION>` marker emitted
- [ ] Methodology loaded: truth hierarchy (PDR/ADR → Spec → Test → Code), lower layer is always in violation when layers disagree
- [ ] Methodology loaded: enabler vs outcome distinction, three-part hypothesis structure
- [ ] Methodology loaded: atemporal voice principle, prohibited temporal markers
- [ ] Methodology loaded: five assertion types (scenario, mapping, conformance, property, compliance) and selection criteria
- [ ] Methodology loaded: lower index constrains higher index and descendants; same index means independent siblings; fractional indexing is the escape hatch when integer gaps are exhausted
- [ ] Methodology loaded: escape hatches (PLAN.md, ISSUES.md) are ephemeral coordination artifacts, not durable spec truth
- [ ] Methodology loaded: `spx/local/` overlays supplement coding/architecting/testing skills per project without modifying the shared marketplace

</success_criteria>
