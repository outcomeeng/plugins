---
name: understand
description: ALWAYS invoke this skill before any spec-tree work to load methodology. NEVER create, read, or modify spec tree files without loading this foundation first.
allowed-tools: Read, Glob, Grep
---

<objective>

The Spec Tree methodology is loaded into the conversation as a shared foundation: the six core reference files are read and the `<SPEC_TREE_FOUNDATION>` marker is emitted, so every subsequent skill operates from the same truth hierarchy, node types, assertion types, ordering rules, imperfection protocol, and verification kinds. This is a foundation skill, loaded once before any spec-tree work in the session and again after every compaction; subsequent skills read the emitted marker before starting work.

</objective>

<principles>

1. **TRUTH FLOWS DOWN** — Decisions (ADR: `{slug}.adr.md`/PDR: `{slug}.pdr.md`) decide. Specs (`{slug}.md`) declare in alignment with decisions. Tests derive from specs. Code derives from tests. When layers disagree, the lower layer is in violation. Never change a decision to match a spec. Never change a spec to match tests. Never change tests to match code. Read `references/durable-map.md`.
2. **FOUNDATION, NOT PRODUCT CONTEXT** — This skill loads the foundation of the Spec Tree methodology; it does not load product-specific artifacts. Use `/contextualize` for target-specific context injection.
3. **LOAD ONCE** — Check for `<SPEC_TREE_FOUNDATION>` marker before loading. If present, skip.
4. **SPECS ARE DECLARATIONS** — The Spec Tree is a durable, declarative map. Nothing moves, nothing closes. Specs declare product truth.
5. **TWO NODE TYPES** — Enablers (infrastructure) and outcomes (hypothesis + assertions). No other node types exist. Read `references/node-types.md`.
6. **ASSERTIONS SPECIFY OUTPUT** — Assertions specify what the software does, locally verifiable by automated tests or agent review. Assertions derive from PDRs/ADRs, not from code or tests.
7. **DETERMINISTIC CONTEXT** — The tree structure defines what context Claude receives. No keyword search, no heuristics. This is handled by `/contextualize`, whose context marker carries both document context and lifecycle continuation state.
8. **ATEMPORAL VOICE** — Specs state product truth. Never narrate history. Flag temporal language as a quality issue.
9. **COORDINATION NOTES INFORM, SPECS DECLARE** — PLAN.md and ISSUES.md are node-local coordination notes inside the tree. They are committed to git for one reason: future sessions read them on context load. They go stale unless acted upon, so verify a coordination note before it steers work — reconcile it against the specs, decisions (ADR/PDR), assertions, tests, implementation, and the current user intent, then act only where it still holds. A coordination note never declares product truth, architecture, product decisions, assertions, or evidence. `/contextualize` reads them automatically; conformance checks ignore them. Session files under `.spx/sessions/` are the only spec-tree artifacts not committed to git — `spx session` shares them across worktrees.
10. **FULL PATHS ONLY** — Every node, ADR, and PDR reference uses the full path from `spx/`. Bare names and bare decision filenames are ambiguous because numeric prefixes repeat under different parents.
11. **LOCAL OVERLAYS** — `spx/local/` holds product-specific overlays for coding, architecting, testing, and lifecycle skills. They supplement marketplace skill defaults without modifying the shared plugin. Enumerated by `/contextualize`; consumed by the relevant skill.
12. **LOCAL LIFECYCLE ROUTE** — changes destined for the default branch route through `/merge`, the transport dispatcher: it reads `spx/local/merging.md`, classifies the changeset, selects the merge transport, and delegates to the selected transport's skills. `spx/local/merging.md` may refine the selection and configure transport behavior. Read it when present.
13. **DEFAULT-BRANCH WORK ENDS AT MERGE** — For changes destined for the default branch, delivered value is value merged to the default branch on origin through `/merge`. Local implementation and verification are progress, not completion; a branch with commits ahead of its resolved base is unfinished even when the working tree is clean. A created branch, a local commit, a pushed branch, an opened PR, or a clean worktree is a transport checkpoint, never a completion boundary. After deterministic verification passes and any required local review or audit gates pass, continue into `/merge` and follow the selected transport until the change reaches the default branch on origin, or until an explicit lifecycle gate stops with no independent local action remaining without operator input or an external-state change. After committing or pushing a default-branch-destined changeset, invoke `/merge` in the same turn unless the user explicitly limited the task to proposal, analysis, review, branch-only, or local-only work. Do not stop after "implemented", "validated", "tests passed", "committed", or "pushed" when the user asked to make the change.
14. **IMPERFECTIONS ARE TRACKED** — Claude maintains a per-turn imperfection ledger. Safe fixes happen immediately. Unresolved entries either block for operator judgment or are written to the correct artifact: product truth in specs/ADRs/PDRs, workflow rules in methodology, and future-session coordination in PLAN.md or ISSUES.md. Read `references/imperfection-protocol.md`.
15. **VERIFICATION TYPES** — Five verification types establish a node's standing: validation, testing, reviewing, auditing, evaluating. Two orthogonal axes describe each — verdict mode (deterministic or agentic) and purpose (conformance or correctness). Three types back the tag an assertion carries: `[test]` by testing, `[eval]` by evaluating, `[audit]` by auditing; validation and reviewing are gates that back no tag. Read `references/verification-kinds.md`.

