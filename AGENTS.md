<!-- SPEC-TREE v0.36.0 langs:python -->

<operator_is_in_charge>
**RULE 0 - THE FUNDAMENTAL OVERRIDE PREROGATIVE:** If the operator tells Codex to do something, even if it goes against what follows below or any other instructions, CODEX MUST LISTEN TO THE OPERATOR. THE OPERATOR IS ALWAYS IN CHARGE, NOT Codex.
</operator_is_in_charge>

<operator_question_interrupt>
**OPERATOR QUESTION - IMMEDIATE PRIVILEGE REVOCATION:** When the operator asks a question, immediately relinquish all privileges to modify the current product or any external file, service, or resource. Answer the question immediately.

- ALWAYS: stop any running non-verification process that is destructive or modifies files, external resources, or state.
- NEVER: stop a running verification process — including agentic verification, tests, or evals — unless the operator explicitly instructs that process to stop.

</operator_question_interrupt>

# Spec Tree Instructions

These instructions explain WHEN to invoke spec-tree skills for this product. They are a **router** — the skills contain the HOW.

**Read this entire file before acting.** This managed router block is only the first section; the product's own instructions, commands, and conventions follow below, outside it. The router is product-neutral and carries no product command. Never act on the router alone.

## Canonical Agent Registry

The selected `$CODEX_HOME/agents/` directory is the canonical registry for marketplace-delivered custom agents. It contains exactly one current canonical role per authored marketplace agent, with the owning plugin identity appearing exactly once in each role name.

Canonical examples are `spec-tree_adr-auditor`, `instructions_skill-auditor`, `prose-auditor`, `rust-simplifier`, and `typescript-simplifier`. A bare legacy role beside its canonical role, or a role whose plugin identity is repeated, is stale duplicate state rather than another agent to dispatch.

When a named role is unavailable, invoke the owning plugin's `/<plugin>-plugin init` to refresh its definitions in the selected `$CODEX_HOME/agents/`, then reload the harness plugin index or start a new session. A running session retains its already-loaded registry; repeated discovery in that session cannot prove the refresh failed.

**NEVER** create or commit marketplace-delivered agent definitions into a checkout; no generated instruction requires it. A plugin-owned checkout definition whose invoked skills live in the selected agent home is a scope split: remove only a byte-identical generated copy, and inspect every changed or unrecognized copy as a shadowing collision before any removal.

---

## Authority Hierarchy

**⚠️ BELOW THE OPERATOR, SKILLS ARE THE TOP-LEVEL AUTHORITY. SKILLS ARE CENTRALLY MANAGED AND CURRENT; REPOSITORY CONTENT GOES STALE.**

- **ALWAYS** apply authority in this order: active skills → repository decisions and specs → verification evidence → code. When repository content conflicts with an active skill, the skill wins.
- **ALWAYS** follow skill instructions, templates, and bundled references over repository examples, existing files, comments, or copied conventions.
- **NEVER** weaken a higher layer to match a lower layer. Fix the lower layer when the layers disagree.
- **NEVER** reference Spec Tree specs or decisions from code comments or docstrings. Code contains no `spx/...` paths, ADR/PDR identifiers, or decision-file references.
- **ALWAYS** let the active skill load the matching `spx/local/*.md` overlay when that skill declares one. The overlay supplies repository-specific values and commands below the skill in authority and cannot replace, weaken, or contradict the skill.
- **ALWAYS** read the active harness guide in every directory before working there when the guide exists: `CLAUDE.md` for Claude Code, `AGENTS.md` for Codex.

### Dangerous-command guard

🛑 **STOP TRIGGER — a dangerous-command guard (DCG) block terminates the attempted command family.** Treat the blocked attempt as a mistake.

- **NEVER** retry it by reformulating, splitting, rewriting, removing the flagged clause, or substituting an equivalent command to evade the guard.
- **NEVER** pass dynamic branch names to `git branch -d` or `git branch -D`: variables, command substitutions, arrays, and globs are denied, including when quoted or placed after `--`. Type every branch name literally; delete several literal names in one command.
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

Require a live `<SPEC_TREE_FOUNDATION>` marker before directly reading, searching, listing, or changing anything under `spx/` or any other product content — source or test files, generated output, evals, and spec-declared configuration. Invoke `/understand` when the marker is absent. This includes repository-content access through Read, Edit, Write, Glob, Grep, `rg`, `grep`, `find`, `cat`, `sed`, and Git commands that emit file contents or patches.

`spx session` operations — including inspection, archive, and release — plus `spx worktree status`, `spx diagnose`, no-patch Git status, history, and topology, and a skill's read of the `spx/local/` overlay or exclusion mechanism it declares are exempt. Never follow paths from their output into repository content without the marker.

A compacted summary, session file, statement that `/understand` ran, or read of the skill file does not prove the foundation is live. After every compaction, invoke `/understand` again before the next product-content access.

### Before working on a specific node -> `/contextualize`

**BLOCKING REQUIREMENT**

**ALWAYS** invoke `/contextualize` on a spec node before discussing it and before reading or modifying any product content it governs.

`/contextualize` MUST invoke `/sync-base` and receive `already_current` or `rebased` before reading product truth. `/sync-base` owns the complete currency operation: fetch, clean rebase or detached advance, session-authorized dirty-tree checkpointing through `/commit-changes`, and same-invocation retry. Callers consume its final result; they never duplicate branch creation, commit, stash, or retry logic, and they never reinterpret `dirty_tree` as a rebase conflict.

**🛑 STOP TRIGGER — after every compaction event:** the set of contextualized nodes is empty. **NEVER** read or modify product content whose governing spec node has not been contextualized since that compaction, and **NEVER** discuss a node before contextualizing it. Product content is every product artifact a spec node governs or must govern: source, tests, evals, generated output, specs, decisions, coordination notes, and spec-declared configuration. Operational configuration — the `spx/local/` overlays and the exclusion mechanism, read by the skill that declares them without the marker — and the agent harness's own instruction and settings files it is told to read, tool and command output, the session store, and scratch space are not product content. Product content's governing node is found by search under the live foundation marker: a path under `spx/<node>/` belongs to that node; any other path belongs to the node whose `spx/**/tests/` file names it and whose spec links that test, or whose spec or decision names that path in an `[audit]` assertion; several matching nodes resolve to their lowest common ancestor. Product content with no governing spec is not read or modified; record the gap. An operational continuation — PR inspection, check wait, merge, deploy, release, `spx session` operations, occupancy proof — touches no product content and triggers neither `/understand` nor `/contextualize`.

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

**Codex execution boundary.** Invoke `/wait-for-load` in its own top-level `functions.exec` call. Inside that call, set a nested `exec_command` yield below the outer call's yield window so the nested call returns either terminal JSON or a `session_id` before the outer call can yield. When it returns a `session_id`, preserve that exact id and collect the same waiter with `write_stdin` in later top-level calls whose outer yield window exceeds the nested `write_stdin` yield. Treat readiness as established only when a top-level call visibly returns the terminal JSON with `ready: true`; an internal exit-code branch, a successfully completed outer cell, or an empty terminal payload is insufficient. Start the selected command in a separate top-level `functions.exec` call. **NEVER** place the waiter and selected command in the same `functions.exec` script or use `functions.wait` as the planned collector for a nested waiter or selected command.

