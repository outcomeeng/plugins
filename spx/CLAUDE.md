# spx/ Directory Guide (Spec Tree)

This guide explains WHEN to invoke spec-tree skills. It is a **router** that tells you which skill to use. The skills themselves contain the HOW.

---

## Structure Overview

The `spx/` tree is a durable map of the product. Nothing moves because work is "done" — specs are permanent product truth, not a backlog.

Two node types at any depth:

```text
spx/
  {product-name}.product.md           # Product spec (root)
  NN-{slug}.adr.md                    # Architecture decision
  NN-{slug}.pdr.md                    # Product constraint
  NN-{slug}.enabler/                  # Shared infrastructure
    {slug}.md                         # Spec file
    tests/                            # Co-located tests
    NN-{slug}.{enabler|outcome}/      # Children (any depth)
  NN-{slug}.outcome/                  # Hypothesis + assertions
    {slug}.md                         # Spec file
    tests/                            # Co-located tests
```

---

## Key Principles

1. **Durable map**: Specs stay in place. Nothing moves because work is "done."
2. **Two node types**: Enabler (infrastructure) and outcome (hypothesis + assertions). No other types.
3. **Co-location**: Tests live with their spec in `tests/`.
4. **Atemporal voice**: Specs state product truth. Never narrate history.
5. **Deterministic context**: The tree path defines what context an agent receives.
6. **Decision records win by hierarchy**: If a spec contradicts an ADR or PDR in its ancestry, the spec is wrong. Rewrite the spec to align with the decision record before any implementation work.
7. **Decision records updated in-place**: When a decision changes, update the ADR/PDR directly. No "superseded" workflow.

---

## Sparse Integer Ordering

Numeric prefixes encode dependency order: lower index constrains higher. Same index means independent.

Formula for N items: `i_k = 10 + floor(k * 89 / (N + 1))`

For N=7: 21, 32, 43, 54, 65, 76, 87.

```text
15-auth-strategy.adr.md              # Constrains everything at 16+
21-test-harness.enabler/             # Depends on 15; constrains 22+
32-auth.outcome/                     # Independent of billing
32-billing.outcome/                  # Independent of auth
43-integration.outcome/              # Depends on BOTH 32s
```

**ALWAYS use full path when referencing nodes:**

| Wrong                  | Correct                                     |
| ---------------------- | ------------------------------------------- |
| "32-parser.outcome"    | "21-infra.enabler/32-parser.outcome"        |
| "implement outcome-43" | "implement 21-infra.enabler/43-api.outcome" |

---

## When to Invoke Skills

### Before ANY spec-tree work → `/understanding`

**BLOCKING REQUIREMENT**

Loads the Spec Tree methodology. Emits `<SPEC_TREE_FOUNDATION>` marker. Required once per session.

### Before working on a specific node → `/contextualizing`

**BLOCKING REQUIREMENT**

**Trigger conditions:**

- User says "implement this node", "work on X"
- You're about to read, write, or modify a spec
- You need to understand what constrains a node

**What it does**: Walks the tree from product root to target, reads all ancestor specs, lower-index siblings, and ADRs/PDRs.

### When creating specs or nodes → `/authoring`

**Trigger conditions:**

- User says "create a product spec", "add an ADR", "create an outcome node"
- You need templates or index assignment

### When breaking down a node → `/decomposing`

**Trigger conditions:**

- A node has too many assertions (>7)
- A node contains independent concerns

### When restructuring the tree → `/refactoring`

**Trigger conditions:**

- Moving a node between parents
- Re-scoping assertions across nodes
- Extracting shared enablers
- Consolidating duplicate nodes

### When checking consistency → `/aligning`

**Trigger conditions:**

- Review, audit, or quality check on specs
- Finding contradictions or gaps across nodes

---

## Quick Reference: Skill Selection

| User Says...             | Invoke             | Do NOT                      |
| ------------------------ | ------------------ | --------------------------- |
| "Implement this outcome" | `/contextualizing` | Read spec files directly    |
| "Create a product spec"  | `/authoring`       | Search for templates        |
| "Add an ADR"             | `/authoring`       | Calculate indices yourself  |
| "This node is too big"   | `/decomposing`     | Split nodes ad hoc          |
| "Move this under that"   | `/refactoring`     | Rename directories manually |
| "Check these specs"      | `/aligning`        | Review without methodology  |
| "Write tests for this"   | `/testing`         | Write tests without spec    |
| "Start the TDD flow"     | `/coding`          | Code without architecture   |

---

## Test Naming Convention

Test level is encoded in the filename. Naming patterns vary by language — **delete sections that don't apply to your project.**

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

**Any test level can exist at any node.** The level describes what KIND of test, not where in the tree it lives.

---

## Assertion-Test Contract

Spec assertions link to their tests inline:

```markdown
### Scenarios

- Given a parser in strict mode, when invalid input is provided, then a ParseError is raised ([test](tests/test_parser_unit.py))

### Properties

- Parsing is deterministic: same input always produces same output ([test](tests/test_parser_unit.py))
```

Every assertion must link to at least one test file. The link is a contract.

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
