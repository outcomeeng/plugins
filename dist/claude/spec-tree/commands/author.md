---
description: Author a spec tree artifact (product, ADR, PDR, enabler, outcome)
argument-hint: [artifact type or description]
---

<objective>
Create or extend a spec tree artifact. Handles product specs, decision records, and nodes.
</objective>

<context>
**Arguments:** `$ARGUMENTS`

**Working Directory:**
!`pwd`

**Spec tree state:**
!`ls spx/*.product.md 2>/dev/null || echo "No product spec — bootstrap first"`

**Top-level nodes:**
!`ls -d spx/*-*.enabler spx/*-*.outcome 2>/dev/null || echo "No nodes yet"`

**Recent ADRs/PDRs:**
!`ls spx/*-*.adr.md spx/*-*.pdr.md 2>/dev/null || echo "No decision records yet"`
</context>

<process>
Invoke the authoring skill NOW:

```json
Skill tool → { "skill": "spec-tree:authoring" }
```

The skill determines the artifact type from $ARGUMENTS and the conversation context. If no product spec exists, it redirects to `/bootstrapping`.
</process>

<success_criteria>

- Authoring skill invoked with argument context
- Artifact created at the correct location with correct index
- Atemporal voice validated

</success_criteria>
