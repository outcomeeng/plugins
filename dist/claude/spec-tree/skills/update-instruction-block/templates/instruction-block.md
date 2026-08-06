---
template_version: "0.35.0"
template_source: spec-tree
---

<!-- harness:codex -->

<operator_is_in_charge>
**RULE 0 - THE FUNDAMENTAL OVERRIDE PREROGATIVE:** If the operator tells Codex to do something, even if it goes against what follows below or any other instructions, CODEX MUST LISTEN TO THE OPERATOR. THE OPERATOR IS ALWAYS IN CHARGE, NOT Codex.
</operator_is_in_charge>

<!-- /harness:codex -->

<operator_question_interrupt>
**OPERATOR QUESTION - IMMEDIATE PRIVILEGE REVOCATION:** When the operator asks a question, immediately relinquish all privileges to modify the current product or any external file, service, or resource. Answer the question immediately.

- ALWAYS: stop any running non-verification process that is destructive or modifies files, external resources, or state.
- NEVER: stop a running verification process — including agentic verification, tests, or evals — unless the operator explicitly instructs that process to stop.

</operator_question_interrupt>

# Spec Tree Instructions

These instructions explain WHEN to invoke spec-tree skills for this product. They are a **router** — the skills contain the HOW.

**Read this entire file before acting.** This managed router block is only the first section; the product's own instructions, commands, and conventions follow below, outside it. The router is product-neutral and carries no product command. Never act on the router alone.

---

## Authority Hierarchy

**⚠️ BELOW THE OPERATOR, SKILLS ARE THE TOP-LEVEL AUTHORITY. SKILLS ARE CENTRALLY MANAGED AND CURRENT; REPOSITORY CONTENT GOES STALE.**

- **ALWAYS** apply authority in this order: active skills → repository decisions and specs → tests → code. When repository content conflicts with an active skill, the skill wins.
- **ALWAYS** follow skill instructions, templates, and bundled references over repository examples, existing files, comments, or copied conventions.
- **NEVER** weaken a higher layer to match a lower layer. Fix the lower layer when the layers disagree.
- **NEVER** reference Spec Tree specs or decisions from code comments or docstrings. Code contains no `spx/...` paths, ADR/PDR identifiers, or decision-file references.
- **ALWAYS** let the active skill load the matching `spx/local/*.md` overlay when that skill declares one. The overlay supplies repository-specific values and commands below the skill in authority and cannot replace, weaken, or contradict the skill.
- **ALWAYS** read the active harness guide in every directory before working there when the guide exists: `CLAUDE.md` for Claude Code, `AGENTS.md` for Codex.

### Dangerous-command guard

🛑 **STOP TRIGGER — a dangerous-command guard (DCG) block terminates the attempted command family.** Treat the blocked attempt as a mistake.

- **NEVER** retry it by reformulating, splitting, rewriting, removing the flagged clause, or substituting an equivalent command to evade the guard.
- **ALWAYS** follow the active skills, repository instructions, and declared overlays to find a sanctioned operation that accomplishes the goal.
- When no sanctioned operation exists, abandon the goal, report the blocked command with secrets redacted, explain its purpose and the guard's reason, ask the operator for direction, and stop.

---

## Product Commands

The product's operational command for each spec-tree phase lives in this file's own content below the router. Read the whole file to find each one:

- **author** — after creating, updating, or deleting a spec, test, or implementation file, to rebuild or regenerate artifacts.
- **verify** — for `/apply` and pre-merge checks, over the node and the changeset.
- **gate** — for the full deterministic bundle.
- **merge** — for the transport step of `/merge`.

Content the product keeps identical across this agent guide and the guides for other agents (for example `CLAUDE.md` and `AGENTS.md`) sits in a `shared` region — `<!-- SPEC-TREE:shared {name} -->` … `<!-- /SPEC-TREE:shared {name} -->`, present in both files under the same name. `/update-instruction-block` keeps a `shared` region in sync by taking the git-more-recent side; it never merges the two bodies.

---

## When to Invoke Skills

### Before product-content access -> `/understand`

**BLOCKING REQUIREMENT**

Require a live `<SPEC_TREE_FOUNDATION>` marker before directly reading, searching, listing, or changing anything under `spx/` or any source or test file. Invoke `/understand` when the marker is absent. This includes repository-content access through Read, Edit, Write, Glob, Grep, `rg`, `grep`, `find`, `cat`, `sed`, and Git commands that emit file contents or patches.

`spx session` operations — including inspection, archive, and release — plus `spx worktree status`, `spx diagnose`, and no-patch Git status, history, and topology are exempt. Never follow paths from their output into repository content without the marker.

A compacted summary, session file, statement that `/understand` ran, or read of the skill file does not prove the foundation is live. After every compaction, invoke `/understand` again before the next product-content access.

### Before working on a specific node -> `/contextualize`

**BLOCKING REQUIREMENT**

**ALWAYS** invoke `/contextualize` before working on a spec node.

`/contextualize` MUST invoke `/sync-base` and receive `already_current` or `rebased` before reading product truth. `/sync-base` owns the complete currency operation: fetch, clean rebase or detached advance, session-authorized dirty-tree checkpointing through `/commit-changes`, and same-invocation retry. Callers consume its final result; they never duplicate branch creation, commit, stash, or retry logic, and they never reinterpret `dirty_tree` as a rebase conflict.

**🛑 STOP TRIGGER — after every compaction event:** all loaded spec-tree context is gone. **NEVER** resume work on a node without re-invoking `/contextualize` for that specific node since the last compaction.

