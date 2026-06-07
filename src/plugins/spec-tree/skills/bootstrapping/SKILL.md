---
name: bootstrapping
description: ALWAYS invoke this skill when setting up a new spec tree or when /authoring detects an empty spx/ directory. NEVER create a spec tree from scratch without this skill.
allowed-tools: Read, Glob, Grep, Write, Edit, Skill
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

Also detect **brownfield**: a product already implemented in code while `spx/` is absent or empty (source packages, a README describing shipped behavior, a working CLI or service). Brownfield bootstrap is valid — note it, because it changes how Step 2 gathers top-level intent (see the brownfield guard).

</step>

<step name="interview">

**Step 2: Interview the user**

Invoke `/interviewing` and apply its methodology (one question at a time, `AskUserQuestion`, coverage display before each question, pushback) with the product-bootstrap coverage areas below as the interview plan. `/interviewing` supplies the technique; bootstrapping supplies the coverage areas — do not fork the interview. Take the areas in order, each constraining the next:

1. **Consumers** — who consumes this product? Name distinct personas, not a single "user".
2. **Job-to-be-done** — what job does each consumer hire the product for?
3. **Surfaces** — through which surfaces is it consumed (web UI, CLI, API, library, embedded, file output, …)?
4. **Actors & sidedness** — one party or several (two-sided / multi-party marketplace, admin vs end-user, producer vs consumer)? Name each actor and what they exchange.
5. **Constraints** — hard requirements, compliance, platforms, dependencies.
6. **Success signals** — the behavior change and business value the product bets on (the three-part hypothesis).
7. **Top-level intent** — the major capabilities the product should eventually contain; which are known now, which deferred, and what open issues composition should account for.

Record top-level answers as intent only. Do not assign node types, child names, or indices in bootstrapping — `/decomposing spx/` owns structure.

**Brownfield guard — existing code present.** When Step 1 found an implemented codebase, derive top-level intent from the product dimensions above — consumers, jobs, surfaces, actors — never from the code's package, module, directory, or file layout. Pre-analysis of existing code informs vocabulary, constraints, and open decisions; it does not set the partition. Candidate areas named after code components (`config`, `model`, `parser`, `layout`, …) repeat the implementation's filing in the tree and invert the truth hierarchy. `/decomposing` enforces the same rule — "decompose by user-facing concern, not implementation layer" — so apply it here and code-shaped intent never reaches it.

Skip questions the conversation already answers.

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

2. Write `spx/{product-name}.product.md` using the template from `${CLAUDE_SKILL_DIR}/../understanding/templates/product/product-name.product.md`. Fill every section from the interview — leave no `{placeholder}` unresolved:
   - Product name
   - Why this product exists
   - Consumers and jobs, Surfaces, and Actors and sidedness — from the product-dimension coverage areas
   - Three-part hypothesis (output → outcome → impact)
   - Scope (capabilities grouped by the consumer and surface they serve)
   - Product-level compliance rules, if any emerged from interview

3. Render the runtime's spx-level guide — `spx/CLAUDE.md` under Claude Code, `spx/AGENTS.md` under Codex — from the template via the update-spx helper, passing the product name and the project's enabled languages so the guide carries its `product_name` and `languages` config (and a later `/update-spx` re-renders from it):

   ```bash
   python3 "${CLAUDE_SKILL_DIR}/../update-spx/scripts/update_spx.py" --template "${CLAUDE_SKILL_DIR}/../understanding/templates/spx-claude.md" --product <runtime-guide-path> --name "<product name>" --languages <comma-separated-languages> --write
   ```

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

**Failure 4: Mirroring the implementation's module layout into top-level intent**

Bootstrapping ran over an existing codebase. Claude read the packages and named the candidate top-level areas after them (`config`, `model`, `format`, `layout`, …), so the tree's shape mirrored how the code happened to be filed. Package boundaries are the lowest layer (Code); letting them shape the highest layer (the tree) inverts the truth hierarchy, and `/decomposing spx/` inherits the contamination through `PLAN.md`.

How to avoid: In brownfield, derive top-level intent from consumers, jobs, surfaces, and actors — the product dimensions from Step 2 — not from the module or file layout. Pre-analysis of the code informs vocabulary and constraints, never the partition. Express every candidate area as a user-facing capability; if an area is named after a code component, re-derive it.

</failure_modes>

<success_criteria>

Bootstrapping is complete when:

- [ ] Existing tree checked (no overwrite of existing product spec); brownfield (existing code) detected if present
- [ ] User interviewed across consumers, jobs, surfaces, actors/sidedness, constraints, success signals, and top-level intent
- [ ] Brownfield: top-level intent derived from product dimensions, not the code's module or file layout
- [ ] Root scaffold plan presented and confirmed
- [ ] `spx/{product-name}.product.md` created with hypothesis and scope
- [ ] `spx/CLAUDE.md` created from template with product name
- [ ] `spx/PLAN.md` created when top-level intent exists
- [ ] Top-level structure delegated to `/decomposing spx/`
- [ ] Next steps recommended

</success_criteria>
