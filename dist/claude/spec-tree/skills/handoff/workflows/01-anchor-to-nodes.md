<objective>
A node anchor list covering every spec-tree node worked on during this session, with each entry tied to durable spec-tree locations so the next Claude context can load context via `/contextualize`.

</objective>

<process>
List every spec-tree node touched in this session (any path matching `spx/**/*.enabler` or `spx/**/*.outcome`). For each, record:

- Full path (e.g., `spx/55-example.enabler/21-bar.outcome`)
- What was done (spec authored, tests written, code implemented, etc.)
- Test status (passing, failing, not yet written)
- TDD flow position if applicable (step 1-8 per `/apply` skill)

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

If "Create a node now" → invoke `/author` to create the node, then return to this workflow.

</no_nodes_case>

<success_criteria>

- Every node worked on is listed with full path, what was done, test status, and TDD position.
- If no nodes: user has confirmed the reason, or a node has been created.

</success_criteria>