### When creating specs or nodes -> `/author`

Create product decisions (ADRs/PDRs), specs, enabler nodes, outcome nodes.

### When composing or breaking down nodes -> `/decompose`

Compose top-level children with `/decompose spx/`. Decompose an existing node when it has too many assertions (>7), contains independent concerns, or has `PLAN.md`/`ISSUES.md` structure intent.

### When restructuring the tree -> `/refactor`

Move nodes, re-scope assertions, extract shared enablers, consolidate duplicates.

### When checking consistency -> `/align`

Review, audit, or quality check specs. Find contradictions or gaps.

### Before tests, evals, builds, or validation -> `/wait-for-load`

🛑 **STOP TRIGGER — Before any test, eval, build, or validation command, ALWAYS invoke `/wait-for-load`.**
**ALWAYS** wait for `ready: true`, then run the selected command unchanged.
**NEVER** use host load to reduce scope, workers, limits, deadlines, or verification.

<!-- harness:codex -->

**Codex execution boundary.** Invoke `/wait-for-load` in its own top-level `functions.exec` call. Inside that call, set a nested `exec_command` yield below the outer call's yield window so the nested call returns either terminal JSON or a `session_id` before the outer call can yield. When it returns a `session_id`, preserve that exact id and collect the same waiter with `write_stdin` in later top-level calls whose outer yield window exceeds the nested `write_stdin` yield. Treat readiness as established only when a top-level call visibly returns the terminal JSON with `ready: true`; an internal exit-code branch, a successfully completed outer cell, or an empty terminal payload is insufficient. Start the selected command in a separate top-level `functions.exec` call. **NEVER** place the waiter and selected command in the same `functions.exec` script or use `functions.wait` as the planned collector for a nested waiter or selected command.

**Codex process lifecycle.** Every nested `exec_command` that returns a `session_id` creates an owned process handle. Record it immediately, collect it with `write_stdin` until an `exit_code` is observed, and reconcile every known handle before another process sequence, an operator question, merge or publication, or turn end. If the work is abandoned, interrupt that process and collect its terminal result. Error output or sufficient-looking partial output never closes the handle and never permits leaving its background terminal dangling.

<!-- /harness:codex -->

### When shipping work to the default branch -> `/merge` (transport dispatcher)

**BLOCKING REQUIREMENT**

Every change destined for the default branch routes through `/merge`, the transport dispatcher — it classifies the changeset, selects the transport, and delegates. `spx/local/merging.md` is the one place repository-specific merge behavior belongs, and it is optional: when absent, `/merge` applies the default lifecycle rather than blocking. Never infer the transport from other docs, and never edit this generated instruction block to change merge behavior. The four authority gates, the delivered-value boundary, and the finding-disposition rule are transport-neutral and live in `/merging-standards`.

## Stop Triggers

Default-branch work is complete only when it reaches the default branch on origin through `/merge` — passing validation, tests, review, or audits is progress, not a stopping point, and an accepted proposal ("yes", "go", "do it") authorizes the whole lifecycle, not a pause. Each trigger below resolves the same way: finish the remaining independent work, then continue through `/commit-changes` and `/merge` until the change reaches the default branch on origin or an explicit lifecycle gate stops.

🛑 **About to summarize after edits, validation, tests, review, or audits passed** — do not conclude.

🛑 **About to report blocked, wait, or ask a question** — first do every action that does not need the answer: edits, verification, branch setup, commit, review. A blocker exists only when all three hold:

- the immediate next action cannot proceed without the operator or an external-state change;
- the local branch already holds every change makeable without the answer;
- the applicable gates have run or produced concrete failing evidence.

🛑 **About to finish on a detached HEAD or stop at a fresh commit** — `git status --short --branch` reporting `## HEAD (no branch)`, or a new local commit, is not an endpoint; create or switch to a local branch preserving the worktree changes, unless the user explicitly limited the task to local-only work.

## Checkpoint Commits

`/commit-changes` may create an atomic local checkpoint whenever a coherent concern is ready to preserve, independent of verification state — never strand dirty work because verification fails or has not run. Record the latest state as `passing`, `failing`, or `not-run`; that state controls later gate dispatch, never commit permission. Run hooks normally, confirm the full `HEAD` changed, and report committed paths, remaining paths, and verification state.

## Worktree Occupancy

Before treating any worktree as available, run `spx worktree status` and require a live claim for the exact absolute worktree root and current native session. Refresh this proof at session start, after restart or compaction, and immediately before any checkout or worktree transition. A clean tree, detached `HEAD`, branch name, pane title, or absent process in one view never proves availability. When the exact root is absent or claimed by another live session, remain in the assigned worktree and record the ownership issue instead of entering the sibling checkout.

## Git Safety Protocol

```text
ALLOW  git checkout -- README.md
ALLOW  git checkout HEAD -- .
ALLOW  git restore README.md

DENY   git stash drop
DENY   git stash drop stash@{3}
DENY   git stash pop
DENY   git stash pop stash@{0}
DENY   git stash clear
```

## Autonomy Boundary

Default-branch git and version-control mutation — branching, committing, pushing, publishing, merging, and the `/merge` flow's own cleanup of the branches it created — proceeds only inside a governing skill flow, never as a direct command outside one; creating or switching to a local branch to preserve work in progress, and a `--force-with-lease` push to the working branch that flow owns, stay inside it. This autonomy never extends to force-pushing a shared or protected ref, deleting a ref no active skill flow authorizes, bypassing commit hooks (`--no-verify`) or commit signing, or any action the Git Safety Protocol forbids; each needs explicit operator instruction in the same turn.

