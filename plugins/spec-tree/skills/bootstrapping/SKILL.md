---
name: bootstrapping
description: >-
  ALWAYS invoke this skill when setting up a new spec tree or when /authoring detects an empty spx/ directory.
  NEVER create a spec tree from scratch without this skill.
allowed-tools: Read, Glob, Grep, Write, Edit
---

<objective>

Interview the user to understand their product, then scaffold the initial `spx/` directory with a product spec, project guide, and top-level node stubs. This is the entry point for new spec-tree projects.

</objective>

<quick_start>

**PREREQUISITE**: Check for `<SPEC_TREE_FOUNDATION>` marker. If absent, invoke `/understanding` first.

This skill runs when:

- The user says "bootstrap", "set up spec tree", "start a new project"
- `/authoring` detects no `spx/` directory or an empty one
- The user invokes `/bootstrapping` directly

</quick_start>

<workflow>

<step name="detect">

**Step 1: Check current state**

```bash
Glob: "spx/*.product.md"
Glob: "spx/*-*.{enabler,outcome}/"
```

If a product spec already exists, this is not a bootstrap — redirect to `/authoring`.

If `spx/` doesn't exist or contains no product spec, proceed.

</step>

<step name="interview">

**Step 2: Interview the user**

Use `AskUserQuestion` to gather product understanding. Adapt based on what's already known from the conversation.

**Round 1 — Product identity:**

- "What does this product do?" (one sentence)
- "Who is it for?" (target user)

**Round 2 — Product hypothesis:**

- "What change in user behavior do you expect?" (outcome)
- "What business value does that produce?" (impact)

**Round 3 — Scope:**

- "What are the 3–7 major things this product does or provides?" (candidate top-level nodes)

For each candidate, ask whether it delivers user-facing value (outcome) or exists to serve other parts (enabler).

**Decision gate:** "Ready to scaffold, or want to refine?"

Skip questions where the conversation already provides the answer.

</step>

<step name="plan">

**Step 3: Present the scaffold plan**

Before creating anything, show the user what will be created:

```text
Proposed structure:

spx/
├── {product-name}.product.md
├── CLAUDE.md
├── {NN}-{slug}.enabler/
│   ├── {slug}.md
│   └── tests/
├── {NN}-{slug}.outcome/
│   ├── {slug}.md
│   └── tests/
└── ...
```

Include:

- Product name and hypothesis
- Each top-level node with type (enabler/outcome), index, and one-line description
- Index rationale (ordering formula applied)

Wait for user confirmation before creating files.

</step>

<step name="scaffold">

**Step 4: Create the scaffold**

1. Create `spx/` directory if it doesn't exist.

2. Write `spx/{product-name}.product.md` using the template from `${SKILL_DIR}/../understanding/templates/product/product-name.product.md`. Fill in:
   - Product name
   - Why this product exists
   - Three-part hypothesis (output → outcome → impact)
   - Scope (included items = the top-level nodes)
   - Product-level compliance rules (if any emerged from interview)

3. Write `spx/CLAUDE.md` from the template at `${SKILL_DIR}/templates/spx-claude.md`. Replace `{product-name}` with the actual product name.

4. For each top-level node:
   - Create directory: `spx/{NN}-{slug}.{enabler|outcome}/`
   - Write spec stub: `{slug}.md` with hypothesis or enables statement and a placeholder assertion
   - Create `tests/` directory

</step>

<step name="deliver">

**Step 5: Report and recommend**

Summarize what was created:

- Product spec path
- CLAUDE.md path
- Each node with type, index, and path

Recommend next steps:

- "Fill in assertions for each node with `/authoring`"
- "If any node has more than 7 concerns, decompose it with `/decomposing`"
- "When assertions are ready, write tests with `/testing`"

</step>

</workflow>

<failure_modes>

**Failure 1: Bootstrapped over an existing tree**

Agent ran bootstrapping in a project that already had `spx/` with specs. The product spec was overwritten.

How to avoid: Step 1 checks for an existing product spec. If one exists, redirect to `/authoring` — this is not a bootstrap.

**Failure 2: Too many top-level nodes**

Agent accepted the user's list of 12 candidate nodes without pushing back. The tree started with too many siblings, making context loading expensive and structure unclear.

How to avoid: During the interview, if the user lists more than 7, ask which ones could be grouped under a parent. The ~7 children heuristic from `decomposition-semantics.md` applies at every level including the top.

**Failure 3: All outcomes, no enablers**

Agent created 5 outcome nodes but missed that 3 of them shared a database schema dependency. The shared concern should have been an enabler at a lower index.

How to avoid: After collecting candidate nodes, explicitly ask: "Do any of these share infrastructure or dependencies?" Extract shared concerns as enablers before assigning indices.

</failure_modes>

<success_criteria>

Bootstrapping is complete when:

- [ ] Existing tree checked (no overwrite of existing product spec)
- [ ] User interviewed for product identity, hypothesis, and scope
- [ ] Scaffold plan presented and confirmed
- [ ] `spx/{product-name}.product.md` created with hypothesis and scope
- [ ] `spx/CLAUDE.md` created from template with product name
- [ ] Top-level nodes created with correct types, indices, and spec stubs
- [ ] Next steps recommended

</success_criteria>
