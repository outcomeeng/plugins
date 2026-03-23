# spx/ Directory Guide (Spec Tree)

This guide explains WHEN to invoke spec-tree skills for the **{product-name}** product. It is a **router** — the skills contain the HOW.

---

## Structure Overview

The `spx/` tree is a durable map of the product. Nothing moves because work is "done" — specs are permanent product truth, not a backlog.

Two node types at any depth:

```text
spx/
  {product-name}.product.md            # Product spec (root)
  NN-{slug}.adr.md                     # Architecture decision
  NN-{slug}.pdr.md                     # Product constraint
  NN-{slug}.enabler/                   # Shared infrastructure
    {slug}.md                          # Spec file
    tests/                             # Co-located tests
    NN-{slug}.{enabler|outcome}/       # Children (any depth)
  NN-{slug}.outcome/                   # Hypothesis + assertions
    {slug}.md                          # Spec file
    tests/                             # Co-located tests
```

---

## Key Principles

1. **Durable map**: Specs stay in place. Nothing moves because work is "done."
2. **Two node types**: Enabler (infrastructure) and outcome (hypothesis + assertions). No other types.
3. **Co-location**: Tests live with their spec in `tests/`.
4. **Atemporal voice**: Specs state product truth. Never narrate history.
5. **Deterministic context**: The tree path defines what context an agent receives.

---

## Sparse Integer Ordering

Numeric prefixes encode dependency order: lower index constrains higher. Same index means independent.

Formula for N items: `i_k = 10 + floor(k * 89 / (N + 1))`

**ALWAYS use full path when referencing nodes** — indices are sibling-unique, not globally unique.

---

## When to Invoke Skills

### Before ANY spec-tree work → `/understanding`

**BLOCKING REQUIREMENT**

Loads the Spec Tree methodology. Emits `<SPEC_TREE_FOUNDATION>` marker. Required once per session.

### Before working on a specific node → `/contextualizing`

**BLOCKING REQUIREMENT**

Walks the tree from product root to target, reads all ancestor specs, lower-index siblings, and ADRs/PDRs.

### When creating specs or nodes → `/authoring`

Create product specs, ADRs/PDRs, enabler nodes, outcome nodes.

### When breaking down a node → `/decomposing`

Decompose when a node has too many assertions (>7) or contains independent concerns.

### When restructuring the tree → `/refactoring`

Move nodes, re-scope assertions, extract shared enablers, consolidate duplicates.

### When checking consistency → `/aligning`

Review, audit, or quality check specs. Find contradictions or gaps.

---

## Quick Reference: Skill Selection

| User Says...             | Invoke             | Do NOT                      |
| ------------------------ | ------------------ | --------------------------- |
| "Implement this outcome" | `/contextualizing` | Read spec files directly    |
| "Create an outcome"      | `/authoring`       | Search for templates        |
| "Add an ADR"             | `/authoring`       | Calculate indices yourself  |
| "This node is too big"   | `/decomposing`     | Split nodes ad hoc          |
| "Move this under that"   | `/refactoring`     | Rename directories manually |
| "Check these specs"      | `/aligning`        | Review without methodology  |
| "Write tests for this"   | `/testing`         | Write tests without spec    |
| "Start the TDD flow"     | `/coding`          | Code without architecture   |

---

## Test Naming Convention

Test level is encoded in the filename. **Delete sections below that don't apply to your project.**

### TypeScript

| Level | Pattern                      | Example                   |
| ----- | ---------------------------- | ------------------------- |
| 1     | `{slug}.unit.test.ts`        | `parsing.unit.test.ts`    |
| 2     | `{slug}.integration.test.ts` | `cli.integration.test.ts` |
| 3     | `{slug}.e2e.test.ts`         | `workflow.e2e.test.ts`    |

### Python

| Level | Pattern                      | Example                   |
| ----- | ---------------------------- | ------------------------- |
| 1     | `test_{slug}_unit.py`        | `test_parsing_unit.py`    |
| 2     | `test_{slug}_integration.py` | `test_cli_integration.py` |
| 3     | `test_{slug}_e2e.py`         | `test_workflow_e2e.py`    |

---

## Assertion-Test Contract

Spec assertions link to their tests inline:

```markdown
### Scenarios

- Given X, when Y, then Z ([test](tests/test_slug_unit.py))
```

Every assertion must link to at least one test file.

---

## Session Management

Claude Code session handoffs are stored in `.spx/sessions/` (separate from the spec tree):

```text
.spx/sessions/
├── todo/          # Available for /pickup
├── doing/         # Currently claimed
└── archive/       # Completed sessions
```

Use `/handoff` to create, `/pickup` to claim.
