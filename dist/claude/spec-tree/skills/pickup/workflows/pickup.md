<required_reading>none</required_reading>

<process>

**Step 2: Load Spec Tree foundation**

This step comes immediately after the session is claimed and the canonical claim markers are emitted. It comes before reading or presenting session details, checking out a work branch, inspecting anchored nodes, or touching node-local coordination notes.

Invoke `/understand` now:

```text
Skill tool -> { "skill": "spec-tree:understand" }
```

If `<SPEC_TREE_FOUNDATION>` is already present, the skill may skip its body. Do not process the session's `<nodes>`, `<persisted>`, or `<coordination>` sections until this foundation step has completed.

**Step 2b: Hold the pickup proposal contract**

Before asking the operator to continue, build a no-surprises proposal. The operator is approving a course of work, not choosing from raw session metadata. Claude must collect enough evidence through the workflow to state:

- Expected outcome — what product or workflow state will be true if continuation succeeds.
- Current classification — `actionable_here`, `owned_elsewhere`, `stale_or_superseded`, `blocked_on_external_dependency`, or `needs_operator_direction`.
- Changed product surface — answer which user-facing, operator-facing, methodology-facing, command, workflow, document, API, page, data projection, configuration, generated contract, skill contract, or other shipped product behavior is likely to be better if continuation succeeds. Before `/contextualize`, use the current session evidence without raw repository storage words; after `/contextualize`, refine the wording with the loaded node context. This is a value field, so keep transport, storage, and artifact identifiers out of it: no PR numbers or links, branch names, commit SHAs, merge commits, file names, file paths, generated-output paths, marketplace-source paths, installed-version receipts, CI/check ids, session ids, or archive receipts. Put those mechanics under inspection references or remaining-work expectation instead.
- Planned skill path — methodology, authoring, testing, audit, review, commit, merge, or lifecycle skills expected before completion.
- Evidence infrastructure — known test files, harnesses, generators, fixtures, evals, audit agents, review agents, generated artifacts, and validation commands the work is expected to touch or depend on.
- Verification plan — deterministic commands and agentic gates expected before reporting completion.
- Inspection references — where the operator can inspect the result: PR, commit, local file paths, generated `dist/` paths, session id, run token, or command output summary.
- Remaining-work expectation — whether completion leaves no continuation, creates or updates a coordination note, parks on an external blocker, or defers to an existing session owner.

The proposal does not need to enumerate every eventual file. It must name the known surfaces and evidence categories clearly enough that approval does not hide foreseeable work. After the operator approves continuation, avoid surprises: if a new required skill, evidence surface, external dependency, ownership conflict, or verification class appears that was not represented in the proposal, stop at the next safe checkpoint and present the delta before continuing.

**Step 3: Check out the work branch**

Read the `git_ref` field from the session frontmatter. When it names a feature branch on origin — a branch name such as `work/…`, not the default branch and not a bare commit SHA — fetch and check that branch out **before** loading node context. The spec-tree state the session points at lives on that branch, and `/handoff`'s persistence precondition guarantees it exists on origin:

```bash
git fetch origin <git_ref>
```

Then check it out per the checkout kind:

- **Bare-repository worktree pool** — bring the work branch into the **assigned worktree**: the working directory the session started in, which the `SessionStart` hook claims at session start. Stay there — never enter a different pool worktree, never `git worktree add` a fresh one, and never hand-record a claim; recording the worktree-occupancy claim is the `SessionStart` hook's sole job, and a worktree or branch conflict is resolved by branching in the assigned worktree, never by relocating to another. Before switching, confirm through `spx worktree status` that the assigned worktree carries this session's running claim — that it reports the worktree `running` for the current session. When it does not — the hook was disabled (`SPECTREE_SESSION_HOOK_DISABLED=1`) or could not reach `spx`, so the claim never landed — surface the unclaimed worktree through `/diagnose` so the hook is repaired, because another agent may otherwise treat it as free; this check is read-only and records nothing. Then run `git switch <git_ref>` in the assigned worktree to attach the work branch; when that branch is already checked out in another live worktree, branch in the assigned worktree and continue rather than entering the worktree that holds it.
- **Single working tree** — `git switch <git_ref>` from a clean tree.

