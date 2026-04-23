<objective>
Identify every spec-tree node worked on during this session. This anchors the handoff to durable locations in the spec tree so the next agent can load context via `/contextualizing`.

</objective>

<process>
Scan the conversation for spec-tree nodes that were worked on. For each node, record:

- Full path (e.g., `spx/21-foo.enabler/32-bar.outcome`)
- What was done (spec authored, tests written, code implemented, etc.)
- Test status (passing, failing, not yet written)
- TDD flow position if applicable (step 1-8 per `/applying` skill)

</process>

<no_nodes_case>
If NO spec-tree nodes were involved in this session, use `AskUserQuestion`:

```json
{
  "questions": [{
    "question": "This session's work isn't anchored to any spec-tree node. Why?",
    "header": "Node anchor",
    "multiSelect": false,
    "options": [
      { "label": "Create a node now", "description": "Pause handoff to author a node that captures this work, then resume." },
      { "label": "Exploratory / cross-cutting", "description": "Work doesn't belong to a specific node (infrastructure, tooling, research). Proceed with justification." },
      { "label": "Plugin / methodology work", "description": "Work was on the plugin or methodology itself, not on product specs." }
    ]
  }]
}
```

If "Create a node now" → invoke `/authoring` to create the node, then return to this workflow.

</no_nodes_case>

<success_criteria>

- Every node worked on is listed with full path, what was done, test status, and TDD position.
- If no nodes: user has confirmed the reason, or a node has been created.

</success_criteria>