</principles>

<stop_triggers>

About to create or restructure child nodes, assign node indices, decide sibling ordering, or reason about decomposition -> STOP. Invoke `/decompose`; this foundation only covers the context-loading meaning of existing order.

About to load context for an existing target and explain why lower-index siblings are read -> read `references/ordering-rules.md`.

</stop_triggers>

<workflow>

1. Check conversation for `<SPEC_TREE_FOUNDATION>` marker. If present, skip — already loaded.
2. Read core references (always loaded):
   - `references/durable-map.md` — truth hierarchy, future product truth, decision-to-spec alignment, declarative model, atemporal voice, node states
   - `references/node-types.md` — enabler vs outcome, directory structure
   - `references/assertion-types.md` — scenario, mapping, conformance, property, compliance
   - `references/ordering-rules.md` — context-loading meaning of existing numeric prefixes and sibling number scope
   - `references/imperfection-protocol.md` — per-turn ledger, no-origin-distinction rule, closing protocol
   - `references/verification-kinds.md` — the five verification types, verdict mode, purpose, assertion tags
3. Note operational references (loaded on demand by other skills):
   - `references/what-goes-where.md` — ADR/PDR/spec/test content taxonomy and test-infrastructure governance and placement rules (used by `/align`, `/decompose`)
   - `references/excluded-nodes.md` — `spx/EXCLUDE` convention, quality gate integration (used by `/author`, `/test`)
   - PLAN.md / ISSUES.md inside node directories — node-local coordination notes for pending plans and known issues, git-tracked to carry coordination across sessions, verified and reconciled against the durable layers before use, never spec truth (used by `/contextualize`, `/handoff`)
   - `spx/local/*.md` — product-specific overlays for `/code-*`, `/architect-*`, `/test-*`, and lifecycle skills (enumerated by `/contextualize`)
4. Check for local lifecycle routing:
   - Changes destined for the default branch route through `/merge`, the transport dispatcher. It reads `spx/local/merging.md`, classifies the changeset, selects the merge transport, and delegates to the selected transport's skills.
   - If `spx/local/merging.md` exists at the repository root, read it. Its declarations refine transport selection and lifecycle configuration.
