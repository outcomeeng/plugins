---
name: understand
description: ALWAYS invoke this skill at the beginning of each session and after compaction. NEVER read, create, or modify any file in this repository other than the root agent guide without loading this skill and all its references first.
allowed-tools: Read, Glob, Grep, Bash(python3:*)
---

<objective>

The `<SPEC_TREE_FOUNDATION>` marker present in the conversation, carrying the loaded truth hierarchy, node types, assertion types, ordering rules, imperfection protocol, and verification kinds.

</objective>

<principles>

1. **TRUTH FLOWS DOWN** — Decisions (ADR: `{slug}.adr.md`/PDR: `{slug}.pdr.md`) decide. Specs (`{slug}.md`) declare in alignment with decisions. Tests derive from specs. Code derives from tests. When layers disagree, the lower layer is in violation. Never change a decision to match a spec. Never change a spec to match tests. Never change tests to match code. Read `references/durable-map.md`.
2. **SPEC TREE IS DECLARATIVE** — The Spec Tree is a durable, declarative map. Nothing moves, nothing closes. Specs declare product truth. Any change to what the operator demands is reflected in the Spec Tree first and naturally induces temporary inconsistency while dependent siblings and lower levels and consumers of decisions are brought up to date.
3. **DETERMINISTIC CONTEXT** — The Spec Tree structure defines what context Claude receives. No keyword search, no heuristics. This is handled by `/contextualize`, whose context marker carries both document context and lifecycle continuation state.
4. **ATEMPORAL VOICE** — The Spec Tree states product truth. Never narrate history. Immediately flag temporal language and make a proposal how to address it.
5. **FULL PATHS ONLY** — In every conversation with the operator and in every markdown link, every Spec Tree decision (ADR and PDR) and Spec Tree node reference uses the full path from `spx/`. Bare names and bare decision filenames are ambiguous because numeric prefixes repeat under different parents.
6. **TWO NODE TYPES** — Enablers (infrastructure) and outcomes (hypothesis + assertions). No other node types exist. Read `references/node-types.md`.
7. **ASSERTIONS SPECIFY OUTPUT** — Assertions specify what the software does, locally verifiable by automated tests or agent review. Assertion types derive from PDRs/ADRs and are materialized in specs. Assertions never derive from code or tests.
8. **VERIFICATION TYPES** — Five verification types establish a node's standing: validate, test, review, audit, evaluate. Two orthogonal axes describe each — verdict mode (deterministic or agentic) and purpose (conformance or correctness). Three of these verification types back the tag an assertion carries: `[test]` indicates the evidence is established via deterministic tests, `[eval]` indicates the evidence is established by a deterministic eval runner scoring the producing skill's structured verdict, `[audit]` indicates the evidence is established by a dedicated audit sub-agent. In contrast, the verification types *validate* and *review* are never used in spec assertions. Instead, validation is based on the product- and language-specific deterministic quality gates like linting and static analysis; review is based on the skill-driven standards executed by a dedicated sub-agent. Read `references/verification-kinds.md`.
9. **IMPERFECTIONS ARE ADDRESSED** — Claude notices every imperfection and addresses it. Claude researches on its own to find the right fix — never guessing, never assuming a fix is unsafe to make alone when available context could settle it. Only when an imperfection survives that validation does Claude take it to the operator — as options with a clear recommendation that improves the product, naming the skills and instructions behind the recommendation. Read `references/imperfection-protocol.md`.
10. **COORDINATION NOTES AND SESSION FILES INFORM WHAT TO WORK ON** — Coordination notes are Spec Tree node-aligned PLAN.md and ISSUES.md node-local coordination notes inside the tree. They are committed to git for one reason: future sessions read them on context load through `/contextualize`. They go stale quickly unless acted upon, so verify a coordination note before it steers work — reconcile it against the decisions (ADR/PDR), specs and verify any referenced downstream files (i.e., tests and implementation), and the current user intent, then act only where it still holds and suggest to update or remove any notes that are out of date. A coordination note never declares product truth, product decisions, architecture decisions, assertions, or evidence. `/contextualize` reads them automatically; conformance checks ignore them. Session files are invisible to Claude and only accessible via the `spx` CLI. Session files are the only Spec Tree-governed files that are *not committed to git* — `spx session` shares them across worktrees.
11. **LOCAL OVERLAYS** — `spx/local/` holds product-specific overlays for coding, architecting, testing, merge lifecycle and other skills. They supplement marketplace skill defaults without modifying the shared plugin. Enumerated by `/contextualize`; consumed by the relevant skill.
12. **NO VALUE IS DELIVERED WITHOUT MERGE** — ALL work only delivers value when merged to the default branch on origin through `/merge`. Local implementation and verification are progress, not completion; a branch with commits ahead of its resolved base is unfinished even when the working tree is clean. A created branch, a local commit, a pushed branch, an opened PR, or a clean worktree is a transport checkpoint, never a completion boundary. After targeted verification (validation, tests / evals, audit, review) pass according to the guidance in the root agent guide, continue into `/merge` and follow the selected transport until the change reaches the default branch on origin, or until an explicit lifecycle gate stops with no independent local action remaining without operator input or an external-state change. After committing or pushing a default-branch-destined changeset, invoke `/merge` in the same turn unless the user explicitly limited the task to proposal, analysis, review, branch-only, or local-only work. Do not stop after "implemented", "validated", "tests passed", "committed", or "pushed" when the user asked to make the change. Repository-specific merge behavior belongs in `spx/local/merging.md`, never in a generated guide; never reconstruct the transport from incidental docs when the overlay is absent — invoke `/merge`, the transport dispatcher: it classifies the changeset, selects the merge transport, and delegates to the selected transport's skills. `spx/local/merging.md` is an optional repo-local overlay that may refine the selection and configure transport behavior — a conditional read, read only when present. Its absence is normal and not of interest to the operator; the default lifecycle applies.

