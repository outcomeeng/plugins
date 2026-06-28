---
name: contextualize
description: ALWAYS invoke this skill when asking about status, progress, or what exists in the spec tree. NEVER work on any part of the spec tree without loading context through this skill first.
allowed-tools: Read, Glob, Grep, Skill
---

<objective>

A `<SPEC_TREE_CONTEXT target="...">` marker carrying a structured context manifest for a target node — every ancestor spec, lower-index sibling spec, ADR, PDR, guide file, and the local lifecycle overlay read into the conversation, with no heuristic selection.

</objective>

<essential_principles>

**COMPLETE CONTEXT OR ABORT. NO EXCEPTIONS.**

- Every node along the path must have its spec file (`{slug}.md`)
- Missing spec file = ABORT with remediation guidance
- Read order: product root → ancestors → target (top-down)
- All ADRs and PDRs at all levels must be read — no skipping based on title relevance
- Lower-index siblings' specs must be read at each directory level — they constrain the target
- A context-grounded answer requires the matching `<SPEC_TREE_CONTEXT target="...">` marker. Loading this skill and completing `/sync-base` are prerequisites, not context.
- Test files are not read by `/contextualize`. The target spec already exposes inline `[test](tests/...)` links; list those links and the `tests/` directory state, then leave test-body inspection to `/test`, `/audit-tests`, or `/apply`.
- **Always use full paths** from `spx/` for targets and references. Never refer to nodes, ADRs, or PDRs by bare name or numeric prefix; sibling numbers repeat under different parents and decision files cannot be found without their parent path.
  - Wrong: `/contextualize 32-parser.outcome`
  - Right: `/contextualize 21-infra.enabler/32-parser.outcome`

**BOOTSTRAP MODE**: When the target path doesn't exist yet and the operation is authoring, return an empty manifest with `bootstrap=true` instead of aborting. This allows creating the first node in an empty tree.

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

- `already_current` or `rebased` → record the status for the eventual context marker, then immediately proceed to Step 0 for the same target on the now-current checkout. This also covers a detached worktree `/sync-base` advanced to the base tip — the loaded context reads the current base, not the stale parked commit. Do not answer the context-grounded question, inspect pull-request state, push, or manage branch ahead/behind status between the clean sync result and Step 0; those are caller lifecycle concerns after context loading completes.
- `conflict` → STOP and surface the `/sync-base` `conflict` details. The branch cannot be brought current autonomously, and reading stale-or-conflicted context is the failure this gate prevents; leave the rebase active and resume once the operator resolves, continues, or aborts it.
- `dirty_tree` → proceed to Step 0, noting that loaded context may be stale. Uncommitted tracked changes block the rebase (or the detached advance), so the checkout may still be behind its base. Context loading is read-only: it never commits or stashes to clear the tree — whether the changes are the operator's work-in-progress or a file Claude created this session — surfacing the staleness rather than mutating the working tree. Committing those changes is the mutating caller's job: the merge lifecycle or `/pickup`, via `/sync-base`'s `<dirty_tree_resolution>`, commits then re-syncs. This is not a rebase conflict and is never a reason to ask the operator to resolve a merge conflict.
- `git_failure` → distinguish by the reported `detail`. A `git_failure` detached outcome is the genuinely non-advanceable case: a diverged detached HEAD carrying its own commits (no branch to rebase them onto), or one with no resolvable remote base; a clean behind-base detached HEAD is not a `git_failure` — `/sync-base` advances it and returns `rebased`/`already_current` above. The non-advanceable cases are not applicable — proceed to Step 0; this is not a merge gate, so do not block on a non-advanceable checkout. A failed fetch or an unresolved base on a configured remote leaves currency unestablished — the checkout may still be behind its base — so surface the `detail` and that the loaded context may be stale before proceeding; never silently treat unverified currency as current.

</step>

<step name="locate">

**Step 0: Locate target node**

```bash
# Find the product file
Glob: "spx/*.product.md"

# Verify target path exists
Glob: "spx/{target-path}/*.md"
```

If the product file is missing, ABORT: "No product file found in spx/. Create one with `/author` first."

If the target path doesn't exist:

- If operation is `author` → return empty manifest with `bootstrap=true`
- Otherwise → ABORT: "Target path not found: {path}. Check the path or create it with `/author`."