**Codex process lifecycle.** Every nested `exec_command` that returns a `session_id` creates an owned process handle. Record it immediately, collect it with `write_stdin` until an `exit_code` is observed, and reconcile every known handle before another process sequence, an operator question, merge or publication, or turn end. If the work is abandoned, interrupt that process and collect its terminal result. Error output or sufficient-looking partial output never closes the handle and never permits leaving its background terminal dangling.

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

## Commit Before Another Session Reads

Changes may remain uncommitted while the authoring agent session works on them. When repository writes are authorized, commit the exact current version through `/commit-changes` before another agent session or human reads it for collaboration or reusable verification; the commit may record `passing`, `failing`, or `not-run`. After any further change, commit the new version before another such reading. An explicit advisory audit or review may inspect modified or untracked work, but its verdict is not reusable gate evidence. Without repository-write authorization, defer a reading that requires a committed subject. Agentic gate dispatch additionally requires its declared deterministic verification to pass on the exact committed subject.

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

Default-branch git and version-control mutation — branching, committing, pushing, publishing, merging, and the `/merge` flow's own cleanup of the branches it created — proceeds only inside a governing skill flow, never as a direct command outside one; creating or switching to a local branch to preserve work in progress, and a `--force-with-lease` push to the working branch that flow owns, stay inside it. The `/merge` direct-push transport's publication of a coordination-note-only changeset to the default branch on origin, performed under a held `MERGE_READINESS` with a converged local review, is likewise inside its governing flow. This autonomy never extends to force-pushing a shared or protected ref, deleting a ref no active skill flow authorizes, bypassing commit hooks (`--no-verify`) or commit signing, or any action the Git Safety Protocol forbids; each needs explicit operator instruction in the same turn.

### Sub-agent dispatch

The configured verifier and reviewer roles this router names are pre-authorized. A harness rule may require the operator to request sub-agent use before one is dispatched; treat this section as that standing request. Authorization follows the named role, never a role resemblance.

- **NEVER** ask the operator to confirm dispatching one — not at a gate, not per node, not once per session, and never as a structured-question option set. A harness permission prompt is the operator's to answer, never a question to raise.
- **NEVER** dispatch a sub-agent this router does not name merely because it is discovered, available, or plausibly useful.
- **NEVER** run a verification skill — audit or review — in the main conversation; the separate verifier agent session keeps the verdict free of the authoring agent session's bias.
- **ALWAYS** treat the gate as blocked when a named role cannot be dispatched or does not return: finish the deterministic verification, then report the exact dispatch attempted and how it failed.

### Agent identity in generated artifacts

**NEVER** name the agent or its runtime in an operational artifact — a branch name, commit message, pull-request title or body, review comment, or authorship marker written into a product file. Describe the work, never who performed it. Exact filesystem paths, package and tool names, quoted command output, and operator-supplied text keep their required spelling.

**ALWAYS** confine that ban to operational artifacts. Authored guidance that documents Claude's behavior uses imperative voice or names Claude as its subject by design; stripping Claude from that guidance to satisfy this rule misapplies it rather than complying with it.

### Operator questions

Raise an operator question through request_user_input, never as prose the operator has to answer in free text. Reserve it for an answer that changes what happens next and that no loaded skill, decision, spec, or command output settles — a product-intent conflict a rebase cannot decide, a blocked expense ceiling, or a resolution the evidence leaves genuinely open. Name the exact blocked action, what each option does, and a pause-and-inspect choice.

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

Skills run in the main conversation. Agents preload the skill and run autonomously in their own agent sessions. Audit agents return structured verdicts; changeset reviewer agents return the raw review journal token for the main conversation to inspect and process through the governing review workflow. Dispatch agents in parallel when auditing multiple targets; `### Sub-agent dispatch` above governs when to dispatch one.

**Read each file fully in its designated context.** A file the user names is read in the main conversation. A file this conversation authored is verified by a configured verifier or reviewer in an independent context. Subagents may locate files; a file the main conversation needs is then read in the main conversation in full.

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

Wait once for one or more spawned agents. Use the 10-minute individual-file timeout for subagents such as `spec-tree_implementation-auditor` or `spec-tree_spec-auditor`:

```json
{
  "tool": "multi_agent_v1.wait_agent",
  "arguments": {
    "targets": ["<agent-id-from-spawn-agent>"],
    "timeout_ms": 600000
  }
}
```

Use the 30-minute changeset timeout only for `spec-tree_changes-reviewer` role work:

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

Successful `spec-tree_changes-reviewer` result shape:

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

**Codex `spec-tree_changes-reviewer` output contract.** For `agent_type: "spec-tree_changes-reviewer"`, a successful final message is the raw `spx journal --type review` run token. Treat that token as the only review result. Inspect the review by reading or rendering the sealed journal prefix for that token. Do not ask the reviewer to summarize findings, do not accept a prose summary as the gate result, and do not run `spec-tree:review-changes` in the main thread to replace a missing token.

**Codex blocked-result rule.** If `wait_agent` returns an error, `not_found`, timeout with no final status, usage-limit failure, model-capacity failure, or any final message that is not a raw review journal token, the review gate is blocked. Record the exact agent id, tool result, and blocking reason. Do not publish, merge, or mark the gate passed. When repairing a finding or blocked subject, rerun deterministic verification, create a new local checkpoint commit, and review that new head; an operator-approved process exception is the only other path past the gate.

**Use raw scope only for the `spec-tree_changes-reviewer` role task.** The review agent owns `spec-tree:review-changes`, severity taxonomy, scope expansion, and finding shape. Pass only the raw scope token as the spawn `message`: `HEAD` for the current committed branch scope, `origin/<base>...HEAD` for a specific committed range, a branch name, or a PR reference. Confirm the worktree is clean before dispatch; commit the exact current version before the reviewer agent session reads it.

- ALWAYS prepare the worktree first: isolate the intended changes, sync to the base using the `spec-tree:sync-base` skill when the governing workflow requires it, pass deterministic verification, create a local checkpoint commit, and leave the worktree clean so the reviewer judges an exact committed head. Never dispatch the reviewer over a working diff.
- NEVER invoke the `spec-tree:review-changes` skill in the main authoring conversation; the `spec-tree_changes-reviewer` invokes it inside its isolated role workflow.
- NEVER pass a prose prompt, restate review instructions, add severity filters, or tell the reviewer to focus only on new changes, or what to emphasize.

```json
{
  "tool": "multi_agent_v1.spawn_agent",
  "arguments": {
    "agent_type": "spec-tree_changes-reviewer",
    "message": "HEAD"
  }
}
```

```json
{
  "tool": "multi_agent_v1.spawn_agent",
  "arguments": {
    "agent_type": "spec-tree_changes-reviewer",
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
    "agent_type": "spec-tree_implementation-auditor",
    "message": "Repository: <absolute-repository-path>\nScope: <base>..<head> committed changeset scope\nLive file list: <none for reusable gate evidence | full modified and untracked paths for explicit advisory audit>\nGoverning node(s): <full spx/... path(s)>\nDeterministic verification already run: <commands and results, or advisory state>\nRun driver identity: {\"producerKind\":\"agent\",\"agentName\":\"implementation-auditor\",\"agentOwningPluginName\":\"spec-tree\",\"skillName\":\"audit-implementation\",\"skillOwningPluginName\":\"spec-tree\",\"invocationRole\":\"run-driver\"}\nTask: Run the implementation audit through spx verification run. Return the run token and rendered projection; the complete blocked SPX diagnostic with run token or not-started, exact command, payload source, payload key, exit code, and stderr; or the complete pre-run skill-load diagnostic with run token not-started, required skill spec-tree:audit-implementation, and the exact load or availability failure."
  }
}
```

