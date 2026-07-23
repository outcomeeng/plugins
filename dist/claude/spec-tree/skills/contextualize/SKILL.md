---
name: contextualize
description: ALWAYS invoke this skill when asking about status, progress, or what exists in the spec tree. NEVER work on any part of the spec tree without loading context through this skill first.
argument-hint: "<spx-root-or-full-node-path>"
arguments: target
allowed-tools: Read, Glob, Grep, Skill
---

<objective>

A `<SPEC_TREE_CONTEXT target="...">` marker carrying a structured context manifest for a product-root or node target — every applicable ancestor spec, lower-index sibling spec, ADR, PDR, cited methodology-governance decision, guide file, and the local lifecycle overlay read into the conversation, with no heuristic selection.

</objective>

<essential_principles>

**COMPLETE CONTEXT OR ABORT. NO EXCEPTIONS.**

- Every node along the path must have its spec file (`{slug}.md`)
- Missing spec file = ABORT with remediation guidance
- Read order: product root → ancestors → target (top-down)
- All ADRs and PDRs at all levels must be read — no skipping based on title relevance
- Lower-index siblings' specs must be read at each directory level — they constrain the target
- Explicit full-path ADR/PDR citations in loaded specs and decision records must be read before the context marker is emitted; coordination notes never add cited decisions.
- A context-grounded answer requires the matching `<SPEC_TREE_CONTEXT target="...">` marker. Loading this skill and completing `/sync-base` are prerequisites, not context.
- Test files are not read by `/contextualize`. The node target spec or product-root product spec already exposes inline `[test](tests/...)` links; list those links and the applicable `tests/` directory state, then leave test-body inspection to `/test`, `/audit-tests`, or `/apply`.
- **Always use canonical full paths** from `spx/` for targets and references. The product-root target is exactly `spx/`; a node target begins with `spx/` and contains only node-directory segments. Never refer to nodes, ADRs, or PDRs by bare name or numeric prefix; sibling numbers repeat under different parents and decision files cannot be found without their parent path.
  - Wrong: `/contextualize 32-parser.outcome`
  - Right: `/contextualize spx/{path-to-node}`

**BOOTSTRAP MODE**: Bootstrap is derived from the documented target and tree state, never from an undeclared operation. When `$target` is exactly `spx/`, one product spec exists, and no node directories exist, emit the product-root manifest with `bootstrap=true`. A missing node target always aborts; authoring a new node contextualizes its existing parent (`spx/` for a top-level node or the canonical full parent node path for a nested node).

</essential_principles>

<workflow>

<step name="gate">

**Step GATE: Check foundation**

Check the live conversation for the `<SPEC_TREE_FOUNDATION>` marker.
A marker mentioned only in a compaction summary, session file, handoff note, prior run description, or statement that `/understand` ran does not count. Reading the `/understand` SKILL.md file alone does not count.
If absent → STOP. Invoke `/understand` first, then resume from Step 0. Do not inspect git, session state, product files, or spec-tree content before the live marker is present.

</step>

<step name="sync_base">

**Step SYNC: Bring the branch current with its base**

Before reading any product or spec content, invoke `/sync-base` so the loaded context reflects current product truth rather than a stale checkout — a branch or detached worktree behind its base reads superseded specs and decisions. `/sync-base` fetches the base and brings the checkout current automatically from observable git state — rebasing a branch, or advancing a clean detached worktree to the base tip; never ask the operator whether to rebase. Act on its result:

- `already_current` or `rebased` → record the status for the eventual context marker, then immediately proceed to Step 0 for the same target on the now-current checkout. This also covers a detached worktree `/sync-base` advanced to the base tip — the loaded context reads the current base, not the stale parked commit. Do not answer the context-grounded question, inspect pull-request state, push, or manage branch ahead/behind status between the clean sync result and Step 0; lifecycle work resumes after context loading completes.
- `conflict` → STOP and surface the `/sync-base` `conflict` details. The branch cannot be brought current autonomously, and reading stale-or-conflicted context is the failure this gate prevents; leave the rebase active and resume once the operator resolves, continues, or aborts it.
- `dirty_tree` → treat the result as an unresolved ownership boundary returned by `/sync-base`, which already owns session-authorized checkpointing and retry. ABORT before reading product truth, preserve the exact reported paths, and resume this target only after `/sync-base` reaches a clean result. Never duplicate its branch, commit, or retry protocol here.
- `git_failure` → ABORT with the reported `detail`. A failed fetch, unresolved base, or non-advanceable detached checkout leaves currency unestablished, so no authoritative context can be loaded. Resolve the reported git condition, invoke `/sync-base` again, and then restart `/contextualize` for the same target.