5. Enforce the default-branch completion boundary:
   - If the work changes files and is destined for the default branch, continue after verification into `/merge`.
   - After any successful commit or push of a changeset that changes specs, decisions, tests, implementation, or docs, immediately invoke `/merge` unless the user explicitly limited the task to proposal, analysis, review, branch-only, or local-only work.
   - A request to create a branch, preserve a branch, or push a branch does not by itself scope out `/merge`; it only names the transport state to create before continuing.
   - A clean working tree is still unfinished when the branch carries committed changes ahead of its resolved base.
   - Passing validation, tests, review, or audit gates is progress evidence, not completion.
   - A status assessment may report local evidence, then continue through `/merge` when the branch carries committed changes and the user has not explicitly limited the task.
   - Terse follow-ups such as "so?", "continue", "ship it", "finish", or "go on" mean continue the already-governed merge lifecycle.
   - Stop before `/merge` only when the user explicitly limited the task to proposal, analysis, review, branch-only, or local-only work.
   - A blocker exists only after every independent action that does not require operator input is complete: the applicable edits are made, deterministic verification and required local review or audit gates have run or produced concrete failing evidence, and all work that can be committed without the answer is committed on a local branch.
   - Until no independent work remains, continue doing work that does not depend on the answer or removed blocker. When no independent work remains, report the exact blocker, the evidence, and the next operator decision needed.
6. Note template and example locations (read only when authoring):
   - `templates/product/product-name.product.md`
   - `templates/decisions/decision-name.adr.md`
   - `templates/decisions/decision-name.pdr.md`
   - `templates/nodes/enabler-name.md`
   - `templates/nodes/outcome-name.md`
   - `examples/` — concrete filled specs (read to see what a completed spec looks like)
7. Emit the `<SPEC_TREE_FOUNDATION>` marker:

```text
<SPEC_TREE_FOUNDATION>
Loaded: durable-map, node-types, assertion-types, ordering-rules, imperfection-protocol, verification-kinds
Operational references available: what-goes-where, excluded-nodes
Local lifecycle route: changes route through /merge (reads spx/local/merging.md, classifies the changeset, selects the merge transport, delegates to the selected transport)
Default-branch completion boundary: delivered value is value merged to the default branch on origin through /merge; verified local changes and clean branches with commits ahead of base remain unfinished until they reach the default branch on origin, unless the user explicitly limited the task to proposal, analysis, review, branch-only, or local-only work or stopped at an explicit lifecycle gate with no independent local action remaining
Templates available: product, adr, pdr, enabler, outcome
Examples available in: examples/
</SPEC_TREE_FOUNDATION>
```

8. Check the product's spx-level guide for template drift (once per session — the step 1 foundation-marker guard makes this run on first load only). The guide is `spx/CLAUDE.md`, or `spx/AGENTS.md` where that is the real file. The canonical template lives in this skill's own directory at `${CLAUDE_SKILL_DIR}/templates/spx-claude.md`. Read its frontmatter `template_version`, the guide's frontmatter `template_version` and `languages`, and detect the languages the project actually uses (from its spec-tree test files and enabled language plugins). Emit the staleness marker when any of these hold:

   - The guide is absent — emit `status="absent"`.
   - The guide exists but carries no `template_version` frontmatter key — emit `status="stale"`. A pre-render-model or hand-written guide holds no version to compare; treat it as behind the installed template so `/update-spx` re-renders it onto the render model.
   - The guide's `template_version` is numerically below the installed template's `template_version` — emit `status="stale"`.
   - The guide's recorded `languages` differ from the languages the project actually uses — emit `status="stale"`. The render scopes the guide to the project's languages, so a drift (a language added or dropped since the last render) leaves the guide carrying the wrong language sections.

   Compare versions by dotted-numeric order, not string inequality: a guide whose `template_version` equals or exceeds the installed one is not stale (a guide ahead of the install would only be downgraded by a re-render), matching the `update-spx` helper's strictly-below `--check` verdict. The marker lets `/handoff` carry the staleness into the persistence proposal so the operator can run `/update-spx` (which re-renders the guide from the installed template, scoped to the detected languages):

```text
<SPX_CLAUDE_STALE status="[stale|absent]">
spx/CLAUDE.md [is behind the installed template or scoped to the wrong languages | is not present]; run /update-spx to reconcile.
</SPX_CLAUDE_STALE>
```

When the guide carries a `template_version` not below the installed template's and records the languages the project uses, emit nothing.

</workflow>

<failure_modes>

**Failure: Claude reported completion at a pushed branch.**

