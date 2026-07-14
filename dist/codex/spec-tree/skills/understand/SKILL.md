---
name: understand
description: >-
  ALWAYS invoke this skill at the beginning of each session, after every
  compaction, and before answering spec-tree workflow or session-continuity
  questions when the live SPEC_TREE_FOUNDATION marker is absent. NEVER
  read, create, or modify any file in this repository other than
  AGENTS.md without loading this skill and all its references
  first.
argument-hint: "[profile]"
arguments: profile
allowed-tools: Read, Glob, Grep
---

<objective>

The `<SPEC_TREE_FOUNDATION>` marker present in the conversation, carrying the loaded truth hierarchy, node types, assertion types, ordering rules, imperfection protocol, and verification kinds, plus a complete materials receipt when a named composition profile is requested.

</objective>

<principles>

1. **TRUTH FLOWS DOWN** — Decisions (ADR: `{slug}.adr.md`/PDR: `{slug}.pdr.md`) decide. Specs (`{slug}.md`) declare in alignment with decisions. Tests derive from specs. Code derives from tests. When layers disagree, the lower layer is in violation. Never change a decision to match a spec. Never change a spec to match tests. Never change tests to match code. Read `${SKILL_DIR}/references/durable-map.md`.
2. **SPEC TREE IS DECLARATIVE** — The Spec Tree is a durable, declarative map. Nothing moves, nothing closes. Specs declare product truth. Any change to what the operator demands is reflected in the Spec Tree first and naturally induces temporary inconsistency while dependent siblings and lower levels and consumers of decisions are brought up to date.
3. **DETERMINISTIC CONTEXT** — The Spec Tree structure defines what context Claude receives. No keyword search, no heuristics. This is handled by `/contextualize`, whose context marker carries both document context and lifecycle continuation state.
4. **ATEMPORAL VOICE** — The Spec Tree states product truth. Never narrate history. Immediately flag temporal language. Authoring workflows propose a correction; read-only conformance workflows report the factual violation without remediation.
5. **FULL PATHS ONLY** — In every conversation with the operator and in every markdown link, every Spec Tree decision (ADR and PDR) and Spec Tree node reference uses the full path from `spx/`. Bare names and bare decision filenames are ambiguous because numeric prefixes repeat under different parents.
6. **TWO NODE TYPES** — Enablers (infrastructure) and outcomes (hypothesis + assertions). No other node types exist. Read `${SKILL_DIR}/references/node-types.md`.
7. **ASSERTIONS SPECIFY OUTPUT** — Assertions specify what the software does, locally verifiable through `[test]`, `[eval]`, or `[audit]` evidence. Assertion types derive from PDRs/ADRs and are materialized in specs. Assertions never derive from code or tests.
8. **VERIFICATION TYPES** — Five verification types establish a node's standing: validate, test, review, audit, evaluate. Two orthogonal axes describe each — verdict mode (deterministic or agentic) and purpose (conformance or correctness). Three of these verification types back the tag an assertion carries: `[test]` indicates the evidence is established via deterministic tests, `[eval]` indicates the evidence is established by a deterministic eval runner scoring the producing skill's structured verdict, `[audit]` indicates the evidence is established by a dedicated audit sub-agent. In contrast, the verification types *validate* and *review* are never used in spec assertions. Instead, validation is based on the product- and language-specific deterministic quality gates like linting and static analysis; review is based on the skill-driven standards executed by a dedicated sub-agent. Read `${SKILL_DIR}/references/verification-kinds.md`.
9. **IMPERFECTIONS ARE ADDRESSED** — Claude notices every imperfection and addresses it. Claude researches on its own to find the right fix — never guessing, never assuming a fix is unsafe to make alone when available context could settle it. Only when an imperfection survives that validation does Claude take it to the operator — as options with a clear recommendation that improves the product, naming the skills and instructions behind the recommendation. Read `${SKILL_DIR}/references/imperfection-protocol.md`.
10. **COORDINATION NOTES AND SESSION FILES INFORM WHAT TO WORK ON** — Coordination notes are Spec Tree node-aligned PLAN.md and ISSUES.md node-local coordination notes inside the tree. They are committed to git for one reason: future sessions read them on context load through `/contextualize`. They go stale quickly unless acted upon, so verify a coordination note before it steers work — reconcile it against the decisions (ADR/PDR), specs and verify any referenced downstream files (i.e., tests and implementation), and the current user intent, then act only where it still holds and suggest to update or remove any notes that are out of date. A coordination note never declares product truth, product decisions, architecture decisions, assertions, or evidence. `/contextualize` reads them automatically; conformance checks ignore them. Session files are invisible to Claude and only accessible via the `spx` CLI. Session files are the only Spec Tree-governed files that are *not committed to git* — `spx session` shares them across worktrees.
11. **LOCAL OVERLAYS** — `spx/local/` holds product-specific overlays for coding, architecting, testing, merge lifecycle and other skills. They supplement marketplace skill defaults without modifying the shared plugin. Enumerated by `/contextualize`; consumed by the relevant skill.
12. **NO VALUE IS DELIVERED WITHOUT MERGE** — ALL work only delivers value when merged to the default branch on origin through `/merge`. Local implementation and verification are progress, not completion; a branch with commits ahead of its resolved base is unfinished even when the working tree is clean. A created branch, a local commit, a pushed branch, an opened PR, or a clean worktree is a transport checkpoint, never a completion boundary. After targeted verification (validation, tests / evals, audit, review) pass according to the guidance in AGENTS.md, continue into `/merge` and follow the selected transport until the change reaches the default branch on origin, or until an explicit lifecycle gate stops with no independent local action remaining without operator input or an external-state change. After committing or pushing a default-branch-destined changeset, invoke `/merge` in the same turn unless the user explicitly limited the task to proposal, analysis, review, branch-only, or local-only work. Do not stop after "implemented", "validated", "tests passed", "committed", or "pushed" when the user asked to make the change. Repository-specific merge behavior belongs in `spx/local/merging.md`, never in a generated guide; never reconstruct the transport from incidental docs when the overlay is absent — invoke `/merge`, the transport dispatcher: it classifies the changeset, selects the merge transport, and delegates to the selected transport's skills. `spx/local/merging.md` is an optional repo-local overlay that may refine the selection and configure transport behavior — a conditional read, read only when present. Its absence is normal and not of interest to the operator; the default lifecycle applies.

