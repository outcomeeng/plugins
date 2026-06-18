<required_reading>none</required_reading>

<process>

**Step 2: Load Spec Tree foundation**

This step comes immediately after the session is claimed and the canonical claim markers are emitted. It comes before reading or presenting session details, checking out a work branch, inspecting anchored nodes, or touching node-local coordination notes.

Invoke `/understand` now:

```text
Skill tool -> { "skill": "spec-tree:understand" }
```

If `<SPEC_TREE_FOUNDATION>` is already present, the skill may skip its body. Do not process the session's `<skills>`, `<nodes>`, `<persisted>`, or `<coordination>` sections until this foundation step has completed.

**Step 3: Present skills checklist**

This step comes BEFORE loading node context. The skills checklist tells Claude what to invoke and what to avoid.

Read the `<skills>` section from the session file and present it prominently:

**Critical — invoke before starting work**
These skills are REQUIRED. The previous Claude context identified them as essential. List each skill with its reasoning.

**Missed — do not repeat these mistakes**
The previous Claude context skipped these skills and it caused problems. List each missed skill with what went wrong.

**Next action — where to resume**
Show the recommended skill and TDD flow position.

**Step 4: Check out the work branch**

Read the `git_ref` field from the session frontmatter. When it names a feature branch on origin — a branch name such as `work/…`, not the default branch and not a bare commit SHA — fetch and check that branch out **before** loading node context. The spec-tree state the session points at lives on that branch, and `/handoff`'s persistence precondition guarantees it exists on origin:

```bash
git fetch origin <git_ref>
```

Then check it out per the checkout kind:

- **Bare-repository worktree pool** — claim the branch in a **free** pool worktree, never the main checkout. A pool worktree is free only when no live Claude session holds it: read its occupancy with `spx worktree status <pool-worktree>` and enter only a worktree the command reports unclaimed or stale (a claim whose holding Claude session is dead). Git cleanliness is not freedom — a clean, detached worktree can still be actively held by Claude between commits or mid-think. Run `git -C <pool-worktree> switch <git_ref>`, or `git worktree add` a fresh one, then record occupancy with `spx worktree claim <pool-worktree>` so no other Claude session reuses the worktree while Claude holds it — no runtime hook claims it. When `spx worktree status` is unavailable or errors, occupancy is unreadable; `git worktree add` a fresh worktree rather than reuse an existing one, so no held worktree is entered.
- **Single working tree** — `git switch <git_ref>` from a clean tree.

**Foreign-pool guardrail.** Operate only inside a pool Claude participates in. A worktree in a `.spx/` pool Claude does not participate in — another product's checkout — is off-limits regardless of how free its git state looks; treat it as occupied. The claim protocol coordinates only Claude sessions that share one pool.

When `git_ref` names the default branch or is a bare commit SHA, the work landed on the default branch with no feature branch — skip this step and read the spec tree from there.

**Step 5: Inspect anchored nodes**

For each node in the `<nodes>` section:

1. **Present status from the session file**: Show what the handoff recorded as done and remaining.
2. **Check for coordination note paths only**:
   ```bash
   Glob: "spx/{node-path}/PLAN.md"
   Glob: "spx/{node-path}/ISSUES.md"
   ```
   If found, list their paths. Do not read `PLAN.md` or `ISSUES.md` content in this step. `/contextualize` reads node-local coordination notes after product context and ancestry are loaded; acting on note content before then violates the spec-tree context guarantee.

**Step 6: Present persisted artifacts**

Show the `<persisted>` section:

- What was committed (trust these are in place)
- What is uncommitted (may need `/commit` before continuing)
- What insights were written to CLAUDE.md/memory/skills
- What coordination notes were written and where

**Step 7: Present coordination context**

Show the `<coordination>` section — cross-cutting context that does not belong to any single node. This may include:

- Why the previous session ended
- Dependencies between nodes
- Environment or setup requirements
- Open questions or pending decisions

**Step 8: Invoke /contextualize (MANDATORY)**

NEVER offer the user a choice here. NEVER propose fixes, code, or any implementation work at this point.

The ONLY valid next action after presenting the session is to invoke `/contextualize` on the target node. The spec-tree methodology forbids all work without loaded context.

If the session references multiple nodes, ask which node to start with. Otherwise, invoke immediately:

```text
Skill tool → { "skill": "spec-tree:contextualize", "args": "spx/{node-path}" }
```