### Sub-agent dispatch

The configured verifier and reviewer roles this router names are pre-authorized. A harness rule may require the operator to request sub-agent use before one is dispatched; treat this section as that standing request. Authorization follows the named role, never a role resemblance.

- **NEVER** ask the operator to confirm dispatching one — not at a gate, not per node, not once per session, and never as a structured-question option set. A harness permission prompt is the operator's to answer, never a question to raise.
- **NEVER** dispatch a sub-agent this router does not name merely because it is discovered, available, or plausibly useful.
- **NEVER** run a verification skill — audit or review — in the main conversation; the separate context is what keeps the verdict free of that conversation's bias.
- **ALWAYS** treat the gate as blocked when a named role cannot be dispatched or does not return: finish the deterministic verification, then report the exact dispatch attempted and how it failed.

### Agent identity in generated artifacts

**NEVER** name the agent or its runtime in an operational artifact — a branch name, commit message, pull-request title or body, review comment, or authorship marker written into a product file. Describe the work, never who performed it. Exact filesystem paths, package and tool names, quoted command output, and operator-supplied text keep their required spelling.

**ALWAYS** confine that ban to operational artifacts. Instruction content that documents agent behavior names the agent as its subject by design; stripping that subject out of authored guidance to satisfy this rule misapplies it rather than complying with it.

### Operator questions

<!-- harness:claude -->

Raise an operator question through AskUserQuestion, never as prose the operator has to answer in free text. Reserve it for an answer that changes what happens next and that no loaded skill, decision, spec, or command output settles — a product-intent conflict a rebase cannot decide, a blocked expense ceiling, or a resolution the evidence leaves genuinely open. Name the exact blocked action, what each option does, and a pause-and-inspect choice.

<!-- /harness:claude -->

<!-- harness:codex -->

Raise an operator question through request_user_input, never as prose the operator has to answer in free text. Reserve it for an answer that changes what happens next and that no loaded skill, decision, spec, or command output settles — a product-intent conflict a rebase cannot decide, a blocked expense ceiling, or a resolution the evidence leaves genuinely open. Name the exact blocked action, what each option does, and a pause-and-inspect choice.

<!-- /harness:codex -->

- **ALWAYS** finish every action that does not depend on the answer first, so the question is the only thing outstanding when it is asked.
- **NEVER** raise one to confirm work already authorized, to report progress, or to choose an option the loaded truth already decides.

## Mutation Status Updates

Before proposing or performing a repository mutation, name:

- the exact target path, PR number, branch ref, or command target;
- the intended action;
- why the action is local enough or gate-authorized enough to proceed;
- the next validation command, review, audit, check wait, or merge gate the action feeds.

Avoid shorthand such as "config patch" or "ship it path" when the exact file, PR state, or command is known. A terse prompt such as "check", "continue", or "ship it" still gets the live state first: full head SHA when a PR exists, current-head review state, required-check state, deployment-readiness and release-readiness rules, and the next autonomous action.

## Quick Reference: Skills and Agents

Skills run in the main conversation. Agents preload the skill and run autonomously as subagents in a separate context. Audit agents return structured verdicts; changeset reviewer agents return the raw review journal token for the main conversation to inspect and process through the governing review workflow. Dispatch agents in parallel when auditing multiple targets; `### Sub-agent dispatch` above governs when to dispatch one.

<!-- harness:codex -->

**If a plugin's agents are missing, run that plugin's `/<plugin>-plugin init`.** For an agent whose plugin manifest cannot declare agents, a plugin's agent definitions reach a session only once they are materialized into the checkout's agent directory, and every plugin ships a lifecycle skill that places them. When dispatching an agent finds no such agent, invoke the owning plugin's `/<plugin>-plugin init` and retry — `/spec-tree-plugin init` for a spec-tree agent, `/instructions-plugin init` for an instructions agent. This is repair on the failure path, not a check to run at session start. The definitions it places are durable checkout configuration: commit them, so sessions that run no verb receive the same agents. That plugin's lifecycle skill governs their persistence, including the removals and renames an `upgrade` produces.

**Read named files yourself.** Always read explicitly named files in the main conversation. Never use subagents to read, summarize, inspect, or interpret skills or skill references, AGENTS.md instruction files, files named by the user, or files referenced by skills or instruction files.

**Dispatch each named role through the runtime's exposed typed-subagent spawn capability** (`multi_agent_v1.spawn_agent` when that identifier is available), spawning the matching subagents in parallel when several roles apply. `### Sub-agent dispatch` above governs when to dispatch, forbids asking the operator to confirm, and blocks the gate when a named role cannot be dispatched; this section governs only the Codex mechanics. Act only on the result the subagent returns.

**Already-dispatched verifier boundary.** Apply the typed-spawn rules above only in the main authoring conversation. Once running as a named verifier or reviewer, treat the current context as the required isolation and execute the configured audit or review skill directly. NEVER search for or spawn another verifier, use `tool_search` to discover multi-agent tools, or invoke `codex exec`, `claude`, `pi`, or another agent CLI. Missing nested-verifier tools is expected inside the dispatched verifier and does not block direct execution.

**STOP TRIGGER — in the main authoring conversation, discover deferred agent tools before reporting an agent unavailable.**