</step>

<step name="locate">

**Step 0: Locate target**

If the invocation supplies no target path, ABORT: "A canonical target is required. Invoke `/contextualize spx/` for the product root or `/contextualize spx/{path-to-node}` for a node."

Before the first filesystem lookup, accept `$target` only when it is the exact product-root target `spx/` or a repository-relative node target beginning with `spx/` whose non-empty segments after `spx/` each match `{index}-{slug}.{enabler|outcome}`. Reject absolute paths, empty targets, repeated separators, `.` or `..` segments, trailing separators on node targets, and malformed node segments. Otherwise ABORT: "Invalid target path: $target. Supply `spx/` or one canonical full `spx/...` node path."

Set `product_root_target=true` only for the exact target `spx/`. Every other accepted target is a node target.

```bash
# Find the product file
Glob: "spx/*.product.md"

# Verify a node target exists; product-root mode already addresses spx/
Glob: "$target/*.md"  (node targets only)
```

If the product file is missing, ABORT: "No product file found in spx/. Create one with `/bootstrap` first."

If a node target path doesn't exist, ABORT: "Target path not found: $target. Check the path or contextualize its existing parent before creating it with `/author`."

For the exact product-root target `spx/`, list top-level node directories after locating the product spec. Set `bootstrap=true` when none exist and `bootstrap=false` otherwise. For every node target, set `bootstrap=false`.

For a node target, extract the path segments from product root to target. Each segment is a directory to walk. For the product-root target, the segment list is empty.

</step>

<step name="product">

**Step 1: Load product-level context**

```bash
# Read product spec
Read: spx/{product-name}.product.md

# Read runtime product guide if present
Read: CLAUDE.md  (if exists)

# Read ALL product-level ADRs and PDRs
Glob: "spx/*-*.adr.md"
Glob: "spx/*-*.pdr.md"

# Check for product-level coordination notes
Glob: "spx/PLAN.md"
Glob: "spx/ISSUES.md"

# Enumerate local overlays
Glob: "spx/local/*.md"

# Read local lifecycle overlay if present
Read: spx/local/merging.md  (if exists)
```

**Read EVERY file returned by the ADR/PDR globs.** Do not filter by title. Decision records contain cross-cutting constraints that may not be obvious from the title.

**Verification**: Count files returned by globs. Count files actually read. These must match.

**Guide files**: Read `CLAUDE.md` when present and record it in the manifest. A freshly bootstrapped tree may lack the guide; absence is normal.

**Coordination notes**: Read product-level `PLAN.md` and `ISSUES.md` when present. Reconcile them against product truth before use, and never scan their prose for cited governance decisions.

**Local overlays**: Record the list of files returned by `spx/local/*.md` for the manifest. Read `spx/local/merging.md` when present because default-branch lifecycle routing governs whether local implementation, validation, and commits are terminal. Do not read the other local overlays here — they are consumed by the relevant language skill, not by the context loader.

</step>

<step name="walk">

**Step 2: Walk the tree from root to target**

For each directory along the path from product root to a node target. In product-root mode the path contains zero node directories, so skip Step 2.

**2a. Read the directory's spec file**

```bash
# The spec file is {slug}.md (no type suffix, no numeric prefix)
Read: {path-to-dir}/{slug}.md

# Read harness guide in this directory if present
Read: {path-to-dir}/CLAUDE.md  (if exists)
```

ABORT if the spec file is missing.

A missing on-path guide is normal. Read a guide only when it exists, and record every guide read in the manifest.

**2b. Read all ADRs and PDRs in this directory**

```bash
Glob: "{path-to-dir}/*-*.adr.md"
Glob: "{path-to-dir}/*-*.pdr.md"
```