**Foreign-pool guardrail.** Operate only inside a pool Claude participates in. A worktree in a `.spx/` pool Claude does not participate in — another product's checkout — is off-limits regardless of how free its git state looks; do not enter it. The claim protocol coordinates only Claude sessions that share one pool.

When `git_ref` names the default branch or is a bare commit SHA, the work landed on the default branch with no feature branch — skip this checkout step. Do not treat the current checkout as authoritative product truth yet: a detached worktree parked at a bare SHA, or a stale default-branch checkout, can sit behind `origin/<default>`.

**Step 4: Bring the checkout current — sync before presenting**

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
Glob: "{full-spx-node-path}/PLAN.md"
Glob: "{full-spx-node-path}/ISSUES.md"
```

If found, list their paths. Do not read `PLAN.md` or `ISSUES.md` content in this step. `/contextualize` reads node-local coordination notes after product context and ancestry are loaded; acting on note content before then violates the spec-tree context guarantee.

**Step 5b: Present the session's first action**

After checkout synchronization and claim reconciliation, present the `next_step`
frontmatter value as the handoff's recommended first action. This comes before
loading node context or starting continuation work. Treat it as context, not as
a substitute for the required `/contextualize` step below; the resuming context
still chooses skills from loaded methodology and current repository state.

**Step 6: Present persisted artifacts**

Show the `<persisted>` section:

- What was committed (trust these are in place)
- What is uncommitted (may need `/commit-changes` before continuing)
- What durable insights were written to repository instructions, coordination notes, or skills
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
2. The first `<nodes>` entry whose "Coordination notes" list a `PLAN.md` or `ISSUES.md` path.
3. The first node listed in `<nodes>`.

Rule 3 always resolves a single node, so node multiplicity never triggers a user question — selection is deterministic. Ask the user which node to start with only when `<nodes>` is empty or unreadable. After loading the first target, contextualize additional nodes only when the next action touches them.

Invoke on the selected node:

```text
Skill tool → { "skill": "spec-tree:contextualize", "args": "{selected-full-spx-node-path}" }
```

After context is loaded, review session evidence before asking the operator anything. The operator must never decide from the session id, raw `next_step`, or unreviewed coordination notes.

Review these inputs:

- Target node and current state from `/contextualize`.
- Recommended next action from the handoff.
- Claim-verification verdicts from Step 5.
- Persisted artifacts from Step 6.
- Coordination section from Step 7.
- Note content loaded by `/contextualize` for any found `PLAN.md` or `ISSUES.md`; treat notes as stale-prone inputs and verify them against the loaded specs, decisions, assertions, tests, implementation, and current user intent before they steer work.
- Existing `doing` sessions from `spx session list --status doing --json`, comparing their `specs`, `files`, `goal`, and `next_step` with this session's target node and topic terms.
- Branch/worktree ownership from `git branch --list` and `git worktree list` when the session names a feature branch, branch-like `git_ref`, or a live-branch conflict.
- PR ownership from `gh pr list` or `gh pr view` when the session names a PR, branch, or merged/open PR state.

Classify the session:

- `actionable_here` — the loaded context and evidence support continuing in this conversation.
- `owned_elsewhere` — another active `doing` session, branch, worktree, open PR, merged PR, or committed live branch owns the same objective.
- `stale_or_superseded` — the session's recorded objective or paths no longer match current product truth, with no active owner to continue.
- `blocked_on_external_dependency` — continuation depends on state Claude cannot change now, such as a published CLI release, remote workflow result, or operator-held decision.
- `needs_operator_direction` — the evidence leaves a real product or ownership fork that the repository cannot decide.

When classification is `owned_elsewhere`, report the collision in plain English, name the owning session id, branch, worktree, PR, or commit when known, and STOP. Do not ask whether to archive, release, hand off, or continue. Leave the claimed session in `doing` and make no further session mutation.

For every other classification, present a post-context checkpoint with a no-surprises proposal:

```text
Pickup reviewed session `[claimed-session-id]`.