**Codex `spec-tree_implementation-auditor` output contract.** A successful final message carries the raw `spx verification run` token and rendered projection, without a competing prose verdict envelope. Treat the projection's `terminalStatus` as authoritative: `approved` passes the implementation-audit gate and `rejected` requires repair. A command-failure `BLOCKED` result leaves the gate blocked and must carry the run token or `not-started`, exact command, payload source, payload key, exit code, and stderr. A pre-run skill-load `BLOCKED` result also leaves the gate blocked and must carry run token `not-started`, required skill `spec-tree:audit-implementation`, and the exact load or availability failure. A missing token or projection, a terminal status outside that vocabulary, or an incomplete blocked diagnostic also leaves the gate blocked.

**Implementation audit subject.** A gate-eligible implementation audit reads an exact locally committed subject, carries `Live file list: none`, and runs only after applicable deterministic verification passes on that subject. An explicit advisory implementation audit may carry the full modified and untracked path list; its result supplies no reusable gate evidence.

**Full deterministic gate ordering.** When the repository declares a full deterministic bundle, run its declared command only after every applicable prior agentic gate has converged on the same clean committed head — including evidence audits, decision audits with any required language-architecture concerns, implementation audits, skill or subagent audits, and changeset review. Never launch it before agentic verification, from inside an agent, or concurrently with another heavy command. Any later change invalidates the full-gate result and requires the affected agentic checks to converge again before rerunning the full bundle.

Use this shape for test-evidence audits:

```json
{
  "tool": "multi_agent_v1.spawn_agent",
  "arguments": {
    "agent_type": "spec-tree_test-evidence-auditor",
    "message": "Repository: <absolute-repository-path>\nGoverning node: <full spx/... node path>\nSpec assertions: <full assertion text or exact spec file path plus assertion headings>\nTest files: <full paths to test files under the node>\nTask: Audit whether the test evidence proves the listed assertions without weakening the selected verification type or test assertion type. Return only the audit-tests JSON verdict, with schema_version 1, skill audit-tests, overall APPROVED or REJECTED, rows, and metadata. Do not add prose outside the JSON object."
  }
}
```

Use this shape for eval-evidence audits:

```json
{
  "tool": "multi_agent_v1.spawn_agent",
  "arguments": {
    "agent_type": "spec-tree_eval-evidence-auditor",
    "message": "Repository: <absolute-repository-path>\nGoverning node: <full spx/... node path>\nSpec assertions: <full [eval] assertion text or exact spec file path plus assertion headings>\nEval artifacts: <full paths to eval.toml, prompt.md, cases.jsonl, and history.jsonl>\nProducer artifacts: <full paths to the producing skill, agent, classifier, script, or command source>\nTask: Audit whether the eval evidence proves the listed assertions without replacing the real producer with a prompt-only simulation. Return the JSON verdict specified by audit-eval-evidence, with overall PASS, FAIL, or UNKNOWN and row findings for failed evidence properties. Do not add prose outside the JSON object."
  }
}
```

Use this shape for spec-node audits:

```json
{
  "tool": "multi_agent_v1.spawn_agent",
  "arguments": {
    "agent_type": "spec-tree_spec-auditor",
    "message": "Repository: <absolute-repository-path>\nNode: <full spx/... node path>\nTask: Audit the node spec for assertion quality, evidence tags, atemporal voice, decision alignment, and spec-tree structure. Return only the audit-specs JSON verdict, with schema_version 1, skill audit-specs, overall APPROVED or REJECTED, the section-structure, atemporal-voice, and tag-fitness rows, and metadata. Do not add prose outside the JSON object."
  }
}
```

Use this shape for decision audits:

```json
{
  "tool": "multi_agent_v1.spawn_agent",
  "arguments": {
    "agent_type": "spec-tree_adr-auditor",
    "message": "Repository: <absolute-repository-path>\nDecision file: <full spx/.../*.adr.md path>\nGoverning node: <full spx/... node path>\nAudit scope: <exact committed changeset or artifact scope>\nScope classification: <language-neutral | implementation-language partitions: comma-separated languages>\nTask: Audit the ADR for decision structure, atemporal voice, tag validity, and every language-specific architecture concern required by the scope classification. Return only the structured JSON verdict specified by audit-adr, with no prose outside the JSON object."
  }
}
```

```json
{
  "tool": "multi_agent_v1.spawn_agent",
  "arguments": {
    "agent_type": "spec-tree_pdr-auditor",
    "message": "Repository: <absolute-repository-path>\nDecision file: <full spx/.../*.pdr.md path>\nGoverning node: <full spx/... node path>\nTask: Audit the PDR for product-decision structure, atemporal voice, tag validity, downstream alignment, and evidence quality. Return only the audit-pdr JSON verdict, with schema_version 1, skill audit-pdr, overall APPROVED or REJECTED, the content-classification, property-quality, tag-validity, atemporal-voice, and consistency rows, and metadata. Do not add prose outside the JSON object."
  }
}
```

Use this shape for skill audits:

```json
{
  "tool": "multi_agent_v1.spawn_agent",
  "arguments": {
    "agent_type": "instructions_skill-auditor",
    "message": "Repository: <absolute-repository-path>\nSkill content: <full paths to every changed artifact governing the skill surface, including SKILL.md files, skill subdirectory files, authored shared fragments, and generated runtime copies>\nGoverning node(s): <full spx/... path(s) when known>\nDeterministic verification already run: <commands and results, or why this audit is being run before verification>\nTask: Audit the changed skill content for skill-authoring standards, agent-prompt standards, progressive disclosure, portability, voice, and structure; also audit the complete plugin skill-name set when the active repository skill-authoring overlay requires a plugin-wide naming audit. Return only the structured JSON verdict specified by instructions:audit-skill, with no prose outside the JSON object."
  }
}
```

Use this shape for one subagent audit. When several custom-agent configurations changed, dispatch one `instructions_subagent-auditor` per file: acquire each handle sequentially, then let the role tasks run concurrently.

```json
{
  "tool": "multi_agent_v1.spawn_agent",
  "arguments": {
    "agent_type": "instructions_subagent-auditor",
    "message": "Repository: <absolute-repository-path>\nCustom agent file: <full path to one changed agent-directory file in the checkout>\nGoverning node(s): <full spx/... path(s) when known>\nDeterministic verification already run: <commands and results, or why this audit is being run before verification>\nTask: Audit the changed custom agent configuration for subagent-authoring standards, prompt voice, tool boundaries, model settings, skill preloads, and output contract. Return only the structured JSON verdict specified by instructions:audit-subagent, with no prose outside the JSON object."
  }
}
```

**Inspect every successful `spec-tree_changes-reviewer` result through the sealed journal.** Invoke the `spec-tree:project-run-journal` skill and use its `render_review_run.py <run-token>` helper. The helper calls `spx journal render --type review --run <run-token>`, resolves a not-found current-scope miss through `spx journal list --type review --sealed sealed --limit 200`, re-renders with the listed branch slug when exactly one sealed run matches the token, reads the sealed event prefix, and prints the raw token, terminal status, full head/base identity, scope coverage, blocking/debt counts, and any findings through `render_surface(events)`. Treat this as journal inspection; the sealed prefix remains the only review result.

**Configured verifier and reviewer role-task contracts.** Supply only the fields named for the role:

- `spec-tree_changes-reviewer`: the raw scope token — `HEAD`, `origin/<base>...HEAD`, a branch, or a PR reference. Its final message MUST be the raw sealed review-journal run token.
- `spec-tree_implementation-auditor`: repository path, exact committed `<base>..<head>` scope, no live file list for a gating audit, governing node paths, deterministic verification commands and results, the `spec-tree_implementation-auditor` role's six-field run-driver identity, and the task to run the implementation audit through `spx verification run`. Its final message MUST carry the raw run token and rendered projection; only `terminalStatus: approved` passes.
- `spec-tree_test-evidence-auditor`: repository path, governing node, full assertion text or exact spec path plus headings, test-file paths, and the task to audit coupling, falsifiability, alignment, and coverage without weakening the evidence type. Its final message MUST be the `spec-tree:audit-tests` JSON verdict with `schema_version: 1`, `skill: "audit-tests"`, `overall: "APPROVED" | "REJECTED"`, `rows`, and `metadata`, with no prose outside the JSON object. Treat `overall` as authoritative. Malformed JSON, a missing required field, an unexpected `skill`, or an `overall` value outside that vocabulary blocks the gate.
- `spec-tree_eval-evidence-auditor`: repository path, governing node, `[eval]` assertions, all eval artifacts, producer artifacts, and the task to audit real-producer evidence. Its final message MUST be the audit-eval-evidence JSON verdict with overall `PASS`, `FAIL`, or `UNKNOWN` and no prose outside the JSON object.
- `spec-tree_spec-auditor`: repository path, full node path, and the task to audit assertion quality, evidence tags, atemporal voice, decision alignment, and structure. Its final message MUST be the `spec-tree:audit-specs` JSON verdict with `schema_version: 1`, `skill: "audit-specs"`, `overall: "APPROVED" | "REJECTED"`, the `section-structure`, `atemporal-voice`, and `tag-fitness` rows, and `metadata`, with no prose outside the JSON object. Treat `overall` as authoritative. Malformed JSON, a missing required field or row, an unexpected `skill`, or an `overall` value outside that vocabulary blocks the gate.
- `spec-tree_adr-auditor` or `spec-tree_pdr-auditor`: repository path, full decision path, governing node, committed audit scope, and the role's decision-audit task; ADR tasks also carry the language-scope classification. The final message MUST follow that auditor's structured verdict contract without a competing prose envelope.
- `instructions_skill-auditor`, when that configured role is installed: repository path, full paths to every changed artifact governing the skill surface — including skill-directory files, authored shared fragments, and generated runtime copies — governing nodes when known, deterministic verification state, and the skill-authoring audit task. Its final message MUST be the `instructions:audit-skill` JSON verdict with `schema_version: 1`, `skill: "audit-skill"`, `overall: "APPROVED" | "REJECTED"`, and the `keep-these-aspects`, `worth-improving`, and `must-fix` rows. Treat `overall` as authoritative. Malformed JSON, a missing required field or row, an unexpected `skill`, or an `overall` value outside that vocabulary blocks the gate.
- A craft plugin's `{plugin}-auditor` — the artifact-type auditor named for the plugin that governs its artifact type, such as a prose plugin's `prose-auditor` — when that configured role is installed: the artifact content or full paths under audit, every classification the owning plugin's audit skill requires as an input, and the audit task that skill declares — consult that skill for its exact required-field list and for its declared output contract, which is one of two shapes. When it declares a structured verdict, the final message MUST be that verdict with no prose outside it; treat `overall` as authoritative, and a malformed verdict, a missing required field, a verdict that does not identify itself as the owning plugin's audit skill, or an `overall` value outside the declared vocabulary blocks the gate. When it declares a sealed-run journal token, the final message MUST be that raw token with no prose outside it; render the sealed run through `spx journal render --type <the skill's declared run type> --run <run-token>` and treat the run's terminal status as authoritative, with only `approved` passing, and a blocked, unsealed, or unrenderable run blocking the gate. A final message that is neither the declared verdict nor the declared token blocks the gate.

- `instructions_subagent-auditor`, when that configured role is installed: repository path, exactly one changed custom agent configuration path in the active agent harness's native format, governing nodes when known, deterministic verification state, and the subagent-authoring audit task. Multiple changed configurations require separate `instructions_subagent-auditor` dispatches, one per path; acquire their handles sequentially and let the role tasks run concurrently. Each final message MUST be the `instructions:audit-subagent` JSON verdict with `schema_version: 1`, `skill: "audit-subagent"`, `overall: "APPROVED" | "REJECTED"`, and the `critical-issues`, `recommendations`, `strengths`, and `quick-fixes` rows. Treat `overall` as authoritative. Malformed JSON, a missing required field or row, an unexpected `skill`, or an `overall` value outside that vocabulary blocks the gate.

| User Says...                                            | Skill                  | Agent                             |
| ------------------------------------------------------- | ---------------------- | --------------------------------- |
| "Implement this outcome" or "Start the TDD flow"        | `/apply`               | —                                 |
| "Create an outcome" or "Add an ADR"                     | `/author`              | —                                 |
| "Add a new node" or "This node is too big"              | `/decompose`           | —                                 |
| "Move this under that"                                  | `/refactor`            | —                                 |
| "Check these specs"                                     | `/align`               | —                                 |
| "Establish evidence for this" or "Write tests for this" | `/verify`              | —                                 |
| "Audit this PDR"                                        | `/audit-pdr`           | `spec-tree_pdr-auditor`           |
| "Audit this ADR"                                        | `/audit-adr`           | `spec-tree_adr-auditor`           |
| "Audit test evidence"                                   | `/audit-tests`         | `spec-tree_test-evidence-auditor` |
| "Audit eval evidence"                                   | `/audit-eval-evidence` | `spec-tree_eval-evidence-auditor` |
| "Audit this spec node"                                  | `/audit-specs`         | `spec-tree_spec-auditor`          |
| "Diagnose the spx environment"                          | `/diagnose`            | —                                 |
| "File a follow-up in a dependency queue"                | `/issue`               | —                                 |

Per-language code, architecture, and test audits ship as `audit-{lang}-{code|tests|architecture}` skills that generic artifact-type auditors compose for the language in scope. There is no per-language auditor agent. Dispatch `spec-tree_implementation-auditor` for implementation audits; it invokes the matching language concern skills automatically. Any per-language audit-skill table this instruction block carries covers only the languages recorded in its opening `<!-- SPEC-TREE v{version} langs:{list} -->` marker.

| User Says...            | Skill (composed)             | Composing agent                    |
| ----------------------- | ---------------------------- | ---------------------------------- |
| "Audit this code"       | `/audit-python-code`         | `spec-tree_implementation-auditor` |
| "Audit ADRs for Python" | `/audit-python-architecture` | `spec-tree_adr-auditor`            |
| "Audit these tests"     | `/audit-python-tests`        | `spec-tree_test-evidence-auditor`  |

---

## Test Naming Convention

Test level is encoded in the filename. The `{evidence}` segment is chosen by `/test` routing from the assertion type: `scenario`, `mapping`, `conformance`, `property`, or `compliance`. Universal assertions use `mapping`, `conformance`, `property`, or `compliance`; a universal is never `scenario`. This instruction block renders only the languages recorded in its opening `<!-- SPEC-TREE v{version} langs:{list} -->` marker; `/update-instruction-block` re-renders from the installed template when the methodology advances.

### Python

| Level | Pattern                           | Example                        |
| ----- | --------------------------------- | ------------------------------ |
| 1     | `test_{subject}.{evidence}.l1.py` | `test_parsing.scenario.l1.py`  |
| 2     | `test_{subject}.{evidence}.l2.py` | `test_cli.mapping.l2.py`       |
| 3     | `test_{subject}.{evidence}.l3.py` | `test_workflow.property.l3.py` |

