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

After context is loaded, STOP and present a post-context checkpoint:

- Target node and its current state
- Recommended next action from the handoff
- Persisted artifacts or coordination items that could change the next move

If `$ARGUMENTS` includes `--auto-continue`, acknowledge the override and resume with the recommended next action.

Otherwise, use `AskUserQuestion` with exactly one question and 2-4 options. The options must come from the loaded context:

- Include the recommended next action as the first option
- Include "Review persisted artifacts first" only when persisted artifacts or escape hatches exist
- Include "Re-check coordination claims first" only when coordination reports failing tests, bugs, or errors
- Include "Take a different approach" only when the loaded context reveals a real alternative

Wait for the user's selection before continuing. The checkpoint completes only after the `AskUserQuestion` response is received.

After the checkpoint completes, emit a canonical post-context marker using the claimed session id from `<PICKUP_CLAIM>` and carry the full session scope from the most recent `<SESSION_SCOPE ids="...">`:

```text
<PICKUP_CHECKPOINT id="[claimed-session-id]" scope="[first-pickup],...,[claimed-session-id]" target="spx/{node-path}" mode="[ask|auto-continue]">
  next_action: [selected or resumed next action]
</PICKUP_CHECKPOINT>
```

If the checkpoint used `AskUserQuestion`, record the selected option in `next_action`. If `--auto-continue` was used, record the resumed next action and `mode="auto-continue"`. The `scope` attribute mirrors the latest `<SESSION_SCOPE>` so handoff workflows can read a single marker.

After emitting the checkpoint marker, report the result and the current session state. Do not infer that successful verification means closure. State which sessions remain claimed in `doing`.

**Valid next steps after a completed checkpoint:**

- Continue work under the claimed session(s).
- Invoke `/handing-off` if the user asks to close or hand off.
- Invoke `/release` if the user asks to close without creating a handoff. `/release` is an alias for `/handing-off --no-session` — it archives the in-scope sessions; it does NOT put the claimed session back in the todo queue. If the user explicitly wants a claimed session returned to the shared queue, that requires a manual file move from `.spx/sessions/doing/` to `.spx/sessions/todo/`.

**Invalid next steps:**

- `spx session archive` — pickup never archives.
- `spx session release` run directly — not a real CLI command; use `/release` (which runs `/handing-off --no-session`) so scope accounting runs, or move the session file manually if putting back in todo.
- Creating a replacement handoff to justify closing the claimed session — no new session is permission to close an existing one.

NEVER invoke `/applying`, author ADRs/tests/code, or edit files before this checkpoint completes.

**Step 7: Verify coordination claims before triaging**

When the coordination section reports failing tests, known bugs, or specific errors, run them first before proposing fixes. The coordination section is a point-in-time snapshot; commits may have landed between handoff-write and pickup-claim that resolved listed failures. Running the tests is cheap (one command); triaging a non-existent failure wastes time and risks mis-diagnosis.

This applies after the post-context checkpoint in Step 6 completes, or after the explicit `--auto-continue` override is acknowledged.

</process>

<success_criteria>

- [ ] Skills checklist presented BEFORE any work starts
- [ ] Each anchored node's status presented
- [ ] PLAN.md / ISSUES.md checked and read if present
- [ ] Persisted artifacts acknowledged
- [ ] `/contextualizing` invoked on target node — NOT offered as an option, just done
- [ ] Canonical post-context marker emitted as `<PICKUP_CHECKPOINT id="..." scope="...">` with the full session scope
- [ ] Claimed session remains in `doing` after the checkpoint — pickup workflow never archives or releases
- [ ] Post-context decision captured via `AskUserQuestion` response, or explicit `--auto-continue` override acknowledged
- [ ] No `/applying`, ADR, test, code, or file-editing work starts before the checkpoint or override
- [ ] Failures listed in coordination are verified against current state before triaging
- [ ] Agent knows which skills to invoke and which to avoid

</success_criteria>