After context is loaded, STOP and present a post-context checkpoint:

- Target node and its current state
- Recommended next action from the handoff
- Persisted artifacts or coordination items that could change the next move

`/contextualize` reads the note content for any found `PLAN.md` or `ISSUES.md`. Treat those notes as stale-prone inputs and verify them against the loaded specs, decisions, assertions, tests, implementation, and current user intent before they steer work.

If `$ARGUMENTS` includes `--auto-continue`, acknowledge the override and resume with the recommended next action.

Otherwise, use `AskUserQuestion` with exactly one question and 2-4 options. The options must come from the loaded context:

- Include the recommended next action as the first option
- Include "Review persisted artifacts first" only when persisted artifacts or coordination notes exist
- Include "Re-check coordination claims first" only when coordination reports failing tests, bugs, or errors
- Include "Take a different approach" only when the loaded context reveals a real alternative

Wait for the user's selection before continuing. The checkpoint completes only after the `AskUserQuestion` response is received.

After the checkpoint completes, emit a canonical post-context marker using the claimed session id from `<PICKUP_CLAIM>` and carry the full claimed-session set from the most recent `<CLAIMED_SESSIONS ids="...">`:

```text
<PICKUP_CHECKPOINT id="[claimed-session-id]" claimed="[first-pickup],...,[claimed-session-id]" target="spx/{node-path}" mode="[ask|auto-continue]">
  next_action: [selected or resumed next action]
</PICKUP_CHECKPOINT>
```

If the checkpoint used `AskUserQuestion`, record the selected option in `next_action`. If `--auto-continue` was used, record the resumed next action and `mode="auto-continue"`. The `claimed` attribute mirrors the latest `<CLAIMED_SESSIONS>` so handoff workflows can read a single marker.

After emitting the checkpoint marker, report the result and the current session state. Do not infer that successful verification means closure. State which sessions remain claimed in `doing`.

**Valid next steps after a completed checkpoint:**

- Continue work under the claimed session(s).
- Invoke `/handoff` if the user asks to close or hand off.
- Invoke `/handoff --no-session` if the user asks to close without creating a handoff. It archives the claimed sessions; it does NOT put the claimed session back in the todo queue. If the user explicitly wants a claimed session returned to the shared queue, run `spx session release <id>` to move it from `doing/` back to `todo/`.

**Invalid next steps:**

- `spx session archive` — pickup never archives.
- `spx session release` as a substitute for the close workflow — skips claimed-session accounting, reflection, and archival; use `/handoff --no-session` for proper closure.
- Creating a replacement handoff to justify closing the claimed session — no new session is permission to close an existing one.

NEVER invoke `/apply`, author ADRs/tests/code, or edit files before this checkpoint completes.

**Step 9: Verify coordination claims before triaging**

When the coordination section reports failing tests, known bugs, or specific errors, run them first before proposing fixes. The coordination section is a point-in-time snapshot; commits may have landed between handoff-write and pickup-claim that resolved listed failures. Running the tests is cheap (one command); triaging a non-existent failure wastes time and risks mis-diagnosis.

This applies after the post-context checkpoint in Step 8 completes, or after the explicit `--auto-continue` override is acknowledged.

</process>

<success_criteria>

- [ ] `/understand` invoked immediately after claim markers and before session details are processed
- [ ] Skills checklist presented BEFORE any work starts beyond foundation loading
- [ ] When the session `git_ref` names a feature branch, that branch is fetched and checked out before node context is loaded (Step 4)
- [ ] Each anchored node's status presented
- [ ] PLAN.md / ISSUES.md paths checked before context loading, with note content read by `/contextualize`
- [ ] Persisted artifacts acknowledged
- [ ] `/contextualize` invoked on target node — NOT offered as an option, just done
- [ ] Canonical post-context marker emitted as `<PICKUP_CHECKPOINT id="..." claimed="...">` with the full claimed-session set
- [ ] Claimed session remains in `doing` after the checkpoint — pickup workflow never archives or releases
- [ ] Post-context decision captured via `AskUserQuestion` response, or explicit `--auto-continue` override acknowledged
- [ ] No `/apply`, ADR, test, code, or file-editing work starts before the checkpoint or override
- [ ] Failures listed in coordination are verified against current state before triaging
- [ ] Claude knows which skills to invoke and which to avoid

</success_criteria>
