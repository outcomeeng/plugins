---
name: bootstrap
description: ALWAYS invoke this skill when setting up a new Product Tree in an empty or absent spx/ directory. NEVER create a Product Tree from scratch without this skill.
allowed-tools: Read, Glob, Grep, Write, Skill
---

<objective>

An initial `spx/` root scaffolded with a product document and product guide, plus recorded top-level structure intent for `/decompose spx/`.

</objective>

<quick_start>

**PREREQUISITE**: Check for `<PRODUCT_TREE_FOUNDATION>` marker. If absent, use skill `product-tree:understand` first.

</quick_start>

<workflow>

<step name="detect">

**Step 1: Check current state**

```bash
Glob: "spx/*.product.md"
Glob: "spx/*-*.{enabler,outcome}/"
```

If a product document already exists, this is not a bootstrap. Redirect to `/author` for single artifacts or `/decompose spx/` for top-level structure.

If `spx/` doesn't exist or contains no product document, proceed.

Also detect **brownfield**: a product already implemented in code while `spx/` is absent or empty (source packages, a README describing shipped behavior, a working CLI or service). Brownfield bootstrap is valid — note it, because it changes how Step 2 gathers top-level intent (see the brownfield guard).

</step>

<step name="interview">

**Step 2: Interview the user**

Use skill `product-tree:interview` and apply its methodology (one question at a time, `AskUserQuestion`, coverage display before each question, pushback) with the product-bootstrap coverage areas below as the interview plan. `/interview` supplies the technique; bootstrapping supplies the coverage areas — do not fork the interview. Take the areas in order, each constraining the next:

1. **Consumers** — who consumes this product? Name distinct personas, not a single "user".
2. **Job-to-be-done** — what job does each consumer hire the product for?
3. **Surfaces** — through which surfaces is it consumed (web UI, CLI, API, library, embedded, file output, …)?
4. **Actors & sidedness** — one party or several (two-sided / multi-party marketplace, admin vs end-user, producer vs consumer)? Name each actor and what they exchange.
5. **Constraints** — hard requirements, compliance, platforms, dependencies.
6. **Success signals** — the behavior change and business value the product bets on (the three-part hypothesis).
7. **Top-level intent** — the major capabilities the product should eventually contain; which are known now, which deferred, and what open issues composition should account for.

Record top-level answers as intent only. Do not assign node types, child names, or indices in bootstrapping — `/decompose spx/` owns structure.

When candidate top-level areas mix aggregate domains, concrete behaviors, surfaces, actors, and code-shaped names, apply the product-domain-shapes classifier and examples from the reference the live `<PRODUCT_TREE_FOUNDATION>` marker lists.

**Brownfield guard — existing code present.** When Step 1 found an implemented codebase, derive top-level intent from the product dimensions above — consumers, jobs, surfaces, actors — never from the code's package, module, directory, or file layout. Pre-analysis of existing code informs vocabulary, constraints, and open decisions; it does not set the partition. Candidate areas named after code components (`config`, `model`, `parser`, `layout`, …) repeat the implementation's filing in the tree and invert the truth hierarchy. `/decompose` enforces the same rule — "decompose by user-facing concern, not implementation layer" — so apply it here and code-shaped intent never reaches it.

Skip questions the conversation already answers.

</step>

<step name="plan">

**Step 3: Present the root scaffold plan**

Before creating anything, show the user what will be created:

```text
Proposed root scaffold:

CLAUDE.md
AGENTS.md
spx/
├── {product-name}.product.md
└── PLAN.md        # optional top-level composition intent for /decompose spx/
```

Include:

- Product name and hypothesis
- Included and excluded product scope
- Top-level composition intent that will be recorded for `/decompose spx/`

Wait for user confirmation before creating files.

</step>

<step name="scaffold">

**Step 4: Create the root scaffold**

1. Create `spx/` directory if it doesn't exist.