</principles>

<workflow>

1. Check the conversation for the `<SPEC_TREE_FOUNDATION>` marker. If present, the foundation is already loaded — skip ahead and read directly whichever `references/` or `templates/` file this invocation needs.
2. Read the following references in full and point out any contradictions to the operator immediately:
   - `references/durable-map.md`
   - `references/node-types.md`
   - `references/assertion-types.md`
   - `references/ordering-rules.md`
   - `references/verification-kinds.md`
   - `references/imperfection-protocol.md`
3. List each operational reference and `spx/local/` overlay with its path, last-modified time, and line count — evidence each was located this session, not assumed. These load on demand in other skills:
   - `references/what-goes-where.md` — ADR/PDR/spec/test content taxonomy and test-infrastructure governance and placement rules (used by `/align`, `/decompose`)
   - `references/excluded-nodes.md` — `spx/EXCLUDE` convention, quality gate integration (used by `/author`, `/test`)
   - PLAN.md / ISSUES.md inside node directories — node-local coordination notes for pending plans and known issues, git-tracked to carry coordination across sessions, verified and reconciled against the durable layers before use, never spec truth (used by `/contextualize`, `/handoff`)
   - `spx/local/*.md` — product-specific overlays for `/code-*`, `/architect-*`, `/test-*`, and lifecycle skills (enumerated by `/contextualize`)

   Produce the listing with the `Bash(python3:*)` grant:

   ```bash
   python3 -c 'import sys, datetime
   from pathlib import Path
   for a in sys.argv[1:]:
       items = sorted(Path(a).glob("*.md")) if Path(a).is_dir() else [Path(a)]
       for p in items:
           if not p.exists():
               continue
           n = sum(1 for _ in open(p))
           print(n, "lines", datetime.datetime.fromtimestamp(p.stat().st_mtime).isoformat(), p)' \
     "${CLAUDE_SKILL_DIR}/references/what-goes-where.md" \
     "${CLAUDE_SKILL_DIR}/references/excluded-nodes.md" \
     spx/local
   ```
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
6. List each template and example with its path, last-modified time, and line count — evidence each was located, not assumed — then read in full immediately when authoring:
   - `templates/product/product-name.product.md`
   - `templates/decisions/decision-name.adr.md`
   - `templates/decisions/decision-name.pdr.md`
   - `templates/nodes/enabler-name.md`
   - `templates/nodes/outcome-name.md`
   - `examples/` — concrete filled specs (read to see what a completed spec looks like)

   Produce the listing with the same `Bash(python3:*)` pass:

   ```bash
   python3 -c 'import sys, datetime
   from pathlib import Path
   for a in sys.argv[1:]:
       items = sorted(Path(a).glob("*.md")) if Path(a).is_dir() else [Path(a)]
       for p in items:
           if not p.exists():
               continue
           n = sum(1 for _ in open(p))
           print(n, "lines", datetime.datetime.fromtimestamp(p.stat().st_mtime).isoformat(), p)' \
     "${CLAUDE_SKILL_DIR}/templates/product/product-name.product.md" \
     "${CLAUDE_SKILL_DIR}/templates/decisions/decision-name.adr.md" \
     "${CLAUDE_SKILL_DIR}/templates/decisions/decision-name.pdr.md" \
     "${CLAUDE_SKILL_DIR}/templates/nodes/enabler-name.md" \
     "${CLAUDE_SKILL_DIR}/templates/nodes/outcome-name.md" \
     "${CLAUDE_SKILL_DIR}/examples"
   ```