---

## Session Management

Sessions are shared across every worktree. Hand off each session via `/handoff` so it can be resumed from any other worktree: the handoff leaves the worktree clean and persists all state on origin. Propose one when the session's goal is met or the work must pause; resume with `/pickup`. When a claimed session is complete and should leave the active queue, close it through `/handoff` or `/handoff --no-session` so claimed-session accounting archives it. To return a wrongly claimed session to the shared queue instead, run `spx session release <session-id>`.

An explicit request to inspect, archive, or release identified session documents routes directly through the corresponding `spx session` command as operational-state management; `/handoff` is reserved for closing active work through reflection, persistence, continuation disposition, and claimed-session accounting. Direct session operations require `/understand` only before following their output into `spx/`, source, or test content.

<!-- /SPEC-TREE -->

# Outcome Engineering Plugin Marketplace

This product is a combined Codex and Claude Code marketplace (`outcomeeng/plugins`) delivering the Spec Tree methodology for [Outcome Engineering](https://outcome.engineering) — the product engineering paradigm where human-written specifications are the authoritative source of truth.

`AGENTS.md` and `CLAUDE.md` share product-owned instructions, while each file carries its own harness-specific managed Spec Tree instruction block.

## Two audiences, two design surfaces

This repo is two things at once.

It is a **product**, with its own spec tree under `spx/`, its own decision records, its own implementation under `outcomeeng/`, and authored plugin sources under `src/plugins/`. The reader of work in those directories is this product's own developers and agents. You may name this repo's nodes, languages, and conventions directly.

It is also a **methodology shipped as plugins** from generated runtime trees under `dist/claude/` and `dist/codex/`. Those plugins install into hundreds of consumer repositories whose spec trees, languages, layouts, and conventions are unknown at design time. The reader of shipped plugin content is a consumer agent in some other repository. Any design that assumes this repo's tree, this repo's languages, this repo's overlay declarations, or this repo's specific node addresses is wrong for that audience. Authored skill content under `src/plugins/` must render into language-neutral, portable plugin output; never a product-internal node path, never a single-language test filename pattern, never a PDR or ADR specific to this product.

Carrying assumptions from one surface to the other is the most common source of wrong design here. Designing a shipped plugin change as if every consumer were this repo, or naming this repo's PDR in a shipped skill body, breaks the change for every consumer that is not this repo. The Plugin Portability Constraints section below deepens the consumer-audience rules; references to specific nodes, languages, and overlays elsewhere in this file apply only when the audience is this repo's own developers.

## Coding Agents

This repository publishes two plugin surfaces from the same source tree:

- `.claude-plugin` for Claude Code skills and thin agents
- `.codex-plugin` for Codex skill bundles

Shared plugins ship both manifests where supported.

## Marketplace Methodology

This file covers repository rules that apply across both agents.

Claude Code-specific methodology — skill structure patterns, testing philosophy, research on skill activation — lives in [`methodology/`](methodology/CLAUDE.md). Read [`methodology/CLAUDE.md`](methodology/CLAUDE.md) when creating or restructuring skills, writing tests, or tuning skill descriptions for reliable activation.

Spec-tree methodology rules (node types, states, assertion types, ordering) live inline in `src/plugins/spec-tree/skills/understand/SKILL.md` and are authoritative over `methodology/`. Each skill owns its templates in that skill's `templates/` directory; the sibling `references/` directory carries conditional operational detail.

## Critical Rules

- ⚠️ **NEVER maintain backward compatibility** - When rewriting a module, replace it entirely. No legacy aliases, no re-exports of old names, no shims. Update all imports across the codebase to use the new API.
- ⚠️ **Depend on an `spx` CLI capability only after it is PUBLISHED and the floor is advanced** - The shipped skills and their tests invoke the `@outcomeeng/spx` CLI; a skill or test that assumes a capability merged only to spx `main` (not yet published to npm) ships a contract the consumer's installed CLI cannot honor, and surfaces as an opaque CI test failure or a consumer regression. Merged-to-spx-main is **not** "available." A capability is available only when (1) an `@outcomeeng/spx` release containing it is published to npm, (2) `REQUIRED_SPX_VERSION` in `outcomeeng/validation/spx_version.py` is advanced to that version, and (3) `SPX_VERSION` in `.github/workflows/check.yml` is bumped to a published version at or above the floor. The `spx-version` gate step enforces pin ≥ floor, and the pin can only reach a published version — so a dependency on an unpublished capability fails `just check-full` in CI with a named gap, governed by `spx/13-infrastructure.enabler/21-test-infrastructure.enabler/15-ci-gate.adr.md`.
- ⚠️ **Protect untracked work during cleanup** - use `just clean` (`git clean -fdX`) for gitignored artifacts such as `.metadata_never_index`, `.DS_Store`, and `__pycache__`. Inspect every non-gitignored untracked path before removing it and establish whether it is user work, generated output, or stale workspace state. Empty directories remain visible to filesystem discovery even though Git does not track them; remove a stale empty directory after confirming it is empty and no workflow owns it.
- ⚠️ **The methodology is multi-language** - Skill content shipped under `dist/` that names a test filename pattern, an import syntax, or any other language-specific token is wrong unless framed per-language with a cross-reference. Authoritative conventions live in `spx/15-test-language.adr.md` for this product and in each language plugin's `{language}-test-standards` skill for consumers. Never write `test_*.py` (or any single-language pattern) into a skill body that ships to consumer projects — the file under audit may be a `.test.ts`, a `.rs` test module, or whatever the consumer's language plugin declares.
- ⚠️ **Authored skill content names "Claude" as the subject — never strip it to satisfy the self-reference policy** - Per `instructions`'s `agent-prompt-standards` `<voice>` rule, skill and methodology content drops the subject (imperative mood) by default and names **"Claude"** for behavioral claims, tendencies, and failure modes; **"the agent"**, **"an agent"**, **"the model"**, and **"you"** are banned subjects. The router's **Agent identity in generated artifacts** rule governs **operational artifacts only** — branch names, commit messages, PR titles and bodies, review comments — NOT authored skill content under `src/plugins/`. The build ships authored "Claude" verbatim to both `dist/claude/` and `dist/codex/` (no identity substitution today); other-agent targeting is a downstream replacement step, so the authored canon is always "Claude". Conflating the two — removing "Claude" from skill content because the self-reference policy forbids it in commits — is a real, recurring error.
- ⚠️ **Editing a skill surface requires the typed skill auditor as a gate** - After changing any artifact that governs a skill surface — a `SKILL.md`, another file in a skill directory, an authored shared fragment, or a generated runtime copy — dispatch the configured `skill-auditor` role to a separate verifier agent session and give it the complete changed surface. Never run `instructions:audit-skill` or `/audit-skill` in the authoring conversation. The `changes-reviewer` local review and the CI `spec-tree-review` do not load the skill-authoring standards (`skill-standards`, `agent-prompt-standards`) and cannot replace this gate.

- 🛑 **STOP TRIGGER — NEVER abbreviate a session ID, or any identity value** - A session ID is `YYYY-MM-DD_HH-MM-SS` and is reproduced **verbatim and in full** every single time — in prose, questions, commits, and tool calls. NEVER shorten it to a fragment (e.g. the `HH-MM-SS` tail, the date, or any substring): a fragment identifies nothing, is ambiguous across sessions, breaks `spx session show/pickup/archive` lookups, and obscures the user's comparison against the source. The same rule binds every agent-surfaced identity value — commit SHA, run ID, `owner/repo`, host account, agent-session ID: copy it exactly from its source, never paraphrase or truncate it (this is the product-level verbatim-identity compliance rule in `spx/outcomeeng.product.md`). If a value is long, paste the whole value; do not "tidy" it.

- ✅ **Use this repo's command surface exactly** - Skills decide when validation, tests, review, audit, merge, and marketplace sync are required. `AGENTS.md` records this repo's concrete command forms and how to pass the file set:
  - `[test]` evidence: `just test <pytest-target>...`. Pass co-located spec test files, node test directories, or pytest node IDs, for example `just test spx/21-spec-tree.enabler/76-merge.enabler/tests/test_merge_gate_policy.mapping.l1.py`. When a source file under `outcomeeng/`, `outcomeeng_testing/`, `outcomeeng_evals/`, or `src/plugins/` changes, pass the spec test file(s) or node test directory that exercise it; do not pass implementation paths as if they were tests. Never run bare `pytest`.
  - Verbose failing test rerun: `just test-v <same pytest-target>...`.
  - `[eval]` evidence: `just eval <eval-toml>`, `just eval-case <eval-toml> <case-id>`, or `just eval-node <node-path>`. These wrap `uv run outcomeeng-evals run`, read `plugin_dir` from `eval.toml` unless `PLUGIN_DIR` is set, and default to `MAX_BUDGET_USD=0.75`, `WORKERS=1`, and `TIMEOUT_SECONDS=180`. Do not run bare `outcomeeng-evals`; do not raise `MAX_BUDGET_USD`, `WORKERS`, or `TIMEOUT_SECONDS` without structured operator approval.
  - Spec-only or Markdown-instruction-only changes: `spx validation markdown` and `spx spec status --format json`. These commands take no changed-file list; the scope is the markdown/spec lane.
  - Markdown formatting: `just fmt <changed-markdown-file>...`. Pass every changed Markdown file that dprint formats, for example `just fmt AGENTS.md spx/local/open-pr.md`.
  - Python formatting: `just fmt-python <changed-python-file>...`. Pass every changed Python file that ruff formats.
  - Skill or plugin Markdown under `src/plugins/` or generated `dist/`: `just check-skills` and `just docs-check`. These commands take no changed-file list; they check the committed skill/catalog surfaces.
  - Selected local deterministic gate: `just check`. This automatically selects the gate steps that cover the changed paths and prints the selected steps with reasons before running them through the recipe runner.
  - Full deterministic gate: `just check-full`. CI invokes this full gate on `pull_request` and push to `main`; run it locally only when the active skill, `spx/local/merging.md`, the governing node, risk evidence, or the user explicitly requires the full gate.
  - Generated plugin trees after `src/plugins/` edits: `just build-skills`. Do not hand-edit `dist/`.
  - Plugin version bumps: `just bump` (run before `just build-skills` so `dist/` carries the bumped version). NEVER hand-edit a manifest `version` field — `just bump` classifies the segment and writes both manifests in lockstep; `spx/local/commit-changes.md` carries the full bump policy.
  - Generated root Spec Tree instruction blocks after instruction-block-template or distribution-render changes: `just build-skills`, then `just build-instructions`. Do not hand-edit the managed instruction blocks in `CLAUDE.md` or `AGENTS.md`; regenerate them from the rendered harness templates in `dist/`, then verify with `just instructions-check`. Several router sections are pinned verbatim: each `*_POLICY_REQUIREMENTS` tuple in `outcomeeng/distribution/instruction_block.py` asserts literal substrings of one template section, so rewording a pinned section without updating its tuple in the same change fails the render with a named missing requirement instead of a wording diff. This coupling is internal to this repository's build; it never ships to consumers.
  - Generated eval CI trigger paths after an `eval.toml` `owned_paths` edit: `just build-eval-triggers`. Do not hand-edit the marker-delimited `paths:` blocks in `.github/workflows/spec-tree-evals.yml`; the gate's `eval-triggers` step fails on drift.
  - Marketplace installation verification before merge: `just verify-marketplace-installation`. The command runs the complete repository-installation evidence through pytest discovery, including real agent CLIs in disposable homes, and leaves persistent state unchanged.
  - Marketplace release installation after merged plugin-distribution changes: `just install-marketplace` from the merged assigned checkout, as directed by `spx/local/merging.md`. The command refreshes exactly the installed catalog plugins in Claude Code project scope and the selected `$CODEX_HOME`; empty agent state receives only `spec-tree` with a warning, and nonempty state without `spec-tree` is rejected before mutation.
- 🛑 **STOP TRIGGER — NEVER raise command expense ceilings without explicit operator approval** - Command defaults are authority for cost-bearing and quota-bearing runs. Do not add or increase flags, environment variables, or config values that raise spend, quota use, hosted minutes, paid API usage, token budget, worker parallelism, retry count, timeout, or external-service capacity without structured operator approval in the same turn. Examples include `--max-budget-usd`, model/API budget caps, worker or parallelism counts, retry limits, hosted-runner minutes, and paid-provider switches. If a command fails because the default ceiling is too low, stop and ask through the structured-question tool the router block names, naming the exact failed command, the blocked ceiling, the proposed new ceiling, and a pause/inspect option.
- ✅ **Use the Justfile as this repo's command interface** - Use `just --list` / `just help` only to confirm exact recipe spelling after a governing instruction has selected the command class; do not use recipe discovery to choose an independent validation strategy. Repository-local Python modules (`python3 -m outcomeeng.*`, `uv run python -m outcomeeng.*`, and similar module invocations) run through `just` recipes only; inside the `Justfile`, those invocations are recipe implementation details. If a needed repository operation exists only as a Python module, add or fix the narrow Just recipe first, then run the recipe. Plugin-shipped skill scripts are different: when an active skill instructs a direct `python3 "${CLAUDE_SKILL_DIR}/scripts/..."` command, run that exact portable skill script. To understand a recipe, inspect `Justfile` and the underlying source with read-only tools; execute through `just`.
- ✅ **Dog-food platform features in skills** - When you discover an undocumented Claude Code capability (e.g., `skills:` field in subagents), check whether our skills teach it and update them if not
- ⚠️ **Spec-only validation stays on the spec lane** - When the change only adds or edits specs, decisions, EXCLUDE entries, or Markdown instructions, use the spec-only command pair in this repo's command surface above. Do not run `spx validation all`, install Node dependencies, or run ESLint/TypeScript validation unless JavaScript/TypeScript source, package manager files, validation config, or the validation pipeline changed, or the user explicitly asks for the full gate.

## Plugin Portability Constraints

Plugins from this product are installed into consumer projects that share none of this repository's tooling. When a skill or agent invokes a script that ships inside a plugin, the script runs against the consumer's environment — not against this repo's `uv`, `pyproject.toml`, or `outcomeeng_*` packages.

Authors of skills, agents, and the scripts they invoke must assume:

- ⚠️ **Only the installed plugin tree is guaranteed present.** Consumer checkouts do not contain `src/`, `dist/`, `outcomeeng/`, `outcomeeng_evals/`, `outcomeeng_testing/`, `spx/`, or any other top-level directory from this repo. Anything a plugin script needs at runtime must render into that plugin's own generated runtime tree under `dist/claude/` and `dist/codex/`.
- ⚠️ **`python3` only — no `uv`.** Skill content invokes scripts via `python3 "${CLAUDE_SKILL_DIR}/path/to/script.py"` — the skill loader substitutes the path before the agent sees it. Hooks (in `hooks/hooks.json`) and MCP server configs use `${CLAUDE_PLUGIN_ROOT}` instead, since they have no skill directory. Agent definition files (under `agents/`) get neither variable substituted in the prompt body and `${CLAUDE_PLUGIN_ROOT}` is not a Bash environment variable, so agents must reach `scripts/` only by invoking a skill that resolves the path. **Shipped scripts support the two most recent Python feature releases (currently 3.14 and 3.13), with the older as the floor (3.13)**, per `spx/12-shipped-scripting.adr.md`. Use a managed interpreter (Homebrew or equivalent), never the system macOS Python, which lags years behind (macOS 26 ships 3.9). Scripts may use `StrEnum`, `tomllib`, exception groups, `type` aliases, and other features the floor provides without conditional fallbacks; consumers on older Python must upgrade. The linter and type-checker that govern shipped scripts are pinned to the floor (currently 3.13) so a shipped script never uses a feature the floor lacks. No `uv run`, no `pip install`, no project-scoped virtualenv.
- ⚠️ **Stdlib only.** No `click`, no `pydantic`, no third-party JSON Schema, no `tomllib`-via-package. `argparse`, `json`, `dataclasses`, `enum`, `pathlib`, `subprocess`, `sys`, `typing` — that's the toolbox. Anything richer must be vendored or replaced.
- ⚠️ **No on-the-fly dependency installation.** Skills must not run `pip install`, `uv pip install`, `npm install`, or any other package fetch as part of their normal flow. Consumers approve plugin installation once; runtime side effects must not include further installations.

The `outcomeeng_*` Python packages in this repo are part of the product's own toolchain (validation, distribution, eval harness) — they exist to build and test the plugins, not to be invoked by skills inside consumer projects. Code that lives outside a generated plugin runtime tree is not portable.

When a skill genuinely needs richer Python machinery, the right answer is usually to write the logic in stdlib-only form, ship it inside the plugin, and document the `python3 "${CLAUDE_SKILL_DIR}/..."` invocation in the skill body.

## Markdown Formatting Rules

**IMPORTANT: Pseudo-XML in Markdown Code Fences**

When documenting XML-like syntax that isn't valid XML (pseudo-XML with text content, no proper elements), **ALWAYS use `text` as the language identifier**, not `xml`:

```text
<!-- ✅ CORRECT: Use "text" for pseudo-XML -->
<metadata>
  timestamp: [UTC timestamp]
  product: [Product name]
</metadata>
```

**Why:** The markup formatter (`markup_fmt`) in dprint will attempt to format XML code fences and can mangle pseudo-XML syntax. Using `text` prevents this issue while maintaining syntax highlighting compatibility with most linters.

**NEVER USE:**

- `` ```xml `` for pseudo-XML (causes formatting issues)
- `` ``` `` with no language identifier (rejected by some markdown linters)

## Documentation

### Official Anthropic Resources

**Core Documentation:**

- [Create plugins](https://code.claude.com/docs/en/plugins) - How to create and structure plugins
- [Plugin Marketplaces](https://code.claude.com/docs/en/plugin-marketplaces) - How to create and distribute marketplaces
- [Plugins Reference](https://code.claude.com/docs/en/plugins-reference) - Complete technical specifications, schemas, and CLI commands
- [Discover Plugins](https://code.claude.com/docs/en/discover-plugins) - How users find and install plugins
- [Agent Skills](https://code.claude.com/docs/en/skills) - Creating and using Skills

**Announcements:**

- [Claude Code Plugins Announcement](https://www.anthropic.com/news/claude-code-plugins) - Official plugin system launch
- [Agent Skills Introduction](https://www.anthropic.com/news/skills) - Skills feature announcement

**Best Practices:**

- [Claude Code Best Practices](https://www.anthropic.com/engineering/claude-code-best-practices) - Agentic coding patterns

### OpenAI / Codex Resources

- [Codex](https://openai.com/codex) - Codex product overview
- [Codex Overview](https://platform.openai.com/docs/codex/overview) - Codex cloud and local workflow overview
- `codex --help` - Local CLI reference
- `codex plugin --help` - Local plugin management reference

## Plugin Catalog

Every skill and thin agent across every plugin is listed in the auto-generated catalog in [`README.md`](README.md#plugins), sourced from `.claude-plugin/marketplace.json` and the YAML frontmatter of each plugin's `SKILL.md` and `agents/*.md`. Run `just docs` to regenerate; `just check-full` enforces freshness in CI. Do not maintain plugin tables in this file.

## Spec Tree Methodology

The Spec Tree methodology for [Outcome Engineering](https://outcome.engineering). Three steps drive the methodology: **declare, spec, apply**. Audit gates operate within each step. See `src/plugins/spec-tree/skills/understand/SKILL.md` for the authoritative inline foundation.

### Spec-tree navigation: declaration and inverse

The methodology declares forward:

```text
PDR/ADR → spec assertion → [test](path) link → test file → import → implementation file
```

The PR flow, the apply flow, and any code-change workflow need the *inverse* — from a code change in the diff back to the spec that governs it:

```text
implementation file
  → grep imports across spx/**/tests/  (per-language import syntax)
  → set of test files
  → spec assertions linking those test files via [test]
  → containing node directory under spx/
```

`spx/` contains only specs, decision records, coordination notes, co-located `tests/` and `evals/` evidence directories, optional `knowledge/` roots on a node or the product root, and operational configuration (`spx/local/`, `spx/EXCLUDE`). Implementation code lives outside `spx/` (in `src/plugins/`, `outcomeeng/`, generated `dist/`, etc.). The inverse navigation walks from an outside-`spx/` file in the diff, through the import graph into an inside-`spx/` test, then up to the spec assertion linking that test, then up to the containing node.

If multiple implementation files in the diff resolve to multiple nodes, take their lowest common ancestor in the tree — `/contextualize` on the LCA pulls constraining context for every descendant.

An implementation file in the diff that no test imports has no governing spec assertion — a coverage gap the PR is shipping. Specs declare; tests verify; code complies. Surface the gap; do not invent a node to load.

Per-language test conventions live in `spx/15-test-language.adr.md` (this product uses pytest with `test_<subject>.<evidence>.<level>.py`) and in each language plugin's `{language}-test-standards` skill. In a consumer repo, the consumer's spec tree and language plugin determine the conventions; the inverse-navigation procedure is the same.

## Before Making Changes

### After Adding/Modifying Skills, Agents etc

Everything under `src/plugins/` is authored source; the installed trees under `dist/claude/` and `dist/codex/` are generated. After any `src/plugins/` edit, regenerate them so the two match:

```bash
just build-skills   # uv run python -m outcomeeng.distribution.build src dist
```

The pre-commit hook runs `build-skills` automatically, and `just check-full`'s `dist-diff` step (`git diff --exit-code dist`) fails when `dist/` is out of sync with `src/` — so a `src/plugins/` change and its regenerated `dist/` land in the same commit. Because the hook regenerates `dist/` at commit time, an uncommitted working tree that has `src/plugins/` edits but no matching `dist/` change is the **expected** mid-edit state — never report it as a defect, a review finding, or a merge blocker (for example "the generated trees have not been rebuilt" or "`dist/` is out of sync"). Only a `src/`↔`dist/` divergence that survives into a commit is a problem, and the hook prevents that. Never hand-edit `dist/`; edit `src/plugins/` and rebuild.

Continue through [Git workflow](#git-workflow) when the change is destined for the default branch. `/merge` dispatches to the selected transport; for the GitHub-PR transport it delegates to `/manage-github-pr`, which routes committing, opening, management, merge, and closure.

**When adding a new plugin**, register it in **both** marketplace catalogs:

| File                               | Surface     |
| ---------------------------------- | ----------- |
| `.claude-plugin/marketplace.json`  | Claude Code |
| `.agents/plugins/marketplace.json` | Codex       |

`just check-full` will fail if a plugin directory is missing from either catalog.

### Top-level layout

- `src/plugins/` — authored skills, thin agents, manifests, and templates. One subdirectory per plugin.
- `dist/claude/`, `dist/codex/` — generated runtime plugin trees (rebuilt from `src/plugins/` by `just build-skills`) shipped to consumer repos. The plugin catalog in [`README.md`](README.md#plugins) is authoritative for what each plugin contains; this file does not duplicate it.
- `spx/` — this product's spec tree (durable map). The managed Spec Tree instruction block in this root file is the skill router. `spx/local/` holds the product-specific skill overlays and carries the generated-source declaration `generated-sources.toml`, a verification-scope input distinct from the `*.md` skill overlays.
- `outcomeeng/`, `outcomeeng_testing/`, `outcomeeng_evals/` — this product's Python toolchain (validation, distribution, eval harness) and its test infrastructure. Not portable to consumer projects; do not import from inside any plugin.
- `.claude-plugin/marketplace.json` — Claude Code marketplace catalog (one entry per shipped plugin).
- `.agents/plugins/marketplace.json` — Codex marketplace catalog (mirror of the above).
- `.spx/` — gitignored operational files (sessions, audit state).
- `.claude/settings.json` — product-scoped Claude Code plugin selection, committed for collaborators.
- `.codex/config.toml` — repository Codex settings unrelated to plugin installation or enablement.
- `CHANGELOG.md` — the pointer table naming this repository's two changelog lines, plugin and marketplace, where each is authored, and how each ships. It carries no entries itself, because a changelog reaches its reader only from inside an installed plugin.
- `PROPOSED.md` — the methodology release model: edition versus version, the `provides` / `supports` / `migratingFrom` grammar, and the changelog model it proposes.
- `AGENTS.md` (this file), `CLAUDE.md` (harness-specific copy) — repo-level instruction surfaces.

For the contents of any plugin or `spx/` subdirectory, run `ls` or read the catalog. The authored directory layout under each plugin follows the conventions in `src/plugins/instructions/skills/`.

## Git workflow

### How skill content reaches a session

**Claude Code** uses the project-scoped GitHub marketplace `outcomeeng/plugins`. `just install-marketplace` validates that user scope carries no colliding `outcomeeng` registration, inspects the plugins installed for the invocation checkout, reconciles the project registration to the canonical source, and refreshes exactly those catalog plugins.

**Codex** marketplace registration and plugin installation belong to the selected `$CODEX_HOME`. Explicit `codex plugin marketplace add` and `codex plugin add` commands update that selected home. Repository `.codex/config.toml` has no plugin installation or enablement semantics. Persistent installation reconciles generated agent definitions into the selected `$CODEX_HOME/agents/` registry under a digest-bound marketplace ownership record, leaving foreign and modified files untouched and maintaining exactly one current canonical role per authored marketplace agent. A plugin lifecycle skill reconciles only its own recorded definitions; catalog-wide installation owns cross-plugin pruning. A checkout definition is coherent only where that checkout also carries the skill content it invokes. A checkout definition shadowing selected-home skills is a scope split that stops reconciliation: remove a byte-identical generated copy, and inspect a changed or unrecognized copy as a collision. Marketplace installation never requires creating or committing checkout agent definitions.

Each harness retains plugin content already loaded by a running session. Reload the harness plugin index or start a new session after persistent installation when the current session must consume refreshed content.

### Smoke-testing skill changes

Work in the checkout whose authored plugin files you are changing:

1. Edit `src/plugins/<plugin>/` and run `just build-skills` so the change lands in `dist/claude/<plugin>/`.
2. Run `just verify-marketplace-installation` to install both committed catalogs through the real agent CLIs in disposable homes and verify selected-home placement, ownership-safe pruning, foreign-collision preservation, and scope-split rejection.
3. After a merged release, run `just install-marketplace` from the assigned checkout at `origin/main` to refresh the selected persistent Claude Code project and Codex home.

`just verify-marketplace-installation` is the pre-merge proof and mutates only disposable state. `just install-marketplace` is the release action and mutates the selected persistent state. A persistent run stops before its first state-changing command when Claude Code user scope contains an `outcomeeng` registration, reporting the exact colliding settings path.

## Missing plugins or skills

With explicit operator authorization to change persistent plugin state, run `just install-marketplace` from the intended checkout. The command inspects each agent's installed `outcomeeng` plugins, bounds and orders them through that agent's committed catalog, reconciles the canonical GitHub source, refreshes exactly that set, and reconciles the selected plugins' generated Codex definitions into the selected home under marketplace ownership. Empty agent state receives only `spec-tree` and a warning. Nonempty state without `spec-tree` is rejected before mutation.

Claude Code state is project-scoped. A user-scoped `outcomeeng` registration blocks the command and must be resolved by the owner of that settings file. Codex state belongs to the selected `$CODEX_HOME`; repository `.codex/config.toml` remains unrelated to plugin setup. Use `just verify-marketplace-installation` when the goal is disposable proof rather than a persistent state change.

<!-- SPEC-TREE:shared commands -->

## Spec Tree Phase Commands

- **author** — Regenerate the generated trees after `src/plugins/` edits: `just build-skills`. Regenerate the root instruction blocks after instruction-template edits: `just build-instructions`.
- **verify** — Node and changeset tests: `just test <pytest-target>...`. Spec-only or Markdown-only changes: `spx validation markdown` and `spx spec status --format json`. Skill/plugin Markdown: `just check-skills` and `just docs-check`.
- **gate** — Full local deterministic gate: `just check-full`.
- **merge** — Ship to the default branch through `/merge`; the GitHub-PR transport merges with `gh pr merge <pr-number> --merge --delete-branch=false`.

<!-- /SPEC-TREE:shared commands -->

<!-- SPEC-TREE:shared generated-sources -->

## Generated Sources in Verification Scope

`spx/local/generated-sources.toml` is the committed declaration of every generated extent in this repository — whole generated files by path pattern and generated regions of authored files by marker pair — with each relation's authored sources, generator, and regeneration command. It is governed by `spx/31-outcomeeng.enabler/31-verification.enabler/15-generated-attribution.pdr.md` and is the single source of generated-source attribution: never infer generated status from path names.

- Agentic verification (review, audit) excludes declared generated extents from judgment and names the skipped extents in its verdict — unless the changeset touches the relation's sources or generator, or the source-to-output contract is the declared verification subject, in which case the generated extents are evidence. Journal-recorded skip evidence arrives with the `spx` verification scope projection; until then the exclusion binds through this instruction alone.
- Findings about generated content resolve to the relation's sources; never hand-edit a generated extent.
- Deterministic verification covers the complete changeset; each relation's regeneration command backs regeneration parity — rerunning it leaves the committed generated extents byte-identical.
- Generation inputs and generator implementations are authored files judged in their generation role — template directives are template syntax, never defective final output.

This section is the interim consumer of the declaration; the `spx` verification scope projection supersedes it when that capability ships.

<!-- /SPEC-TREE:shared generated-sources -->