2. Write `spx/{product-name}.product.md` using the canonical product template beneath the `Template root` the live `<PRODUCT_TREE_FOUNDATION>` marker records. Fill every section from the interview — leave no `{placeholder}` unresolved:
   - Product name
   - Why this product exists
   - Consumers and jobs, Surfaces, and Actors and sidedness — from the product-dimension coverage areas
   - Three-part hypothesis (output → outcome → impact)
   - Scope (capabilities grouped by the consumer and surface they serve)
   - Product-level compliance rules, if any emerged from interview

3. Use skill `product-tree:update-instruction-block` for the repository root so its generator writes both root instruction blocks — `CLAUDE.md` for this runtime and `AGENTS.md` for the other runtime — from the installed template. `/update-instruction-block` owns instruction-block rendering, enabled-language detection, and any explicit language override.

4. If top-level composition intent exists, write `spx/PLAN.md` with:
   - Candidate product areas from the interview
   - Known constraints, examples, and unresolved questions
   - Explicit note that `/decompose spx/` owns child boundaries, node types, ordering evidence, and indices

</step>

<step name="delegate">

**Step 5: Delegate top-level composition**

After the root scaffold exists, use skill `product-tree:decompose` with `spx/` to compose top-level children. Pass only `spx/`; the root product document and `spx/PLAN.md` carry the user-provided intent.

</step>

<step name="deliver">

**Step 6: Report and recommend**

Summarize what was created:

- Product document path
- `CLAUDE.md` path and `AGENTS.md` path
- `spx/PLAN.md` path, if created
- `/decompose spx/` as the next structural step

Recommend next steps:

- "Compose top-level nodes with `/decompose spx/`"
- "Fill in assertions for created nodes with `/author`"
- "When assertions are ready, establish evidence with `/verify`"

</step>

</workflow>

<failure_modes>

**Failure 1: Bootstrapped over an existing tree**

Claude ran bootstrapping in a product that already had `spx/` with specs, because it read the request as a new product and skipped the existence check. The product document was overwritten.

How to avoid: Step 1 checks for an existing product document. If one exists, redirect to `/author` or `/decompose spx/`.

**Failure 2: Bootstrapping pre-shaped top-level children**

Claude accepted a list of candidate areas, assigned node types and indices during bootstrapping, and skipped the composition workflow. The first tree shape encoded unexamined dependencies.

How to avoid: Bootstrapping records product intent in the product document and root `PLAN.md`; `/decompose spx/` owns top-level child structure.

**Failure 3: Lost top-level intent**

Claude created only the product document and guide, then discarded the user's candidate product areas, because it treated the interview answers as conversation context the next step would still hold. The next composition step ran in a fresh session and had no durable local context.

How to avoid: Write candidate areas, constraints, examples, and unresolved questions to `spx/PLAN.md` before invoking `/decompose spx/`.

**Failure 4: Mirroring the implementation's module layout into top-level intent**

Bootstrapping ran over an existing codebase. Claude read the packages and named the candidate top-level areas after them (`config`, `model`, `format`, `layout`, …), so the tree's shape mirrored how the code happened to be filed. Package boundaries are the lowest layer (Code); letting them shape the highest layer (the tree) inverts the truth hierarchy, and `/decompose spx/` inherits the contamination through `PLAN.md`.

How to avoid: In brownfield, derive top-level intent from consumers, jobs, surfaces, and actors — the product dimensions from Step 2 — not from the module or file layout. Pre-analysis of the code informs vocabulary and constraints, never the partition. Express every candidate area as a user-facing capability; if an area is named after a code component, re-derive it.

</failure_modes>

<success_criteria>

The scaffold is sound when:

- [ ] No existing product document was overwritten; a tree already present redirected to `/author` or `/decompose spx/`
- [ ] The product document states the hypothesis and scope the interview surfaced in atemporal voice and enumerates no child
- [ ] Every candidate top-level area is a user-facing capability derived from consumers, jobs, surfaces, and actors; none is named after a code component
- [ ] The managed sections of `CLAUDE.md` and `AGENTS.md` match the installed template and name only the project's enabled languages
- [ ] `spx/PLAN.md` carries every candidate area, constraint, example, and unresolved question the interview surfaced and assigns no node kind or index
- [ ] The user confirmed the root scaffold plan before any file was written

</success_criteria>