If a named agent or lifecycle tool is absent from the initial list, inspect the runtime's complete deferred-tool registry. Use top-level `functions.exec`; inside it, inspect `ALL_TOOLS`. Treat `exec_command` as the nested shell tool. Check typed `multi_agent_v1.spawn_agent` and its `Available roles`; an exact match proves availability. Report unavailable only when discovery finds no typed spawn capability or omits the exact role, and include that result. Visible catalogs, initial tools, generated rosters, and local `agents/*.md` files are not availability evidence.

**Use the exposed multi-agent tool schema exactly.** The examples below use the `multi_agent_v1` identifiers emitted by this Codex harness. When the runtime exposes different identifiers, discover the equivalent typed spawn, wait, send-input, and close capabilities and preserve the same fields and result contracts. The initial turn goes in `message`; use `items` only when the turn must pass structured mentions. Omit `fork_context`, `model`, `reasoning_effort`, and `service_tier` for the typed verifier and reviewer agents. Full-history forks are incompatible with changing `agent_type` in this harness, and the named verifier/reviewer roles already carry their own model settings. Store every returned agent id verbatim. The role task is the spawn's initial `message`, so one spawn and one wait complete a role. After spawning, continue only non-overlapping work while the subagent runs, then collect the result with the exposed wait capability and close the child immediately. Completed agents remain open until closed and can interfere with future spawns.

### Subagent lifecycle — preserve every handle and close every thread

Treat every spawned subagent as an owned resource. Maintain a registry in the main conversation containing its exact `agent_id`, role or task, and lifecycle state. Record a successful spawn's returned id before issuing another spawn or making any unrelated tool call. Preserve every unresolved registry entry across interruption and compaction.

**Acquire handles sequentially while agents execute concurrently.** Call `multi_agent_v1.spawn_agent` once per tool call. Several sequential spawn calls may occur within one main-agent tool-call sequence before control returns to the operator, and every agent already spawned may run concurrently while later calls are issued. NEVER place multiple spawn calls in `Promise.all`, another fail-fast combinator, or one parallel tool-call batch: one rejected call can suppress successful sibling results and lose their ids even though those agents remain open. Respect the runtime's configured `agents.max_threads` limit; NEVER hard-code a maximum such as eight and NEVER fill capacity with agents that are not required.

Before each spawn sequence, reconcile the registry: preserve any final results already returned, close their agents, and close work that has been abandoned or superseded. If a spawn fails, stop issuing new spawns, retain every id already acquired, and collect or close those known agents before retrying. A failed individual spawn yields no id for that call and does not erase ids returned by earlier calls.

**Collect, preserve, then close.** Use `multi_agent_v1.wait_agent` with only exact ids from the registry. A timeout with no final status is non-final. When the result remains required, wait again; when the work is explicitly abandoned or superseded, close the agent. For every final status, preserve the complete final message, structured verdict, or journal token first, then close the child and mark it closed in the registry. A notification, pending handle, or open id is never a final result.

Reconcile every registry entry at these checkpoints:

- immediately after a final result;
- before another spawn sequence;
- after any spawn failure;
- after interruption or compaction;
- before asking the operator a question;
- before entering a merge or publication phase; and
- before yielding control to the operator or ending the turn.

At a checkpoint, wait again for every still-required result and close every abandoned or superseded agent. Before merge, publication, or response end, every known id must be closed and every required result must already be preserved. Do not leave completed agents open; completed agents continue consuming thread capacity until closed.

NEVER invent, shorten, or substitute an agent id, including an all-zero placeholder. NEVER assume `multi_agent_v1.list_agents` exists; if the runtime exposes a listing tool, use it only to reconcile the registry. The interactive `/agent` picker is operator-side recovery when registry reconstruction is impossible, never a substitute for preserving ids. If `multi_agent_v1.close_agent` returns `not_found`, record that exact result and do not call `multi_agent_v1.resume_agent` merely to close the id. Resume only when intentionally continuing a known closed agent's work.

**Spawn each verifier or reviewer with its role task as the initial turn.** The `agent_type` binds the child to its configured agent definition, so the role task goes directly in the spawn's `message` and no separate turn precedes it:

```json
{
  "tool": "multi_agent_v1.spawn_agent",
  "arguments": {
    "agent_type": "<exact-agent-type>",
    "message": "<role-task>"
  }
}
```

Record the returned agent id verbatim, then collect the role-task result with `multi_agent_v1.wait_agent`. The role task passes only through its own output contract below; an error, timeout, missing final message, or output outside that contract blocks the gate. Record the full agent id and observed result, and close the child.

Wait once for one or more spawned agents. Use the 10-minute individual-file timeout for subagents such as `implementation-auditor` or `spec-auditor`:

```json
{
  "tool": "multi_agent_v1.wait_agent",
  "arguments": {
    "targets": ["<agent-id-from-spawn-agent>"],
    "timeout_ms": 600000
  }
}
```

Use the 30-minute changeset timeout only for `changes-reviewer` role work:

```json
{
  "tool": "multi_agent_v1.wait_agent",
  "arguments": {
    "targets": ["<agent-id-from-spawn-agent>"],
    "timeout_ms": 1800000
  }
}
```

Close a completed or no-longer-needed agent:

```json
{
  "tool": "multi_agent_v1.close_agent",
  "arguments": {
    "target": "<agent-id-from-spawn-agent>"
  }
}
```

