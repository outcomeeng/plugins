---
name: understanding
description: ALWAYS invoke this skill before any spec-tree work to load methodology. NEVER create, read, or modify spec tree files without loading this foundation first.
allowed-tools: Read, Glob, Grep
---

<objective>

Load the Spec Tree methodology into the conversation so all subsequent skills operate from a shared foundation. This is a foundation skill. It is loaded once before any work involving spec tree happens in the session. It is invoked *again* after every compaction. This skill emits a marker that other skills check before starting work.

</objective>

<principles>

1. **TRUTH FLOWS DOWN** — Decisions (ADR: `{slug}.adr.md`/PDR: `{slug}.pdr.md`) decide. Specs (`{slug}.md`) declare in alignment with decisions. Tests derive from specs. Code derives from tests. When layers disagree, the lower layer is in violation. Never change a decision to match a spec. Never change a spec to match tests. Never change tests to match code. Read `references/durable-map.md`.
2. **FOUNDATION, NOT PRODUCT CONTEXT** — This skill loads the foundation of the Spec Tree methodology; it does not load product-specific artifacts. Use `/contextualizing` for target-specific context injection.
3. **LOAD ONCE** — Check for `<SPEC_TREE_FOUNDATION>` marker before loading. If present, skip.
4. **SPECS ARE DECLARATIONS** — The Spec Tree is a durable, declarative map. Nothing moves, nothing closes. Specs declare product truth.
5. **TWO NODE TYPES** — Enablers (infrastructure) and outcomes (hypothesis + assertions). No other node types exist. Read `references/node-types.md`.
6. **ASSERTIONS SPECIFY OUTPUT** — Assertions specify what the software does, locally verifiable by automated tests or agent review. Assertions derive from PDRs/ADRs, not from code or tests.
7. **DETERMINISTIC CONTEXT** — The tree structure defines what context an agent receives. No keyword search, no heuristics. This is handled by `/contextualizing`.
8. **ATEMPORAL VOICE** — Specs state product truth. Never narrate history. Flag temporal language as a quality issue.
9. **COORDINATION NOTES INFORM, SPECS DECLARE** — PLAN.md and ISSUES.md are node-local coordination notes inside the tree. They are committed to git for one reason: future sessions read them on context load. They go stale unless acted upon, so verify a coordination note before it steers work — reconcile it against the specs, decisions (ADR/PDR), assertions, tests, implementation, and the current user intent, then act only where it still holds. A coordination note never declares product truth, architecture, product decisions, assertions, or evidence. `/contextualizing` reads them automatically; conformance checks ignore them. Session files under `.spx/sessions/` are the only spec-tree artifacts not committed to git — `spx session` shares them across worktrees.
10. **FULL PATHS ONLY** — Every node, ADR, and PDR reference uses the full path from `spx/`. Bare names and bare decision filenames are ambiguous because numeric prefixes repeat under different parents.
11. **LOCAL OVERLAYS** — `spx/local/` holds product-specific overlays for coding, architecting, and testing skills. They supplement marketplace skill defaults without modifying the shared plugin. Enumerated by `/contextualizing`; consumed by the relevant language skill.
12. **IMPERFECTIONS ARE TRACKED** — Claude maintains a per-turn imperfection ledger. Safe fixes happen immediately. Unresolved entries either block for operator judgment or are written to the correct artifact: product truth in specs/ADRs/PDRs, workflow rules in methodology, and future-session coordination in PLAN.md or ISSUES.md. Read `references/imperfection-protocol.md`.
13. **VERIFICATION TYPES** — Five verification types establish a node's standing: validation, testing, reviewing, auditing, evaluating. Two orthogonal axes describe each — verdict mode (deterministic or agentic) and purpose (conformance or correctness). Three types back the evidence lanes an assertion carries: `[test]` by testing, `[eval]` by evaluating, `[audit]` by auditing; validation and reviewing are gates that back no lane. Read `references/verification-kinds.md`.

</principles>

<stop_triggers>

About to create or restructure child nodes, assign node indices, decide sibling ordering, or reason about decomposition -> STOP. Invoke `/decomposing`; this foundation only covers the context-loading meaning of existing order.

About to load context for an existing target and explain why lower-index siblings are read -> read `references/ordering-rules.md`.

</stop_triggers>

<workflow>

1. Check conversation for `<SPEC_TREE_FOUNDATION>` marker. If present, skip — already loaded.
2. Read core references (always loaded):
   - `references/durable-map.md` — truth hierarchy, declarative model, atemporal voice, node states
   - `references/node-types.md` — enabler vs outcome, directory structure
   - `references/assertion-types.md` — scenario, mapping, conformance, property, compliance
   - `references/ordering-rules.md` — context-loading meaning of existing numeric prefixes and sibling number scope
   - `references/imperfection-protocol.md` — per-turn ledger, no-origin-distinction rule, closing protocol
   - `references/verification-kinds.md` — the five verification types, verdict mode, purpose, evidence lanes