Extract the path segments from product root to target. Each segment is a directory to walk.

</step>

<step name="product">

**Step 1: Load product-level context**

```bash
# Read product spec
Read: spx/{product-name}.product.md

# Read runtime product guide if present
Read: spx/CLAUDE.md  (if exists)

# Read ALL product-level ADRs and PDRs
Glob: "spx/*-*.adr.md"
Glob: "spx/*-*.pdr.md"

# Enumerate local overlays
Glob: "spx/local/*.md"

# Read local lifecycle overlay if present
Read: spx/local/merging.md  (if exists)
```

**Read EVERY file returned by the ADR/PDR globs.** Do not filter by title. Decision records contain cross-cutting constraints that may not be obvious from the title.

**Verification**: Count files returned by globs. Count files actually read. These must match.

**Guide files**: Read `spx/CLAUDE.md` when present and record it in the manifest. A freshly bootstrapped tree may lack the guide; absence is normal.

**Local overlays**: Record the list of files returned by `spx/local/*.md` for the manifest. Read `spx/local/merging.md` when present because default-branch lifecycle routing governs whether local implementation, validation, and commits are terminal. Do not read the other local overlays here — they are consumed by the relevant language skill, not by the context loader.

</step>

<step name="walk">

**Step 2: Walk the tree from root to target**

For each directory along the path from product root to the target node:

**2a. Read the directory's spec file**

```bash
# The spec file is {slug}.md (no type suffix, no numeric prefix)
Read: spx/{path-to-dir}/{slug}.md

# Read runtime guide in this directory if present
Read: spx/{path-to-dir}/CLAUDE.md  (if exists)
```

ABORT if the spec file is missing.

A missing on-path guide is normal. Read a guide only when it exists, and record every guide read in the manifest.

**2b. Read all ADRs and PDRs in this directory**

```bash
Glob: "spx/{path-to-dir}/*-*.adr.md"
Glob: "spx/{path-to-dir}/*-*.pdr.md"
```

**Read EVERY file returned.** Verification: glob count must equal read count.

**2c. Check for coordination notes in this directory**

```bash
Glob: "spx/{path-to-dir}/PLAN.md"
Glob: "spx/{path-to-dir}/ISSUES.md"
```

**If PLAN.md or ISSUES.md exist, read them.** These are stale-prone coordination notes left by previous agents via `/handoff`. Deferred plans or known issues in an ancestor node may bear on the target, but they are fallible inputs, not authority — reconcile each against the specs, decisions, assertions, tests, implementation, and current user intent before letting it steer work.

**2d. Read all lower-index siblings' specs**

The target node has an index (e.g., `43` in `43-feature.outcome`). Existing lower-index sibling specs constrain the target's context and must be read.

```bash
# List all sibling directories (same parent, different from target)
Glob: "spx/{parent-path}/*-*.{enabler,outcome}/"

# For each sibling with a lower index than the target:
Read: spx/{parent-path}/{sibling-dir}/{sibling-slug}.md
```

Lower-index siblings' ADRs/PDRs are NOT read — only the sibling's spec itself. Existing numeric order makes the sibling's spec part of the target context, while the sibling's internal decisions are its own concern.

**2e. Note same-index siblings (independent)**

Siblings with the same index as the target are independent — they neither constrain nor are constrained by the target. List them but do not read.

</step>

<step name="target">

**Step 3: Load target node context**

```bash
# Read target spec
Read: spx/{target-path}/{slug}.md

# Read target ADRs and PDRs
Glob: "spx/{target-path}/*-*.adr.md"
Glob: "spx/{target-path}/*-*.pdr.md"

# Enumerate children (if any)
Glob: "spx/{target-path}/*-*.{enabler,outcome}/"

# Check for tests directory
Glob: "spx/{target-path}/tests/*"

# Check for coordination notes
Glob: "spx/{target-path}/PLAN.md"
Glob: "spx/{target-path}/ISSUES.md"
```

**If PLAN.md or ISSUES.md exist, read them.** These are stale-prone coordination notes left by previous sessions via `/handoff`. They carry deferred plans or known issues that subsequent work may account for, but verify each before acting — reconcile it against the specs, decisions, assertions, tests, implementation, and current user intent rather than treating it as settled truth.

