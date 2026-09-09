---
id: 01a0ebba-5f64-73f1-8795-b55a3cecafd6
malleability: spec
---

# Decomposing

PROVIDES structured composition analysis from a product or node address and its durable product truth
SO THAT all spec authors
CAN compose top-level product children or split nodes into focused children with correct kinds, ownership boundaries, and prerequisite order

## Assertions

### Compliance

- ALWAYS: accept `spx/` for top-level composition and a canonical full `spx/...` node address for child decomposition; load the complete context first, reconcile any `ISSUES.md` and prior-form `PLAN.md` as fallible inputs, and derive structure only from product truth and settled operator intent ([audit])
- ALWAYS: decompose on a countable trigger — two or more distinct concepts, present or foreseen, or too many assertions for one node — and keep one coherent concept whole regardless of cosmetic symmetry or separate implementation layers ([audit])
- ALWAYS: classify each candidate through the ordered kind procedure product, variant, substrate, surface, interface, domain, capability; enforce the containment table and kind-specific opening, and never place a provider more outward than its consumer ([audit])
- ALWAYS: resolve the owning node and subtree reach of every ADR or PDR before `/author` writes it whenever decomposition affects concept ownership, node boundaries, placement, or context reach ([audit])
- ALWAYS: assign each node and decision index from its own prerequisites after checking kind order, place prerequisites before consumers, record a falsifiable reason for every named dependency, and treat numeric separation alone as no dependency; reuse an existing index only when it satisfies prerequisite and decision-scope constraints, with no next-free default ([audit])
- ALWAYS: redistribute each assertion to the node that owns its meaning, retain class-wide assertions on the parent, preserve every evidence link, and prove assertion-count conservation across the move; parent specs state their class contract without enumerating children ([audit])
- ALWAYS: write every composed node as `{index}-{slug}.{kind}/{slug}.spec.md` with a UUIDv7 `id`, the selected `malleability`, and the kind opening, then run the product's declared author and verify commands — including `spx validation markdown` and `spx spec status --format json` — and stop on any nonzero result ([audit])
