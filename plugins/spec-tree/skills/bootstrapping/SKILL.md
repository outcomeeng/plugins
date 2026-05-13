---
name: bootstrapping
description: ALWAYS invoke this skill when setting up a new spec tree or when /authoring detects an empty spx/ directory. NEVER create a spec tree from scratch without this skill.
allowed-tools: Read, Glob, Grep, Write, Edit
---

<objective>

Interview the user to understand the product, then scaffold the initial `spx/` root with a product spec and product guide. Record top-level structure intent for `/decomposing spx/`, which owns top-level child composition.

</objective>

<quick_start>

**PREREQUISITE**: Check for `<SPEC_TREE_FOUNDATION>` marker. If absent, invoke `/understanding` first.

This skill runs when:

- The user says "bootstrap", "set up spec tree", "start a new product"
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

If a product spec already exists, this is not a bootstrap. Redirect to `/authoring` for single artifacts or `/decomposing spx/` for top-level structure.

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

**Round 3 — Top-level intent:**

- "What major areas, capabilities, or concerns should the product eventually contain?"
- "Which areas are known now, which are deferred, and what open issues should composition account for?"

Record top-level answers as intent only. Do not assign node types, child names, or indices in bootstrapping.

</step>

<step name="plan">

**Step 3: Present the root scaffold plan**

Before creating anything, show the user what will be created:

```text
Proposed root scaffold:

spx/
├── {product-name}.product.md
├── CLAUDE.md
└── PLAN.md        # optional top-level composition intent for /decomposing spx/
```

Include:

- Product name and hypothesis
- Included and excluded product scope
- Top-level composition intent that will be recorded for `/decomposing spx/`

Wait for user confirmation before creating files.

</step>

<step name="scaffold">

**Step 4: Create the root scaffold**

1. Create `spx/` directory if it doesn't exist.

2. Write `spx/{product-name}.product.md` using the template from `${CLAUDE_SKILL_DIR}/../understanding/templates/product/product-name.product.md`. Fill in:
   - Product name
   - Why this product exists
   - Three-part hypothesis (output → outcome → impact)
   - Scope
   - Product-level compliance rules, if any emerged from interview

3. Write `spx/CLAUDE.md` from the template at `${CLAUDE_SKILL_DIR}/templates/spx-claude.md`. Replace `{product-name}` with the actual product name.

4. If top-level composition intent exists, write `spx/PLAN.md` with:
   - Candidate product areas from the interview
   - Known constraints, examples, and unresolved questions
   - Explicit note that `/decomposing spx/` owns child boundaries, node types, ordering evidence, and indices

</step>

<step name="delegate">

**Step 5: Delegate top-level composition**

After the root scaffold exists, invoke `/decomposing spx/` to compose top-level children. Pass only `spx/`; the root product spec and `spx/PLAN.md` carry the user-provided intent.

</step>

<step name="deliver">

**Step 6: Report and recommend**

Summarize what was created:

- Product spec path
- `spx/CLAUDE.md` path
- `spx/PLAN.md` path, if created
- `/decomposing spx/` as the next structural step

Recommend next steps:

- "Compose top-level nodes with `/decomposing spx/`"
- "Fill in assertions for created nodes with `/authoring`"
- "When assertions are ready, write tests with `/testing`"

</step>

</workflow>

<failure_modes>

**Failure 1: Bootstrapped over an existing tree**

Claude ran bootstrapping in a product that already had `spx/` with specs. The product spec was overwritten.

How to avoid: Step 1 checks for an existing product spec. If one exists, redirect to `/authoring` or `/decomposing spx/`.

**Failure 2: Bootstrapping pre-shaped top-level children**

Claude accepted a list of candidate areas, assigned node types and indices during bootstrapping, and skipped the composition workflow. The first tree shape encoded unexamined dependencies.

How to avoid: Bootstrapping records product intent in the product spec and root `PLAN.md`; `/decomposing spx/` owns top-level child structure.

**Failure 3: Lost top-level intent**

Claude created only the product spec and guide, then discarded the user's candidate product areas. The next composition step had no durable local context.

How to avoid: Write candidate areas, constraints, examples, and unresolved questions to `spx/PLAN.md` before invoking `/decomposing spx/`.

</failure_modes>

<success_criteria>

Bootstrapping is complete when:

- [ ] Existing tree checked (no overwrite of existing product spec)
- [ ] User interviewed for product identity, hypothesis, scope, and top-level intent
- [ ] Root scaffold plan presented and confirmed
- [ ] `spx/{product-name}.product.md` created with hypothesis and scope
- [ ] `spx/CLAUDE.md` created from template with product name
- [ ] `spx/PLAN.md` created when top-level intent exists
- [ ] Top-level structure delegated to `/decomposing spx/`
- [ ] Next steps recommended

</success_criteria>