Goal: [session goal]
Loaded context: {selected-full-spx-node-path}
Classification: [classification]

Evidence:
- Claim verification: [Confirmed / Discrepancy / Unverifiable summary]
- Persisted artifacts: [summary]
- Coordination notes: [paths and current reading]
- Ownership check: [no overlap | owner details]

Work proposal:
- Expected outcome: [plain-English end state]
- Changed product surface: [plain-English product behavior, workflow, document, command, methodology, generated contract, skill contract, or other shipped surface likely to improve]
- Skill path: [planned skills and lifecycle gates]
- Evidence infrastructure: [tests / harnesses / generators / fixtures / evals / audit agents / review agents / generated artifacts / validation commands]
- Verification: [deterministic commands and agentic gates expected]
- Inspection references: [where the operator can inspect the result]
- Remaining work expectation: [none | coordination note | external blocker | existing owner]

Recommended next action: [specific action]
```

If `$ARGUMENTS` includes `--auto-continue`, acknowledge the override and resume with the recommended next action.

Otherwise, use `AskUserQuestion` with exactly one question and 2-3 mutually exclusive options. The options must come from the loaded context:

- Include the recommended next action as the first option, with the proposal's rationale.
- Include "Pause pickup flow" as an option so the operator can direct another workflow.
- Include another option only when the evidence review reveals a real alternative the repository cannot decide.
- Do not include "Review persisted artifacts first" or "Re-check coordination claims first" as options. Claude already performed that review before asking.

Wait for the user's selection before continuing. The checkpoint completes only after the `AskUserQuestion` response is received.

After the checkpoint completes, emit a canonical post-context marker using the claimed session id from `<PICKUP_CLAIM>` and carry the full claimed-session set from the most recent `<CLAIMED_SESSIONS ids="...">`:

```text
<PICKUP_CHECKPOINT id="[claimed-session-id]" claimed="[first-pickup],...,[claimed-session-id]" target="{selected-full-spx-node-path}" mode="[ask|auto-continue]">
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
- [ ] Session `next_step` presented only after `/sync-base` and claim reconciliation, and before node context or continuation work (Step 5b)
- [ ] When the session `git_ref` names a feature branch, that branch is fetched and checked out before node context is loaded (Step 3)
- [ ] In a bare-repository worktree pool, the assigned worktree's running claim is verified read-only before the work branch is switched into it, with a missing claim surfaced via `/diagnose` — `spx worktree claim` is not run during pickup, and no other pool worktree is entered or created (Step 3)
- [ ] Checkout brought current via `/sync-base` before any session detail is presented, for every `git_ref` kind (Step 4)
- [ ] Recorded claims reconciled by running `verify_session_claims.py`, and per-claim verdicts (`Confirmed` / `Discrepancy` / `Unverifiable`) presented in place of the recorded snapshot, before the checkpoint (Step 5)
- [ ] PLAN.md / ISSUES.md paths checked before context loading, with note content read by `/contextualize`
- [ ] Persisted artifacts acknowledged
- [ ] `/contextualize` invoked on target node — NOT offered as an option, just done
- [ ] When the session references multiple nodes, the `/contextualize` target is selected deterministically by the priority order (rule 3 always resolves), so node multiplicity never triggers a user question — the user is asked which node only when `<nodes>` is empty or unreadable
- [ ] Canonical post-context marker emitted as `<PICKUP_CHECKPOINT id="..." claimed="...">` with the full claimed-session set
- [ ] Claimed session remains in `doing` after the checkpoint — pickup workflow never archives or releases
- [ ] Post-context decision captured via `AskUserQuestion` response, or explicit `--auto-continue` override acknowledged
- [ ] No `/apply`, ADR, test, code, or file-editing work starts before the checkpoint or override
- [ ] Failures listed in coordination are verified against current state before triaging
- [ ] Claude has the session `next_step`, current claim verdicts, loaded node context, and coordination-note paths needed to choose the next skill from current methodology

</success_criteria>