In the main authoring conversation, if `multi_agent_v1.spawn_agent`, `multi_agent_v1.wait_agent`, or `multi_agent_v1.close_agent` is not initially exposed, discover it through the runtime's complete deferred-tool registry before concluding the capability or role is unavailable. Accept a subagent notification only when the harness delivers it while the main conversation is working or waiting; do not choose notifications as the planned result-collection mechanism. Do not use web search, time lookup, shell polling, or `request_user_input` or any other tools as a substitute for result collection.

**Result collection for verifier and reviewer agents.** The exposed typed wait capability (`multi_agent_v1.wait_agent` in the examples below) is the planned result-collection mechanism for the role task. Read its returned JSON, keyed by the spawned subagent id under `status`. A timeout returns an empty `status` object and is not a result. A final status for the target id is the turn result; when that final status carries a final message, that message is the turn output. Do not infer success from a subagent notification, a pending handle, or an open subagent id.

Successful `changes-reviewer` result shape:

```json
{
  "status": {
    "<agent-id-from-spawn-agent>": {
      "status": "completed",
      "message": "<raw-spx-review-journal-token>"
    }
  },
  "timed_out": false
}
```

Blocked or incomplete result shape:

```json
{
  "status": {},
  "timed_out": true
}
```

**Codex `changes-reviewer` output contract.** For `agent_type: "changes-reviewer"`, a successful final message is the raw `spx journal --type review` run token. Treat that token as the only review result. Inspect the review by reading or rendering the sealed journal prefix for that token. Do not ask the reviewer to summarize findings, do not accept a prose summary as the gate result, and do not run `spec-tree:review-changes` in the main thread to replace a missing token.

**Codex blocked-result rule.** If `wait_agent` returns an error, `not_found`, timeout with no final status, usage-limit failure, model-capacity failure, or any final message that is not a raw review journal token, the review gate is blocked. Record the exact agent id, tool result, and blocking reason. Do not publish, merge, or mark the gate passed. When repairing a finding or blocked subject, rerun deterministic verification, create a new local checkpoint commit, and review that new head; an operator-approved process exception is the only other path past the gate.

**Use raw scope only for the `changes-reviewer` role task.** The review agent owns `spec-tree:review-changes`, severity taxonomy, scope expansion, and finding shape. Pass only the raw scope token as the spawn `message`: `HEAD` for the current worktree scope, `origin/<base>...HEAD` for a specific committed range, a branch name, or a PR reference. A `HEAD` review satisfies a gate only when the caller first confirms the worktree is clean; on a dirty tree it includes staged, unstaged, and untracked sections and is advisory.

- ALWAYS prepare the worktree first: isolate the intended changes, sync to the base using the `spec-tree:sync-base` skill when the governing workflow requires it, pass deterministic verification, create a local checkpoint commit, and leave the worktree clean so the reviewer judges an exact committed head. A review over a working diff is advisory and never satisfies a gate.
- NEVER invoke the `spec-tree:review-changes` skill in the main authoring conversation; the `changes-reviewer` invokes it inside its isolated role workflow.
- NEVER pass a prose prompt, restate review instructions, add severity filters, or tell the reviewer to focus only on new changes, or what to emphasize.

```json
{
  "tool": "multi_agent_v1.spawn_agent",
  "arguments": {
    "agent_type": "changes-reviewer",
    "message": "HEAD"
  }
}
```

```json
{
  "tool": "multi_agent_v1.spawn_agent",
  "arguments": {
    "agent_type": "changes-reviewer",
    "message": "origin/<base>...HEAD"
  }
}
```

**Use explicit prompts for audit-agent role tasks.** The `message` field comes from the `multi_agent_v1.spawn_agent` schema. This instruction block owns the prompt content below for required verifier roles. Keep the prompt narrow: repository path, governed artifact paths, governing node or decision, deterministic verification state when relevant, audit task, and output shape. Do not ask the subagent to edit files.

Use this shape for an implementation audit:

```json
{
  "tool": "multi_agent_v1.spawn_agent",
  "arguments": {
    "agent_type": "implementation-auditor",
    "message": "Repository: <absolute-repository-path>\nScope: <base>..<head> committed changeset scope\nLive file list: none for a gating audit; full modified and untracked paths only for an advisory pre-commit audit\nGoverning node(s): <full spx/... path(s)>\nDeterministic verification already run: <commands and results>\nTask: Run the implementation audit through spx verification run. Return the run token and rendered projection; the complete blocked SPX diagnostic with run token or not-started, exact command, payload source, payload key, exit code, and stderr; or the complete pre-run skill-load diagnostic with run token not-started, required skill spec-tree:audit-implementation, and the exact load or availability failure."
  }
}
```

**Codex `implementation-auditor` output contract.** A successful final message carries the raw `spx verification run` token and rendered projection, without a competing prose verdict envelope. Treat the projection's `terminalStatus` as authoritative: `approved` passes the implementation-audit gate and `rejected` requires repair. A command-failure `BLOCKED` result leaves the gate blocked and must carry the run token or `not-started`, exact command, payload source, payload key, exit code, and stderr. A pre-run skill-load `BLOCKED` result also leaves the gate blocked and must carry run token `not-started`, required skill `spec-tree:audit-implementation`, and the exact load or availability failure. A missing token or projection, a terminal status outside that vocabulary, or an incomplete blocked diagnostic also leaves the gate blocked.

**Committed gate subject.** A gating implementation audit runs only after deterministic verification passes and the subject is committed locally. A run carrying a live modified or untracked file list is advisory and cannot satisfy an apply or merge gate.

