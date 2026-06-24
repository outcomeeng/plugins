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

- **Bare-repository worktree pool** — claim the branch in a **free** pool worktree, never the main checkout. A pool worktree is free only when no live Claude session holds it: read its occupancy with `spx worktree status <pool-worktree>` and enter only a worktree the command reports `free`. Git cleanliness is not freedom — a clean, detached worktree can still be actively held by Claude between commits or mid-think. Run `git -C <pool-worktree> switch <git_ref>`, or `git worktree add` a fresh one, then record occupancy with `spx worktree claim <pool-worktree>` so no other Claude session reuses the worktree while Claude holds it — no runtime hook claims it. When `spx worktree status` is unavailable or errors, occupancy is unreadable; `git worktree add` a fresh worktree rather than reuse an existing one, so no held worktree is entered.
- **Single working tree** — `git switch <git_ref>` from a clean tree.

**Foreign-pool guardrail.** Operate only inside a pool Claude participates in. A worktree in a `.spx/` pool Claude does not participate in — another product's checkout — is off-limits regardless of how free its git state looks; do not enter it. The claim protocol coordinates only Claude sessions that share one pool.

When `git_ref` names the default branch or is a bare commit SHA, the work landed on the default branch with no feature branch — skip this checkout step. Do not treat the current checkout as authoritative product truth yet: a detached worktree parked at a bare SHA, or a stale default-branch checkout, can sit behind `origin/<default>`.

**Step 4b: Bring the checkout current — sync before presenting**

Before inspecting anchored nodes, presenting any session detail, or touching coordination notes, bring the checkout current for **every** `git_ref` kind — feature branch, default branch, or commit SHA — by invoking `/sync-base`. A session file records claims that were true at handoff time; reading or presenting them against a stale checkout is the exact failure this step prevents (a base that advanced over an anchored node makes the recorded snapshot silently wrong). Do not defer the sync to `/contextualize` (Step 8) — the reconciliation and presentation below must read current product truth, never the parked commit. `/sync-base` advances a clean behind-base detached checkout to the base tip and rebases a behind-base branch; act on its result as `/sync-base` documents.

**Step 5: Reconcile recorded claims against current state**

Do not present the session file's recorded claims as if they were current — the session document is a pointer whose detail is re-derived from the repository, not a source of truth. Reconcile every recorded claim against the now-current checkout by running the verification script, then present its result in place of the recorded snapshot:

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/verify_session_claims.py" <claimed-session-id> --repo <repo-root>
```

Pass the session id from `<PICKUP_CLAIM>`, never a `.spx/sessions/...` path. The `spx` CLI owns the shared session store in both single-worktree and bare-pool layouts; the verifier reads it through `spx session show --json` and `spx session show`.

The script reads only — it reaches `spx session show`, `spx spec status`, `gh`, and `git` to observe, never to mutate — and emits one verdict per recorded claim:

- `Confirmed` — current state matches the recorded claim.
- `Discrepancy` — current state differs (a base that advanced over the node, a commit absent from history, a tree now dirty, a renamed path). Surface these prominently before any work proceeds.
- `Unverifiable` — the check could not run (a tool absent, a claim the script cannot parse). Present it as such; never treat it as `Confirmed`.

Present the per-claim verdict report. Then, for each node in the `<nodes>` section, check for coordination-note paths only:

```bash
Glob: "spx/{node-path}/PLAN.md"
Glob: "spx/{node-path}/ISSUES.md"
```

If found, list their paths. Do not read `PLAN.md` or `ISSUES.md` content in this step. `/contextualize` reads node-local coordination notes after product context and ancestry are loaded; acting on note content before then violates the spec-tree context guarantee.

**Step 6: Present persisted artifacts**

Show the `<persisted>` section:

- What was committed (trust these are in place)
- What is uncommitted (may need `/commit-changes` before continuing)
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

If the session references a single node, invoke `/contextualize` on it immediately. If it references multiple nodes, do NOT ask on multiplicity alone — select the contextualization target by trying these rules in priority order and taking the first that resolves exactly one node, falling through to the next rule when a rule matches zero nodes or more than one:

1. The node named in the `next_step` field immediately after a `/contextualize` reference.
2. The node named on the `<skills>` "## Next action" line — the `spx/{node-path}` in its `/contextualize {node-path}` entry, or in its "TDD flow position: step N … on `spx/{node-path}`" line.
3. The first `<nodes>` entry whose "Coordination notes" list a `PLAN.md` or `ISSUES.md` path.
4. The first node listed in `<nodes>`.

Rule 4 always resolves a single node, so node multiplicity never triggers a user question — selection is deterministic. Ask the user which node to start with only when `<nodes>` is empty or unreadable. After loading the first target, contextualize additional nodes only when the next action touches them.

Invoke on the selected node:

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

**Step 9: Act on the Step 5 verdicts before triaging**

The Step 5 verification pass already reconciled every recorded claim against current state, so do not re-run a narrow per-failure check it already covered. Act on its verdict report instead: a `Discrepancy` on an injected path or the working tree means the recorded picture no longer holds — investigate it before trusting any dependent claim or proposing a fix. Node status and external ids never emit `Discrepancy`; instead, a `Confirmed` node-status or external-id verdict whose surfaced value differs from what the session prose recorded means that state changed since handoff — compare the value against the prose and act on the difference. An `Unverifiable` verdict is an unconfirmed claim, not a passing one — treat it as needing confirmation, never as `Confirmed`. The coordination section remains a point-in-time snapshot; where it names a failure the verdicts do not cover, confirm it against current state before triaging.

This applies after the post-context checkpoint in Step 8 completes, or after the explicit `--auto-continue` override is acknowledged.

</process>

<success_criteria>

- [ ] `/understand` invoked immediately after claim markers and before session details are processed
- [ ] Skills checklist presented BEFORE any work starts beyond foundation loading
- [ ] When the session `git_ref` names a feature branch, that branch is fetched and checked out before node context is loaded (Step 4)
- [ ] Checkout brought current via `/sync-base` before any session detail is presented, for every `git_ref` kind (Step 4b)
- [ ] Recorded claims reconciled by running `verify_session_claims.py`, and per-claim verdicts (`Confirmed` / `Discrepancy` / `Unverifiable`) presented in place of the recorded snapshot, before the checkpoint (Step 5)
- [ ] PLAN.md / ISSUES.md paths checked before context loading, with note content read by `/contextualize`
- [ ] Persisted artifacts acknowledged
- [ ] `/contextualize` invoked on target node — NOT offered as an option, just done
- [ ] When the session references multiple nodes, the `/contextualize` target is selected deterministically by the priority order (rule 4 always resolves), so node multiplicity never triggers a user question — the user is asked which node only when `<nodes>` is empty or unreadable
- [ ] Canonical post-context marker emitted as `<PICKUP_CHECKPOINT id="..." claimed="...">` with the full claimed-session set
- [ ] Claimed session remains in `doing` after the checkpoint — pickup workflow never archives or releases
- [ ] Post-context decision captured via `AskUserQuestion` response, or explicit `--auto-continue` override acknowledged
- [ ] No `/apply`, ADR, test, code, or file-editing work starts before the checkpoint or override
- [ ] Failures listed in coordination are verified against current state before triaging
- [ ] Claude knows which skills to invoke and which to avoid

</success_criteria>