7. Read the product's spx-level routing guide once, if present — `Read: spx/CLAUDE.md`. This is the WHEN-to-invoke-which-skill router for this runtime; the build renders the runtime's own filename. It is routing, not node/spec context, so it loads here once per session (and again after every compaction), not on every `/contextualize`. A freshly bootstrapped tree has no guide yet — skip silently when it does not exist.
8. Emit the `<SPEC_TREE_FOUNDATION>` marker:

```text
<SPEC_TREE_FOUNDATION>
Loaded: durable-map, node-types, assertion-types, ordering-rules, imperfection-protocol, verification-kinds
Operational references available: what-goes-where, excluded-nodes
Local lifecycle route: changes route through /merge (classifies the changeset, selects the merge transport, delegates to the selected transport; reads spx/local/merging.md as an optional overlay only when present, and its absence applies the default lifecycle)
Default-branch completion boundary: delivered value is value merged to the default branch on origin through /merge; verified local changes and clean branches with commits ahead of base remain unfinished until they reach the default branch on origin, unless the user explicitly limited the task to proposal, analysis, review, branch-only, or local-only work or stopped at an explicit lifecycle gate with no independent local action remaining
Routing guide: loaded from spx/CLAUDE.md | absent
Templates available: product, adr, pdr, enabler, outcome
Examples available in: examples/
</SPEC_TREE_FOUNDATION>
```

</workflow>

<failure_modes>

**Failure: Claude reported completion at a pushed branch.**

What happened: Claude created a branch, validated the change, committed, and pushed it, then reported the task complete without invoking `/merge`.

Why it failed: Claude treated the pushed branch as delivered value. In the Spec Tree lifecycle a pushed branch is review-ready state, not delivered value — delivered value is the change merged to the default branch on origin through `/merge`.

How to avoid: After a commit or push succeeds, check whether the user explicitly scoped the task to branch-only, local-only, proposal, or review. If not, invoke `/merge` immediately and let it select the transport.

</failure_modes>

<success_criteria>

- [ ] The six references in step 2 are read in full, with any contradictions among them surfaced to the operator
- [ ] Every operational reference, template, example, and `spx/local/` overlay is listed with its path, last-modified time, and line count — evidence each was located this session, not assumed
- [ ] `<SPEC_TREE_FOUNDATION>` marker emitted

</success_criteria>
