<process>

**Step 2: Present skills checklist**

This step comes BEFORE loading node context. The skills checklist tells Claude what to invoke and what to avoid.

Read the `<skills>` section from the session file and present it prominently:

**Critical — invoke before starting work**
These skills are REQUIRED. The previous agent identified them as essential. List each skill with its reasoning.

**Missed — do not repeat these mistakes**
The previous agent skipped these skills and it caused problems. List each missed skill with what went wrong.

**Next action — where to resume**
Show the recommended skill and TDD flow position.

**Step 3: Load node context**

For each node in the `<nodes>` section:

1. **Present status**: Show what was done and what remains.
2. **Check for escape hatches**:
   ```bash
   Glob: "spx/{node-path}/PLAN.md"
   Glob: "spx/{node-path}/ISSUES.md"
   ```
   If found, read and present them — these contain important non-durable context the previous agent persisted as a hedge.
3. Suggest context loading: "To load full spec context for this node, invoke `/contextualizing {node-path}`"

**Step 4: Present persisted artifacts**

Show the `<persisted>` section:

- What was committed (trust these are in place)
- What is uncommitted (may need `/commit` before continuing)
- What insights were written to CLAUDE.md/memory/skills
- What escape hatches were written and where

**Step 5: Present coordination context**

Show the `<coordination>` section — cross-cutting context that does not belong to any single node. This may include:

- Why the previous session ended
- Dependencies between nodes
- Environment or setup requirements
- Open questions or pending decisions

**Step 6: Invoke /contextualizing (MANDATORY)**

NEVER offer the user a choice here. NEVER propose fixes, code, or any implementation work at this point.

The ONLY valid next action after presenting the session is to invoke `/contextualizing` on the target node. The spec-tree methodology forbids all work without loaded context.

If the session references multiple nodes, ask which node to start with. Otherwise, invoke immediately:

```text
Skill tool → { "skill": "spec-tree:contextualizing", "args": "spx/{node-path}" }
```

After context is loaded, THEN ask how to proceed — the loaded context will inform what options make sense.

**Step 7: Verify coordination claims before triaging**

When the coordination section reports failing tests, known bugs, or specific errors, run them first before proposing fixes. The coordination section is a point-in-time snapshot; commits may have landed between handoff-write and pickup-claim that resolved listed failures. Running the tests is cheap (one command); triaging a non-existent failure wastes time and risks mis-diagnosis.

This applies after `/contextualizing` (Step 6) completes, as Claude shifts from loading context to proposing action.

</process>

<success_criteria>

- [ ] Skills checklist presented BEFORE any work starts
- [ ] Each anchored node's status presented
- [ ] PLAN.md / ISSUES.md checked and read if present
- [ ] Persisted artifacts acknowledged
- [ ] `/contextualizing` invoked on target node — NOT offered as an option, just done
- [ ] Failures listed in coordination are verified against current state before triaging
- [ ] Agent knows which skills to invoke and which to avoid

</success_criteria>