What happened: Claude created a branch, validated the change, committed, and pushed it, then reported the task complete without invoking `/merge`.

Why it failed: Claude treated the pushed branch as delivered value. In the Spec Tree lifecycle a pushed branch is review-ready state, not delivered value — delivered value is the change merged to the default branch on origin through `/merge`.

How to avoid: After a commit or push succeeds, check whether the user explicitly scoped the task to branch-only, local-only, proposal, or review. If not, invoke `/merge` immediately and let it select the transport.

</failure_modes>

<success_criteria>

- [ ] Six core reference files read and understood
- [ ] Operational reference, template, and example locations known
- [ ] Local lifecycle route known: changes route through `/merge`, which reads `spx/local/merging.md`, classifies the changeset, selects the merge transport, and delegates to the selected transport
- [ ] `<SPEC_TREE_FOUNDATION>` marker emitted
- [ ] Methodology loaded: truth hierarchy (PDR/ADR → Spec → Test → Code), lower layer is always in violation when layers disagree
- [ ] Methodology loaded: PDRs, ADRs, product specs, and ancestor specs may declare future product truth ahead of implementation; current code shape is lower-layer evidence, not a reason to weaken the declaration
- [ ] Methodology loaded: higher-level artifact changes require lower-level spec alignment in the same changeset so the declaration has an immediate path down the tree
- [ ] Methodology loaded: enabler vs outcome distinction, three-part hypothesis structure
- [ ] Methodology loaded: atemporal voice principle, prohibited temporal markers
- [ ] Methodology loaded: five assertion types (scenario, mapping, conformance, property, compliance) and selection criteria
- [ ] Methodology loaded: existing lower-index siblings are read as constraining context; same-index and higher-index siblings are listed but not read as target constraints
- [ ] Methodology loaded: `/contextualize` emits lifecycle continuation state, including the default-branch completion boundary and governed `/merge` continuation
- [ ] Methodology loaded: all node, ADR, and PDR references use full paths from `spx/`
- [ ] Methodology loaded: `PLAN.md` anchors pending downstream implementation created by higher-level truth; `ISSUES.md` records known defects or contradictions; neither declares spec truth
- [ ] Methodology loaded: `spx/EXCLUDE` scopes specified nodes with tests and absent implementation; it is not a conceptual workaround for product-decision gaps
- [ ] Methodology loaded: coordination notes (PLAN.md, ISSUES.md) are node-local, git-tracked only to carry coordination across sessions, stale-prone, verified and reconciled against specs/decisions/assertions/tests/implementation/user intent before use, and never spec truth; session files under `.spx/sessions/` are the only spec-tree artifacts that live outside git
- [ ] Methodology loaded: `spx/local/` overlays supplement coding/architecting/test/lifecycle skills per product without modifying the shared marketplace
- [ ] Methodology loaded: default-branch work is complete only when it reaches the default branch on origin through `/merge`, unless the user explicitly limited the task to proposal, analysis, review, branch-only, or local-only work or an explicit lifecycle gate stops with no independent local action remaining without operator input or an external-state change
- [ ] Methodology loaded: a clean working tree with committed changes ahead of the resolved base is unfinished, and passing validation, tests, review, or audit gates are progress gates, not a stopping point, for changes destined for the default branch
- [ ] Methodology loaded: imperfection ledger is maintained per-turn; unresolved entries are fixed, escalated for operator judgment, or written to the correct durable artifact
- [ ] Methodology loaded: five verification types (validation, testing, reviewing, auditing, evaluating) across verdict mode (deterministic/agentic) and purpose (conformance/correctness); three back the assertion tags (`[test]`, `[eval]`, `[audit]`)
- [ ] `spx/CLAUDE.md` drift check run once per session; `<SPX_CLAUDE_STALE>` marker emitted when the product guide is absent (`status="absent"`), exists but carries no `template_version` key (`status="stale"`), its `template_version` is numerically below the installed template (`status="stale"`), or its recorded `languages` differ from the project's languages in use (`status="stale"`)

</success_criteria>