**Do not read test file bodies.** Record the test links visible in the target spec and whether co-located test files exist. Context loading does not infer implementation state from test imports. When the next workflow needs test details, route to `/test`, `/audit-tests`, or `/apply`.

</step>

<step name="summary">

**Step 4: Emit context marker and summary**

Emit the `<SPEC_TREE_CONTEXT>` marker with all collected information:

```text
<SPEC_TREE_CONTEXT target="{full-target-path}">

Product: {product-name}
Target: {target-path} ({enabler|outcome})

Documents loaded:
  Product spec: {product-file}
  Ancestor specs: {count} read
  Lower-index sibling specs: {count} read
  ADRs: {count} found, {count} read
  PDRs: {count} found, {count} read
  Guide files: {list} | none
Sync-base status: {already_current|rebased|dirty_tree|git_failure plus detail}

Hierarchy:
  {product-name}
  └── {ancestor-1} ({enabler|outcome})
      └── {ancestor-2} ({enabler|outcome})
          └── {target} ({enabler|outcome}) ← TARGET

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
| Product file  | "Create with `/author` — every tree needs a product spec"                             |
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

Claude wrote "see 15-build.adr.md" or "continue in 32-parser.enabler" without the full path. Those references are ambiguous because numeric prefixes are sibling-local. Always report `spx/.../15-build.adr.md` or `spx/.../32-parser.enabler` so the file can be found.

**Failure 6: Omitted lifecycle continuation from the context marker**

Claude loaded `/understand`, completed edits, passed deterministic verification, committed the branch, then stopped because the context packet carried document context but no branch-lifecycle state. Context loading now reads `spx/local/merging.md` when present and records the default-branch completion boundary plus `/merge` continuation in `<SPEC_TREE_CONTEXT>`, so local readiness is not mistaken for delivered value.

**Failure 7: Treated status reporting as permission to stop**

Claude answered a progress question by reporting the clean worktree and local verification, then ended the turn while the branch still carried changes destined for the default branch. Context loading now requires a progress verdict and continuation action: complete only after the change reaches the default branch on origin, continuing when `/merge` remains available, or blocked when an explicit lifecycle gate leaves no independent local action.

**Failure 8: Let sync-base become the task**

Claude invoked `/sync-base`, received `already_current` or completed a clean rebase, then drifted into branch or pull-request lifecycle work before emitting `<SPEC_TREE_CONTEXT>`. The context-grounded question stayed unanswered because the prerequisite displaced the workflow. Clean sync results are recorded only as context-load state; the next action is Step 0 for the same target, and lifecycle work waits until context loading completes.

</failure_modes>

<success_criteria>

Context loading is complete when:

- [ ] `<SPEC_TREE_FOUNDATION>` marker present (loaded via `/understand`)
- [ ] Product spec located and read
- [ ] All product-level ADRs/PDRs read (glob count = read count)
- [ ] Every ancestor along the path: spec read, ADRs/PDRs read
- [ ] Runtime guide files checked at product root and on each directory along the target path; present guides read and listed
- [ ] Lower-index siblings' specs read at each directory level
- [ ] Target spec read
- [ ] Target ADRs/PDRs read
- [ ] Children enumerated
- [ ] Test links listed from the target spec and co-located test files listed without reading test bodies
- [ ] Implementation state reported as unknown unless a prior workflow already established it
- [ ] Coordination notes (PLAN.md, ISSUES.md) checked and read if present at each ancestor AND at target
- [ ] Local skill overlays enumerated from `spx/local/` and listed in manifest
- [ ] `spx/local/merging.md` read when present and lifecycle continuation state emitted in the manifest
- [ ] A clean `/sync-base` result is recorded as context-load state and followed immediately by Step 0 for the same target before any answer or branch lifecycle work
- [ ] Status and progress contexts include a lifecycle verdict and continuation action rather than treating local verification, commits, or worktree cleanliness as completion
- [ ] All node, ADR, PDR, test, and coordination-note references in the manifest use full paths from `spx/`
- [ ] `<SPEC_TREE_CONTEXT target="...">` marker emitted with full manifest
- [ ] No ABORT conditions triggered (or appropriate error shown with remediation)

</success_criteria>