**Full deterministic gate ordering.** When the repository declares a full deterministic bundle, run its declared command only after every applicable prior agentic gate has converged on the same clean committed head — including evidence audits, decision audits with any required language-architecture concerns, implementation audits, skill or subagent audits, and changeset review. Never launch it before agentic verification, from inside an agent, or concurrently with another heavy command. Any later change invalidates the full-gate result and requires the affected agentic checks to converge again before rerunning the full bundle.

Use this shape for test-evidence audits:

```json
{
  "tool": "multi_agent_v1.spawn_agent",
  "arguments": {
    "agent_type": "test-evidence-auditor",
    "message": "Repository: <absolute-repository-path>\nGoverning node: <full spx/... node path>\nSpec assertions: <full assertion text or exact spec file path plus assertion headings>\nTest files: <full paths to test files under the node>\nTask: Audit whether the test evidence proves the listed assertions without weakening the selected verification type or test assertion type. Return only the audit-tests JSON verdict, with schema_version 1, skill audit-tests, overall APPROVED or REJECTED, rows, and metadata. Do not add prose outside the JSON object."
  }
}
```

Use this shape for eval-evidence audits:

```json
{
  "tool": "multi_agent_v1.spawn_agent",
  "arguments": {
    "agent_type": "eval-evidence-auditor",
    "message": "Repository: <absolute-repository-path>\nGoverning node: <full spx/... node path>\nSpec assertions: <full [eval] assertion text or exact spec file path plus assertion headings>\nEval artifacts: <full paths to eval.toml, prompt.md, cases.jsonl, and history.jsonl>\nProducer artifacts: <full paths to the producing skill, agent, classifier, script, or command source>\nTask: Audit whether the eval evidence proves the listed assertions without replacing the real producer with a prompt-only simulation. Return the JSON verdict specified by audit-eval-evidence, with overall PASS, FAIL, or UNKNOWN and row findings for failed evidence properties. Do not add prose outside the JSON object."
  }
}
```

Use this shape for spec-node audits:

```json
{
  "tool": "multi_agent_v1.spawn_agent",
  "arguments": {
    "agent_type": "spec-auditor",
    "message": "Repository: <absolute-repository-path>\nNode: <full spx/... node path>\nTask: Audit the node spec for assertion quality, evidence tags, atemporal voice, decision alignment, and spec-tree structure. Return APPROVED or REJECTED. For REJECTED, list concrete findings with full spx/... paths, governing rule, and required fix."
  }
}
```

Use this shape for decision audits:

```json
{
  "tool": "multi_agent_v1.spawn_agent",
  "arguments": {
    "agent_type": "adr-auditor",
    "message": "Repository: <absolute-repository-path>\nDecision file: <full spx/.../*.adr.md path>\nGoverning node: <full spx/... node path>\nAudit scope: <exact committed changeset or artifact scope>\nScope classification: <language-neutral | implementation-language partitions: comma-separated languages>\nTask: Audit the ADR for decision structure, atemporal voice, tag validity, and every language-specific architecture concern required by the scope classification. Return only the structured JSON verdict specified by audit-adr, with no prose outside the JSON object."
  }
}
```

```json
{
  "tool": "multi_agent_v1.spawn_agent",
  "arguments": {
    "agent_type": "pdr-auditor",
    "message": "Repository: <absolute-repository-path>\nDecision file: <full spx/.../*.pdr.md path>\nGoverning node: <full spx/... node path>\nTask: Audit the PDR for product-decision structure, atemporal voice, tag validity, downstream alignment, and evidence quality. Return APPROVED or REJECTED. For REJECTED, list concrete findings with file paths, line numbers, governing rule, and required fix."
  }
}
```

Use this shape for skill audits:

```json
{
  "tool": "multi_agent_v1.spawn_agent",
  "arguments": {
    "agent_type": "skill-auditor",
    "message": "Repository: <absolute-repository-path>\nSkill content: <full paths to every changed artifact governing the skill surface, including SKILL.md files, skill subdirectory files, authored shared fragments, and generated runtime copies>\nGoverning node(s): <full spx/... path(s) when known>\nDeterministic verification already run: <commands and results, or why this audit is being run before verification>\nTask: Audit the changed skill content for skill-authoring standards, agent-prompt standards, progressive disclosure, portability, voice, and structure. Return only the structured JSON verdict specified by instructions:audit-skill, with no prose outside the JSON object."
  }
}
```

Use this shape for one subagent audit. When several custom-agent configurations changed, dispatch one `subagent-auditor` per file: acquire each handle sequentially, then let the role tasks run concurrently.

```json
{
  "tool": "multi_agent_v1.spawn_agent",
  "arguments": {
    "agent_type": "subagent-auditor",
    "message": "Repository: <absolute-repository-path>\nCustom agent file: <full path to one changed agent-directory file in the checkout>\nGoverning node(s): <full spx/... path(s) when known>\nDeterministic verification already run: <commands and results, or why this audit is being run before verification>\nTask: Audit the changed custom agent configuration for subagent-authoring standards, prompt voice, tool boundaries, model settings, skill preloads, and output contract. Return only the structured JSON verdict specified by instructions:audit-subagent, with no prose outside the JSON object."
  }
}
```

<!-- /harness:codex -->

<!-- harness:claude -->

**Use the `Agent` tool for every configured verifier or reviewer.** Launch in the foreground with `subagent_type` set to the exact configured agent type and `prompt` set to the role-task body from the shared contracts below. The completed `Agent` tool result is that configured agent's final message; apply the matching output contract to that message. An error, missing final message, or output outside the matching contract blocks the gate.

