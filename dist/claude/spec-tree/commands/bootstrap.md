---
description: Set up a new spec tree for this product
---

<objective>
Bootstrap a new spec tree by interviewing the user and scaffolding spx/.
</objective>

<context>
**Working Directory:**
!`pwd`

**Existing spx/ directory:**
!`ls spx/*.product.md 2>/dev/null || echo "No product spec found"`

**Product indicators:**
!`ls pyproject.toml package.json tsconfig.json Cargo.toml go.mod 2>/dev/null || echo "No language indicators found"`

**README (first 20 lines, if present):**
!`head -20 README.md 2>/dev/null || echo "No README.md"`
</context>

<process>
Invoke the bootstrapping skill NOW:

```json
Skill tool → { "skill": "spec-tree:bootstrapping" }
```

The skill interviews the user and scaffolds the initial tree.
</process>

<success_criteria>

- Bootstrapping skill invoked
- Product spec created at spx/{name}.product.md
- spx/CLAUDE.md created
- Top-level nodes scaffolded

</success_criteria>