3. Note operational references (loaded on demand by other skills):
   - `references/what-goes-where.md` — ADR/PDR/spec/test content taxonomy and the mandatory test-infrastructure tree shape (used by `/aligning`, `/decomposing`)
   - `references/excluded-nodes.md` — `spx/EXCLUDE` convention, quality gate integration (used by `/authoring`, `/testing`)
   - PLAN.md / ISSUES.md inside node directories — node-local coordination notes for pending plans and known issues, git-tracked to carry coordination across sessions, verified and reconciled against the durable layers before use, never spec truth (used by `/contextualizing`, `/handoff`)
   - `spx/local/*.md` — product-specific overlays for `/coding-*`, `/architecting-*`, and `/testing-*` skills (enumerated by `/contextualizing`)
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
Loaded: durable-map, node-types, assertion-types, ordering-rules, imperfection-protocol, verification-kinds
Operational references available: what-goes-where, excluded-nodes
Templates available: product, adr, pdr, enabler, outcome
Examples available in: examples/
</SPEC_TREE_FOUNDATION>
```

6. Check the product's spx-level guide for template drift (once per session — the step 1 foundation-marker guard makes this run on first load only). The guide is `spx/CLAUDE.md`, or `spx/AGENTS.md` where that is the real file. The canonical template lives in this skill's own directory at `${CLAUDE_SKILL_DIR}/templates/spx-claude.md`. Read its frontmatter `template_version` and the guide's frontmatter `template_version`, then emit the staleness marker when any of these hold:

   - The guide is absent — emit `status="absent"`.
   - The guide exists but carries no `template_version` frontmatter key — emit `status="stale"`. A pre-render-model or hand-written guide holds no version to compare; treat it as behind the installed template so `/update-spx --name` migrates it onto the render model.
   - The guide's `template_version` is numerically below the installed template's `template_version` — emit `status="stale"`.

   Compare versions by dotted-numeric order, not string inequality: a guide whose `template_version` equals or exceeds the installed one is not stale (a guide ahead of the install would only be downgraded by a re-render), matching the `update-spx` helper's strictly-below `--check` verdict. The marker lets `/handoff` carry the staleness into the persistence proposal so the operator can run `/update-spx` (which re-renders the guide from the installed template):

```text
<SPX_CLAUDE_STALE status="[stale|absent]">
spx/CLAUDE.md [is behind the installed template | is not present]; run /update-spx to reconcile.
</SPX_CLAUDE_STALE>
```

When the guide carries a `template_version` that is not below the installed template's, emit nothing.

</workflow>

<success_criteria>

- [ ] Six core reference files read and understood
- [ ] Operational reference, template, and example locations known
- [ ] `<SPEC_TREE_FOUNDATION>` marker emitted
- [ ] Methodology loaded: truth hierarchy (PDR/ADR → Spec → Test → Code), lower layer is always in violation when layers disagree
- [ ] Methodology loaded: enabler vs outcome distinction, three-part hypothesis structure
- [ ] Methodology loaded: atemporal voice principle, prohibited temporal markers
- [ ] Methodology loaded: five assertion types (scenario, mapping, conformance, property, compliance) and selection criteria
- [ ] Methodology loaded: existing lower-index siblings are read as constraining context; same-index and higher-index siblings are listed but not read as target constraints
- [ ] Methodology loaded: all node, ADR, and PDR references use full paths from `spx/`
- [ ] Methodology loaded: coordination notes (PLAN.md, ISSUES.md) are node-local, git-tracked only to carry coordination across sessions, stale-prone, verified and reconciled against specs/decisions/assertions/tests/implementation/user intent before use, and never spec truth; session files under `.spx/sessions/` are the only spec-tree artifacts that live outside git
- [ ] Methodology loaded: `spx/local/` overlays supplement coding/architecting/testing skills per product without modifying the shared marketplace
- [ ] Methodology loaded: imperfection ledger is maintained per-turn; unresolved entries are fixed, escalated for operator judgment, or written to the correct durable artifact
- [ ] Methodology loaded: five verification types (validation, testing, reviewing, auditing, evaluating) across verdict mode (deterministic/agentic) and purpose (conformance/correctness); three back evidence lanes (`[test]`, `[eval]`, `[audit]`)
- [ ] `spx/CLAUDE.md` template-drift check run once per session; `<SPX_CLAUDE_STALE>` marker emitted when the product guide is absent (`status="absent"`), exists but carries no `template_version` key (`status="stale"`), or its `template_version` is numerically below the installed template (`status="stale"`)

</success_criteria>