</principles>

<composition_profiles>

Resolve `$profile` before entering the workflow:

- Empty: load the standard foundation.
- `align`: load the standard foundation plus the conformance references and structural templates owned by this skill, then emit the `<SPEC_TREE_FOUNDATION_MATERIALS profile="align">` receipt below.
- `author`: load the standard foundation plus the content taxonomy, exclusion rules, structural templates, and filled examples needed to author a Spec Tree artifact.
- `bootstrap`: load the standard foundation plus the product-domain classifier and product template needed to scaffold a tree.
- `decompose`: load the standard foundation plus the content taxonomy, product-domain classifier, and node templates needed to compose children and assign indices.
- `refactor`: load the standard foundation plus the content taxonomy needed to move or re-scope nodes.
- `instruction-block`: load the standard foundation, locate and read the canonical instruction-block template, and return its resolved path for the consuming workflow.
- Any other value: STOP and report the unsupported profile.

Each non-empty profile is the deterministic cross-skill lookup mechanism for its consuming workflow. The caller invokes `/understand <profile>` as a composed skill capability and consumes the loaded content and receipt; it never manufactures a filesystem path into this skill's bundle.

</composition_profiles>

<workflow>

1. Resolve `$profile` through `<composition_profiles>`, then check the live conversation for the `<SPEC_TREE_FOUNDATION>` marker. If present and `$profile` is empty, the foundation is already loaded — skip ahead and read directly whichever `${SKILL_DIR}/references/` or `${SKILL_DIR}/templates/` file this invocation needs. A non-empty profile never takes this fast path because it must return a fresh materials receipt to its caller.
   A marker mentioned only in a compaction summary, session file, handoff note, prior run description, or statement that `/understand` ran does not count. Reading this SKILL.md alone does not count.
   After every compaction, treat the marker as absent until this workflow emits it again.
   Questions about `/understand`, `/contextualize`, `/apply`, `/handoff`, `/merge`, `/pickup`, session continuity, or whether a skill was invoked are spec-tree work and require this workflow before answering when the live marker is absent.