**Read EVERY file returned.** Verification: glob count must equal read count.

**2c. Check for coordination notes in this directory**

```bash
Glob: "{path-to-dir}/PLAN.md"
Glob: "{path-to-dir}/ISSUES.md"
```

**If PLAN.md or ISSUES.md exist, read them.** These are stale-prone coordination notes left by previous agents via `/handoff`. Deferred plans or known issues in an ancestor node may bear on the target, but they are fallible inputs, not authority — reconcile each against the specs, decisions, assertions, tests, implementation, and current user intent before letting it steer work.

**2d. Read all lower-index siblings' specs**

The target node has an index (e.g., `43` in `43-feature.outcome`). Existing lower-index sibling specs constrain the target's context and must be read.

```bash
# List all sibling directories (same parent, different from target)
Glob: "{parent-path}/*-*.{enabler,outcome}/"

# For each sibling with a lower index than the target:
Read: {parent-path}/{sibling-dir}/{sibling-slug}.md
```

Lower-index siblings' ADRs/PDRs are NOT read — only the sibling's spec itself. Existing numeric order makes the sibling's spec part of the target context, while the sibling's internal decisions are its own concern.

**2e. Note same-index siblings (independent)**

Siblings with the same index as the target are independent — they neither constrain nor are constrained by the target. List them but do not read.

</step>

<step name="target">

**Step 3: Load target context**

For a node target, load the target context below.

```bash
# Read target spec
Read: $target/{slug}.md

# Read target ADRs and PDRs
Glob: "$target/*-*.adr.md"
Glob: "$target/*-*.pdr.md"

# Enumerate children (if any)
Glob: "$target/*-*.{enabler,outcome}/"

# Check for tests directory
Glob: "$target/tests/*"

# Check for coordination notes
Glob: "$target/PLAN.md"
Glob: "$target/ISSUES.md"
```

**If PLAN.md or ISSUES.md exist, read them.** These are stale-prone coordination notes left by previous sessions via `/handoff`. They carry deferred plans or known issues that subsequent work may account for, but verify each before acting — reconcile it against the specs, decisions, assertions, tests, implementation, and current user intent rather than treating it as settled truth.

**Do not read test file bodies.** Record the test links visible in the target spec and whether co-located test files exist. Context loading does not infer implementation state from test imports. When the next workflow needs test details, route to `/test`, `/audit-tests`, or `/apply`.

For the product-root target, the product spec and product-level decisions and coordination notes were already read in Step 1. Enumerate top-level child nodes with `Glob: "spx/*-*.{enabler,outcome}/"`, list test links from the product spec, check `Glob: "spx/tests/*"` without reading test bodies, and skip node-spec and node-decision lookup. Report the target as `spx/ (product root)` and render the hierarchy as `{product-name} ← TARGET`.

</step>

<step name="cited_governance">

**Step 4: Read cited methodology-governance decisions**

Scan only the spec files and ADR/PDR files read by context loading for full-path decision citations:

```bash
Grep: "spx/[^[:space:])]+\\.(adr|pdr)\\.md" in the loaded spec and decision files
```

Read each cited `spx/.../*.adr.md` or `spx/.../*.pdr.md` file exactly once when it exists and has not already been read. Then scan each newly read cited decision for further full-path ADR/PDR citations, repeating until no unread cited decision remains. Preserve the citing file path for the manifest. Do not scan or trust citations in `PLAN.md`, `ISSUES.md`, or any coordination note; those notes are stale-prone workflow inputs, not context-loading authority.

If a loaded spec or decision cites a missing ADR/PDR path, ABORT with the missing citation path, the citing file, and remediation guidance to fix the stale citation or restore the decision file. A context marker that omits a cited governing decision is partial context.

</step>

<step name="summary">

**Step 5: Emit context marker and summary**

Emit the `<SPEC_TREE_CONTEXT>` marker with all collected information:

```text
<SPEC_TREE_CONTEXT target="{full-target-path}">

Product: {product-name}
Target: $target ({enabler|outcome|product root})
Bootstrap: {true|false}

Documents loaded:
  Product spec: {product-file}
  Ancestor specs: {count} read
  Lower-index sibling specs: {count} read
  ADRs: {count} found, {count} read
  PDRs: {count} found, {count} read
  Cited governance decisions: {list of path cited by path} | none
  Guide files: {list} | none
Sync-base status: {already_current|rebased}

Hierarchy (node target):
  {product-name}
  └── {ancestor-1} ({enabler|outcome})
      └── {ancestor-2} ({enabler|outcome})
          └── {target} ({enabler|outcome}) ← TARGET

Hierarchy (product-root target):
  {product-name} ← TARGET

Children: {count} ({list if any})
Test links: {list from target spec, full paths resolved from target} | none
Co-located tests: {count} listed | none
Implementation: unknown unless already established by a prior workflow
Coordination notes: {list of {path}/PLAN.md and {path}/ISSUES.md found at any level} | none
Local skill overlays: {comma-separated list from spx/local/} | none
Lifecycle overlays read: spx/local/merging.md | none
Default-branch completion boundary: delivered value is value merged to the default branch on origin through /merge; local verification, review, audit, and commits are progress, not completion, while the branch carries changes ahead of its resolved base
Governed next workflow: /merge after local verification when the work changes files and is destined for the default branch, unless explicitly scoped to proposal, analysis, review, or local-only work, or stopped at an explicit lifecycle gate with no independent local action remaining
Progress verdict rule: status and progress answers must classify the lifecycle as complete, continuing, or blocked; a clean worktree, committed branch, or passing local gate cannot classify default-branch work as complete while changes remain ahead of the resolved base
Continuation action: if the lifecycle is continuing, proceed to the governed next workflow instead of ending the turn; if blocked, report the exact gate, evidence, and operator decision required
Lower-index siblings read: {list}
Same-index siblings (independent): {list}
Higher-index siblings listed: {list}

</SPEC_TREE_CONTEXT>
```

</step>

</workflow>

<abort_protocol>

When a required document is missing, ABORT immediately with:

1. **What's missing** — exact file path expected
2. **Why it's needed** — what context it provides
3. **How to fix** — specific remediation action

| Missing       | Remediation                                                                           |
| ------------- | ------------------------------------------------------------------------------------- |
| Product file  | "Create with `/bootstrap` — every tree needs a product spec"                          |
| Ancestor spec | "Node directory exists but spec file is missing. Create `{slug}.md`"                  |
| Target spec   | "Target directory exists but spec file is missing. Create `{slug}.md` with `/author`" |

Do NOT proceed with partial context. The whole point of deterministic context is completeness.

</abort_protocol>

<failure_modes>

**Failure 1: Skipped ADRs/PDRs based on title relevance**

Claude globbed 12 decision records but only read 3 whose titles seemed relevant. The answer to the user's question was in one of the 9 skipped documents. The verification gate ("glob count must equal read count") prevents this.

**Failure 2: Missed lower-index siblings**

Claude walked the ancestor chain but didn't read lower-index siblings' specs. A lower-index enabler contained infrastructure the target depended on. Existing numeric order means lower-index sibling specs are constraining context, so they must be read.

**Failure 3: Read higher-index siblings**

Claude read ALL siblings including higher-index ones. Higher-index siblings may depend on the target but don't constrain it. Reading them wastes context window and may introduce irrelevant information.

**Failure 4: Inferred implementation state from tests during context loading**

Claude read test file imports during `/contextualize` and reported implementation state from those imports. That made context loading expensive and mixed it with testing work. Context loading lists test links and co-located test files only; `/test`, `/audit-tests`, and `/apply` inspect test bodies.

**Failure 5: Reported a bare node or decision name**

Claude wrote "see 15-build.adr.md" or "continue in 32-parser.enabler" without the full path. Those references are ambiguous because numeric prefixes are sibling-local. Always report the complete path from `spx/`, using the shape `spx/{parent-node}/{target-node}/{decision-file}` or `spx/{parent-node}/{target-node}`, so the file can be found.

**Failure 6: Omitted lifecycle continuation from the context marker**