<!-- /harness:claude -->

**Inspect every successful `changes-reviewer` result through the sealed journal.** Invoke the `spec-tree:project-run-journal` skill and use its `render_review_run.py <run-token>` helper. The helper calls `spx journal render --type review --run <run-token>`, resolves a not-found current-scope miss through `spx journal list --type review --sealed sealed --limit 200`, re-renders with the listed branch slug when exactly one sealed run matches the token, reads the sealed event prefix, and prints the raw token, terminal status, full head/base identity, scope coverage, blocking/debt counts, and any findings through `render_surface(events)`. Treat this as journal inspection; the sealed prefix remains the only review result.

**Configured verifier and reviewer role-task contracts.** Supply only the fields named for the role:

- `changes-reviewer`: the raw scope token — `HEAD`, `origin/<base>...HEAD`, a branch, or a PR reference. Its final message MUST be the raw sealed review-journal run token.
- `implementation-auditor`: repository path, exact committed `<base>..<head>` scope, no live file list for a gating audit, governing node paths, deterministic verification commands and results, and the task to run the implementation audit through `spx verification run`. Its final message MUST carry the raw run token and rendered projection; only `terminalStatus: approved` passes.
- `test-evidence-auditor`: repository path, governing node, full assertion text or exact spec path plus headings, test-file paths, and the task to audit coupling, falsifiability, alignment, and coverage without weakening the evidence type. Its final message MUST be the `spec-tree:audit-tests` JSON verdict with `schema_version: 1`, `skill: "audit-tests"`, `overall: "APPROVED" | "REJECTED"`, `rows`, and `metadata`, with no prose outside the JSON object. Treat `overall` as authoritative. Malformed JSON, a missing required field, an unexpected `skill`, or an `overall` value outside that vocabulary blocks the gate.
- `eval-evidence-auditor`: repository path, governing node, `[eval]` assertions, all eval artifacts, producer artifacts, and the task to audit real-producer evidence. Its final message MUST be the audit-eval-evidence JSON verdict with overall `PASS`, `FAIL`, or `UNKNOWN` and no prose outside the JSON object.
- `spec-auditor`: repository path, full node path, and the task to audit assertion quality, evidence tags, atemporal voice, decision alignment, and structure. Its final message MUST be `APPROVED` or `REJECTED`; rejection lists concrete findings with full paths, governing rules, and required fixes.
- `adr-auditor` or `pdr-auditor`: repository path, full decision path, governing node, committed audit scope, and the role's decision-audit task; ADR tasks also carry the language-scope classification. The final message MUST follow that auditor's structured verdict contract without a competing prose envelope.
- `skill-auditor`, when that configured role is installed: repository path, full paths to every changed artifact governing the skill surface — including skill-directory files, authored shared fragments, and generated runtime copies — governing nodes when known, deterministic verification state, and the skill-authoring audit task. Its final message MUST be the `instructions:audit-skill` JSON verdict with `schema_version: 1`, `skill: "audit-skill"`, `overall: "APPROVED" | "REJECTED"`, and the `keep-these-aspects`, `worth-improving`, and `must-fix` rows. Treat `overall` as authoritative. Malformed JSON, a missing required field or row, an unexpected `skill`, or an `overall` value outside that vocabulary blocks the gate.

<!-- harness:claude -->

- `subagent-auditor`, when that configured role is installed: repository path, exactly one changed subagent configuration path in the active agent harness's native format, governing nodes when known, deterministic verification state, and the subagent-authoring audit task. Multiple changed configurations require separate `subagent-auditor` dispatches, one per path; acquire their handles sequentially and let their role tasks run concurrently. Each final message MUST be the `instructions:audit-subagent` JSON verdict with `schema_version: 1`, `skill: "audit-subagent"`, `overall: "APPROVED" | "REJECTED"`, and the `critical-issues`, `recommendations`, `strengths`, and `quick-fixes` rows. Treat `overall` as authoritative. Malformed JSON, a missing required field or row, an unexpected `skill`, or an `overall` value outside that vocabulary blocks the gate.

<!-- /harness:claude -->
<!-- harness:codex -->

- `subagent-auditor`, when that configured role is installed: repository path, exactly one changed custom agent configuration path in the active agent harness's native format, governing nodes when known, deterministic verification state, and the subagent-authoring audit task. Multiple changed configurations require separate `subagent-auditor` dispatches, one per path; acquire their handles sequentially and let their role tasks run concurrently. Each final message MUST be the `instructions:audit-subagent` JSON verdict with `schema_version: 1`, `skill: "audit-subagent"`, `overall: "APPROVED" | "REJECTED"`, and the `critical-issues`, `recommendations`, `strengths`, and `quick-fixes` rows. Treat `overall` as authoritative. Malformed JSON, a missing required field or row, an unexpected `skill`, or an `overall` value outside that vocabulary blocks the gate.

<!-- /harness:codex -->

