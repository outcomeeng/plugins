---
name: contextualizing
description: >-
  ALWAYS invoke this skill when asking about status, progress, or what exists in the spec tree.
  NEVER work on any part of the spec tree without loading context through this skill first.
allowed-tools: Read, Glob, Grep
---

<objective>

Walk the Spec Tree from product root to a target node, deterministically collecting and reading all context: ancestor specs along the path, lower-index siblings' specs at each directory level, and all ADRs/PDRs. Emit `<SPEC_TREE_CONTEXT target="...">` marker with a structured context manifest.

This is full injection — every collected document is read into the conversation. No heuristic selection.

</objective>

<essential_principles>

**COMPLETE CONTEXT OR ABORT. NO EXCEPTIONS.**

- Every node along the path must have its spec file (`{slug}.md`)
- Missing spec file = ABORT with remediation guidance
- Read order: product root → ancestors → target (top-down)
- All ADRs and PDRs at all levels must be read — no skipping based on title relevance
- Lower-index siblings' specs must be read at each directory level — they constrain the target
- Test files are excluded — context is about specs and decisions, not evidence
- **Always use full path** from `spx/` to target — indices are sibling-unique, not globally unique:
  - Wrong: `/contextualizing 32-parser.outcome`
  - Right: `/contextualizing 21-infra.enabler/32-parser.outcome`

**BOOTSTRAP MODE**: When the target path doesn't exist yet and the operation is authoring, return an empty manifest with `bootstrap=true` instead of aborting. This allows creating the first node in an empty tree.

</essential_principles>

<workflow>

<step name="gate">

**Step GATE: Check foundation**

Check conversation for `<SPEC_TREE_FOUNDATION>` marker.
If absent → STOP. Invoke `/understanding` first, then resume from Step 0.

</step>

<step name="locate">

**Step 0: Locate target node**

```bash
# Find the product file
Glob: "spx/*.product.md"

# Verify target path exists
Glob: "spx/{target-path}/*.md"
```

If the product file is missing, ABORT: "No product file found in spx/. Create one with `/authoring` first."

If the target path doesn't exist:

- If operation is `author` → return empty manifest with `bootstrap=true`
- Otherwise → ABORT: "Target path not found: {path}. Check the path or create it with `/authoring`."

Extract the path segments from product root to target. Each segment is a directory to walk.

</step>

<step name="product">

**Step 1: Load product-level context**

```bash
# Read product spec
Read: spx/{product-name}.product.md

# Read product guide if present
Read: spx/CLAUDE.md  (if exists)

# Read ALL product-level ADRs and PDRs
Glob: "spx/*-*.adr.md"
Glob: "spx/*-*.pdr.md"
```

**Read EVERY file returned by the globs.** Do not filter by title. Decision records contain cross-cutting constraints that may not be obvious from the title.

**Verification**: Count files returned by globs. Count files actually read. These must match.

</step>

<step name="walk">

**Step 2: Walk the tree from root to target**

For each directory along the path from product root to the target node:

**2a. Read the directory's spec file**

```bash
# The spec file is {slug}.md (no type suffix, no numeric prefix)
Read: spx/{path-to-dir}/{slug}.md
```

ABORT if the spec file is missing.

**2b. Read all ADRs and PDRs in this directory**

```bash
Glob: "spx/{path-to-dir}/*-*.adr.md"
Glob: "spx/{path-to-dir}/*-*.pdr.md"
```

**Read EVERY file returned.** Verification: glob count must equal read count.

**2c. Read all lower-index siblings' specs**

The target node has an index (e.g., `43` in `43-feature.outcome`). All sibling nodes with a lower index constrain the target and must be read.

```bash
# List all sibling directories (same parent, different from target)
Glob: "spx/{parent-path}/*-*.{enabler,outcome}/"

# For each sibling with a lower index than the target:
Read: spx/{parent-path}/{sibling-dir}/{sibling-slug}.md
```

Lower-index siblings' ADRs/PDRs are NOT read — only the sibling's spec itself. The dependency encoding means the sibling's existence constrains the target, but the sibling's internal decisions are its own concern.

**2d. Note same-index siblings (independent)**

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

# Check for escape hatches
Glob: "spx/{target-path}/PLAN.md"
Glob: "spx/{target-path}/ISSUES.md"
```

**If PLAN.md or ISSUES.md exist, read them.** These are non-durable escape hatches left by previous agents via `/handoff`. They contain deferred plans or known issues that the next agent must be aware of.

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

Hierarchy:
  {product-name}
  └── {ancestor-1} ({enabler|outcome})
      └── {ancestor-2} ({enabler|outcome})
          └── {target} ({enabler|outcome}) ← TARGET

Children: {count} ({list if any})
Tests: {exists|missing}
Escape hatches: {PLAN.md | ISSUES.md | none}
Lower-index siblings read: {list}
Same-index siblings (independent): {list}
Higher-index siblings (depend on target): {list}

</SPEC_TREE_CONTEXT>
```

</step>

</workflow>

<abort_protocol>

When a required document is missing, ABORT immediately with:

1. **What's missing** — exact file path expected
2. **Why it's needed** — what context it provides
3. **How to fix** — specific remediation action

| Missing       | Remediation                                                                              |
| ------------- | ---------------------------------------------------------------------------------------- |
| Product file  | "Create with `/authoring` — every tree needs a product spec"                             |
| Ancestor spec | "Node directory exists but spec file is missing. Create `{slug}.md`"                     |
| Target spec   | "Target directory exists but spec file is missing. Create `{slug}.md` with `/authoring`" |

Do NOT proceed with partial context. The whole point of deterministic context is completeness.

</abort_protocol>

<failure_modes>

**Failure 1: Skipped ADRs/PDRs based on title relevance**

Agent globbed 12 decision records but only read 3 whose titles seemed relevant. The answer to the user's question was in one of the 9 skipped documents. The verification gate ("glob count must equal read count") prevents this.

**Failure 2: Missed lower-index siblings**

Agent walked the ancestor chain but didn't read lower-index siblings' specs. A lower-index enabler contained infrastructure the target depended on. The dependency encoding means lower-index = constraining, so they must be read.

**Failure 3: Read higher-index siblings**

Agent read ALL siblings including higher-index ones. Higher-index siblings may depend on the target but don't constrain it. Reading them wastes context window and may introduce irrelevant information.

</failure_modes>

<success_criteria>

Context loading is complete when:

- [ ] `<SPEC_TREE_FOUNDATION>` marker present (loaded via `/understanding`)
- [ ] Product spec located and read
- [ ] All product-level ADRs/PDRs read (glob count = read count)
- [ ] Every ancestor along the path: spec read, ADRs/PDRs read
- [ ] Lower-index siblings' specs read at each directory level
- [ ] Target spec read
- [ ] Target ADRs/PDRs read
- [ ] Children enumerated
- [ ] Test directory status checked
- [ ] Escape hatches (PLAN.md, ISSUES.md) checked and read if present
- [ ] `<SPEC_TREE_CONTEXT target="...">` marker emitted with full manifest
- [ ] No ABORT conditions triggered (or appropriate error shown with remediation)

</success_criteria>