Claude loaded `/understand`, completed edits, passed deterministic verification, committed the branch, then stopped because the context packet carried document context but no branch-lifecycle state. Context loading now reads `spx/local/merging.md` when present and records the default-branch completion boundary plus `/merge` continuation in `<SPEC_TREE_CONTEXT>`, so local readiness is not mistaken for delivered value.

**Failure 7: Treated status reporting as permission to stop**

Claude answered a progress question by reporting the clean worktree and local verification, then ended the turn while the branch still carried changes destined for the default branch. Context loading now requires a progress verdict and continuation action: complete only after the change reaches the default branch on origin, continuing when `/merge` remains available, or blocked when an explicit lifecycle gate leaves no independent local action.

**Failure 8: Let sync-base become the task**

Claude invoked `/sync-base`, received `already_current` or completed a clean rebase, then drifted into branch or pull-request lifecycle work before emitting `<SPEC_TREE_CONTEXT>`. The context-grounded question stayed unanswered because the prerequisite displaced the workflow. Clean sync results are recorded only as context-load state; the next action is Step 0 for the same target, and lifecycle work waits until context loading completes.

**Failure 9: Missed cited methodology governance**

Claude loaded the structural ancestor context for a plugin-shipping node and saw full-path citations to methodology-governance decisions under an independent sibling subtree, but did not read the cited PDRs because they were outside the structural ancestor path. The answer used an incomplete methodology model. Scan loaded specs and decision records for full-path ADR/PDR citations, including citations from newly read cited decisions, before emitting `<SPEC_TREE_CONTEXT>`.

**Failure 10: Omitted product-level coordination notes**

Claude checked `PLAN.md` and `ISSUES.md` only inside node directories, so product-level coordination disappeared from every target context even though it applied tree-wide. Check and read product-level coordination notes before walking the node path, then list them with the ancestor and target notes in the context manifest.

**Failure 11: Rejected the canonical product-root target**

Claude required at least one node-directory segment after `spx/`, so `/author` could not contextualize the parent of a top-level node even though `spx/` is the canonical product-root address. Treat exact `spx/` as product-root mode, walk zero node segments, and emit product-level context without attempting node-spec lookup.

</failure_modes>

<success_criteria>

Context loading is complete when:

- [ ] `<SPEC_TREE_FOUNDATION>` marker present (loaded via `/understand`)
- [ ] Product spec located and read
- [ ] Target accepted before filesystem lookup only when it is exact `spx/` or a canonical full `spx/...` node path
- [ ] All product-level ADRs/PDRs read (glob count = read count)
- [ ] Every ancestor along the path: spec read, ADRs/PDRs read
- [ ] Runtime guide files checked at product root and on each directory along the target path; present guides read and listed
- [ ] Lower-index siblings' specs read at each directory level
- [ ] Node target spec and ADRs/PDRs read, or product-root mode recorded with top-level children enumerated
- [ ] Full-path ADR/PDR citations in loaded specs and decisions read transitively, with citing files recorded
- [ ] Children enumerated
- [ ] Test links listed from the node target spec or product-root product spec, with co-located test files listed without reading test bodies
- [ ] Implementation state reported as unknown unless a prior workflow already established it
- [ ] Coordination notes (PLAN.md, ISSUES.md) checked and read if present at product root, each ancestor, and target
- [ ] Coordination-note citations excluded from cited-governance loading
- [ ] Local skill overlays enumerated from `spx/local/` and listed in manifest
- [ ] `spx/local/merging.md` read when present and lifecycle continuation state emitted in the manifest
- [ ] A clean `/sync-base` result is recorded as context-load state and followed immediately by Step 0 for the same target before any answer or branch lifecycle work
- [ ] Status and progress contexts include a lifecycle verdict and continuation action rather than treating local verification, commits, or worktree cleanliness as completion
- [ ] All node, ADR, PDR, test, and coordination-note references in the manifest use full paths from `spx/`
- [ ] Bootstrap state derives only from `$target` and the observed tree: exact `spx/` with a product spec and no nodes is `true`; every node target is `false`, and a missing node target aborts
- [ ] `<SPEC_TREE_CONTEXT target="...">` marker emitted with full manifest
- [ ] No ABORT conditions triggered (or appropriate error shown with remediation)

</success_criteria>