2. Read the following references in full and point out any contradictions to the operator immediately:
   - `${SKILL_DIR}/references/durable-map.md`
   - `${SKILL_DIR}/references/node-types.md`
   - `${SKILL_DIR}/references/assertion-types.md`
   - `${SKILL_DIR}/references/ordering-rules.md`
   - `${SKILL_DIR}/references/verification-kinds.md`
   - `${SKILL_DIR}/references/imperfection-protocol.md`
3. List each operational reference and `spx/local/` overlay by path — evidence each was located this session, not assumed. These load on demand in other skills:
   - `${SKILL_DIR}/references/what-goes-where.md` — ADR/PDR/spec/test content taxonomy and test-infrastructure governance and placement rules (used by `/align`, `/decompose`)
   - `${SKILL_DIR}/references/excluded-nodes.md` — `spx/EXCLUDE` convention, quality gate integration (used by `/author`, `/test`)
   - `${SKILL_DIR}/references/product-domain-shapes.md` — product-domain, first-concrete-behavior, actor, surface, and code-shaped-name classifier and examples (used by `/bootstrap`, `/decompose`)
   - `spx/local/*.md` — product-specific overlays for `/code-*`, `/architect-*`, `/test-*`, and lifecycle skills (enumerated by `/contextualize`)

   Locate the three exact reference paths with `Glob`, and enumerate product overlays with `Glob: "spx/local/*.md"`.
4. Check for local lifecycle routing:
   - Changes destined for the default branch route through `/merge`, the transport dispatcher. It classifies the changeset, selects the merge transport, and delegates to the selected transport's skills, reading `spx/local/merging.md` as an optional overlay when present.
   - If `spx/local/merging.md` exists at the repository root, read it. Its declarations refine transport selection and lifecycle configuration. Its absence is normal and not a blocker — the default lifecycle applies, and merge behavior is never reconstructed from other docs or changed by editing a generated guide.
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
6. List each template and example by path — evidence each was located, not assumed — then read in full immediately when authoring:
   - `${SKILL_DIR}/templates/product/product-name.product.md`
   - `${SKILL_DIR}/templates/decisions/decision-name.adr.md`
   - `${SKILL_DIR}/templates/decisions/decision-name.pdr.md`
   - `${SKILL_DIR}/templates/nodes/enabler-name.md`
   - `${SKILL_DIR}/templates/nodes/outcome-name.md`
   - `${SKILL_DIR}/examples/` — concrete filled specs (read to see what a completed spec looks like)

   Locate the five exact template paths with `Glob`, and enumerate examples with `Glob: "${SKILL_DIR}/examples/*.md"`.
   For a non-empty profile, read its additional materials in full:

   | Profile             | Additional materials                                                                                                                             |
   | ------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------ |
   | `align`             | `references/what-goes-where.md` and all five structural templates                                                                                |
   | `author`            | `references/what-goes-where.md`, `references/excluded-nodes.md`, all five structural templates, and every file under `examples/`                 |
   | `bootstrap`         | `references/product-domain-shapes.md` and `templates/product/product-name.product.md`                                                            |
   | `decompose`         | `references/what-goes-where.md`, `references/product-domain-shapes.md`, `templates/nodes/enabler-name.md`, and `templates/nodes/outcome-name.md` |
   | `refactor`          | `references/what-goes-where.md`                                                                                                                  |
   | `instruction-block` | `templates/instruction-block.md`; locate it with `Glob`, read it in full, and retain the resolved absolute path returned by the tool             |
7. Read the product's root routing guide once, if present — `Read: AGENTS.md`. This is the WHEN-to-invoke-which-skill router for this runtime; the build renders the runtime's own filename. It is routing, not node/spec context, so it loads here once per session (and again after every compaction), not on every `/contextualize`. A freshly bootstrapped tree has no guide yet — skip silently when it does not exist.
8. Emit the `<SPEC_TREE_FOUNDATION>` marker:

```text
<SPEC_TREE_FOUNDATION>
Loaded: durable-map, node-types, assertion-types, ordering-rules, imperfection-protocol, verification-kinds
Operational references available: what-goes-where, excluded-nodes, product-domain-shapes
Local lifecycle route: changes route through /merge (classifies the changeset, selects the merge transport, delegates to the selected transport; reads spx/local/merging.md as an optional overlay only when present, and its absence applies the default lifecycle)
Default-branch completion boundary: delivered value is value merged to the default branch on origin through /merge; verified local changes and clean branches with commits ahead of base remain unfinished until they reach the default branch on origin, unless the user explicitly limited the task to proposal, analysis, review, branch-only, or local-only work or stopped at an explicit lifecycle gate with no independent local action remaining
Routing guide: loaded from AGENTS.md | absent
Templates available: product, adr, pdr, enabler, outcome
Examples available in: ${SKILL_DIR}/examples/
</SPEC_TREE_FOUNDATION>
```

9. When `$profile` is non-empty, emit the matching receipt only after every named material has been read in full:

```text
<SPEC_TREE_FOUNDATION_MATERIALS profile="align">
Conformance references loaded by /understand: durable-map, what-goes-where, node-types
Structural templates loaded by /understand: adr, pdr, product, enabler, outcome
</SPEC_TREE_FOUNDATION_MATERIALS>
```

```text
<SPEC_TREE_FOUNDATION_MATERIALS profile="author">
Authoring references loaded by /understand: durable-map, node-types, assertion-types, what-goes-where, excluded-nodes
Structural templates loaded by /understand: adr, pdr, product, enabler, outcome
Filled examples loaded by /understand: every bundled example
</SPEC_TREE_FOUNDATION_MATERIALS>
```

```text
<SPEC_TREE_FOUNDATION_MATERIALS profile="bootstrap">
Bootstrap references loaded by /understand: product-domain-shapes
Structural templates loaded by /understand: product
</SPEC_TREE_FOUNDATION_MATERIALS>
```

```text
<SPEC_TREE_FOUNDATION_MATERIALS profile="decompose">
Decomposition references loaded by /understand: node-types, ordering-rules, what-goes-where, product-domain-shapes
Structural templates loaded by /understand: enabler, outcome
</SPEC_TREE_FOUNDATION_MATERIALS>
```

```text
<SPEC_TREE_FOUNDATION_MATERIALS profile="refactor">
Refactoring references loaded by /understand: node-types, what-goes-where
</SPEC_TREE_FOUNDATION_MATERIALS>
```

```text
<SPEC_TREE_FOUNDATION_MATERIALS profile="instruction-block">
Canonical template loaded by /understand: instruction-block
Template path: <resolved-absolute-template-path>
</SPEC_TREE_FOUNDATION_MATERIALS>
```

</workflow>

<failure_modes>

**Failure: Claude reported completion at a pushed branch.**

What happened: Claude created a branch, validated the change, committed, and pushed it, then reported the task complete without invoking `/merge`.

Why it failed: Claude treated the pushed branch as delivered value. In the Spec Tree lifecycle a pushed branch is review-ready state, not delivered value — delivered value is the change merged to the default branch on origin through `/merge`.

How to avoid: After a commit or push succeeds, check whether the user explicitly scoped the task to branch-only, local-only, proposal, or review. If not, invoke `/merge` immediately and let it select the transport.

</failure_modes>

<success_criteria>

- The conversation contains one live `<SPEC_TREE_FOUNDATION>` marker whose loaded set covers the six foundation references.
- Every bundled operational reference, template, and example resolves from `${SKILL_DIR}`; repo-local overlays are enumerated separately from `spx/local/`.
- Every non-empty profile reads its declared materials in full and emits only its matching `<SPEC_TREE_FOUNDATION_MATERIALS profile="...">` receipt after that complete read.
- The `instruction-block` receipt reports the resolved absolute path returned while locating the canonical template; consuming skills never derive that path from their own skill directory.
- The marker's local lifecycle route, default-branch completion boundary, and routing-guide state match the repository observed during this session.
- A marker retained by the Step 1 fast path satisfies the same invariants without a duplicate reload; a freshly emitted marker appears only after every declared resource was located.
- Any contradiction among the loaded foundation references is visible to the operator rather than hidden behind the marker.

</success_criteria>