| User Says...                                            | Skill                  | Agent                   |
| ------------------------------------------------------- | ---------------------- | ----------------------- |
| "Implement this outcome" or "Start the TDD flow"        | `/apply`               | —                       |
| "Create an outcome" or "Add an ADR"                     | `/author`              | —                       |
| "Add a new node" or "This node is too big"              | `/decompose`           | —                       |
| "Move this under that"                                  | `/refactor`            | —                       |
| "Check these specs"                                     | `/align`               | —                       |
| "Establish evidence for this" or "Write tests for this" | `/verify`              | —                       |
| "Audit this PDR"                                        | `/audit-pdr`           | `pdr-auditor`           |
| "Audit this ADR"                                        | `/audit-adr`           | `adr-auditor`           |
| "Audit test evidence"                                   | `/audit-tests`         | `test-evidence-auditor` |
| "Audit eval evidence"                                   | `/audit-eval-evidence` | `eval-evidence-auditor` |
| "Audit this spec node"                                  | `/audit-specs`         | `spec-auditor`          |
| "Diagnose the spx environment"                          | `/diagnose`            | —                       |
| "File a follow-up in a dependency queue"                | `/issue`               | —                       |

<!-- langs:present -->

Per-language code, architecture, and test audits ship as `audit-{lang}-{code|tests|architecture}` skills that generic artifact-type auditors compose for the language in scope. There is no per-language auditor agent. Dispatch `implementation-auditor` for implementation audits; it invokes the matching language concern skills automatically. Any per-language audit-skill table this instruction block carries covers only the languages recorded in its opening `<!-- SPEC-TREE v{version} langs:{list} -->` marker.

<!-- /langs:present -->
<!-- lang:python -->

| User Says...            | Skill (composed)             | Composing agent          |
| ----------------------- | ---------------------------- | ------------------------ |
| "Audit this code"       | `/audit-python-code`         | `implementation-auditor` |
| "Audit ADRs for Python" | `/audit-python-architecture` | `adr-auditor`            |
| "Audit these tests"     | `/audit-python-tests`        | `test-evidence-auditor`  |

<!-- /lang:python -->
<!-- lang:typescript -->

| User Says...                | Skill (composed)                 | Composing agent          |
| --------------------------- | -------------------------------- | ------------------------ |
| "Audit this code"           | `/audit-typescript-code`         | `implementation-auditor` |
| "Audit ADRs for TypeScript" | `/audit-typescript-architecture` | `adr-auditor`            |
| "Audit these tests"         | `/audit-typescript-tests`        | `test-evidence-auditor`  |

<!-- /lang:typescript -->
<!-- lang:rust -->

| User Says...          | Skill (composed)           | Composing agent          |
| --------------------- | -------------------------- | ------------------------ |
| "Audit this code"     | `/audit-rust-code`         | `implementation-auditor` |
| "Audit unsafe Rust"   | `/audit-rust-code`         | `implementation-auditor` |
| "Audit ADRs for Rust" | `/audit-rust-architecture` | `adr-auditor`            |
| "Audit these tests"   | `/audit-rust-tests`        | `test-evidence-auditor`  |

<!-- /lang:rust -->

<!-- langs:present -->

---

## Test Naming Convention

Test level is encoded in the filename. The `{evidence}` segment is chosen by `/test` routing from the assertion type: `scenario`, `mapping`, `conformance`, `property`, or `compliance`. Universal assertions use `mapping`, `conformance`, `property`, or `compliance`; a universal is never `scenario`. This instruction block renders only the languages recorded in its opening `<!-- SPEC-TREE v{version} langs:{list} -->` marker; `/update-instruction-block` re-renders from the installed template when the methodology advances.

<!-- /langs:present -->
<!-- lang:typescript -->

### TypeScript

| Level | Pattern                           | Example                        |
| ----- | --------------------------------- | ------------------------------ |
| 1     | `{subject}.{evidence}.l1.test.ts` | `parsing.scenario.l1.test.ts`  |
| 2     | `{subject}.{evidence}.l2.test.ts` | `cli.mapping.l2.test.ts`       |
| 3     | `{subject}.{evidence}.l3.test.ts` | `workflow.property.l3.test.ts` |

<!-- /lang:typescript -->
<!-- lang:rust -->

### Rust

| Level | Pattern                                    | Example                         |
| ----- | ------------------------------------------ | ------------------------------- |
| 1     | `{subject}.{evidence}.l1.rs`               | `parsing.scenario.l1.rs`        |
| 2     | `{subject}.{evidence}.l2.rs`               | `cli.mapping.l2.rs`             |
| 3     | `{subject}.{evidence}.l3.rs`               | `workflow.property.l3.rs`       |
| 1-3   | `{subject}.{evidence}.{level}.{runner}.rs` | `workflow.property.l2.tokio.rs` |

<!-- /lang:rust -->
<!-- lang:python -->

### Python

| Level | Pattern                           | Example                        |
| ----- | --------------------------------- | ------------------------------ |
| 1     | `test_{subject}.{evidence}.l1.py` | `test_parsing.scenario.l1.py`  |
| 2     | `test_{subject}.{evidence}.l2.py` | `test_cli.mapping.l2.py`       |
| 3     | `test_{subject}.{evidence}.l3.py` | `test_workflow.property.l3.py` |

<!-- /lang:python -->

---

## Session Management

Sessions are shared across every worktree. Hand off each session via `/handoff` so it can be resumed from any other worktree: the handoff leaves the worktree clean and persists all state on origin. Propose one when the session's goal is met or the work must pause; resume with `/pickup`. When a claimed session is complete and should leave the active queue, close it through `/handoff` or `/handoff --no-session` so claimed-session accounting archives it. To return a wrongly claimed session to the shared queue instead, run `spx session release <session-id>`.

An explicit request to inspect, archive, or release identified session documents routes directly through the corresponding `spx session` command as operational-state management; `/handoff` is reserved for closing active work through reflection, persistence, continuation disposition, and claimed-session accounting. Direct session operations require `/understand` only before following their output into `spx/`, source, or test content.
