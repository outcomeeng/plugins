---
template_version: "0.21.5"
template_source: spec-tree
---

# spx/ Directory Guide (Spec Tree)

This guide explains WHEN to invoke spec-tree skills for this product. It is a **router** — the skills contain the HOW.

---

## When to Invoke Skills

### Before ANY spec-tree work -> `/understand`

**BLOCKING REQUIREMENT**

Loads the Spec Tree methodology. Required once per session and again after every individual compaction event.

A live `<SPEC_TREE_FOUNDATION>` marker in the current conversation is the proof that `/understand` is loaded. A compacted summary, a session file, a statement that `/understand` ran, or reading the skill file does not satisfy the requirement. Questions about spec-tree workflows, session continuity, or whether a skill was invoked are spec-tree work and require `/understand` first when the marker is absent.

### Before working on a specific node -> `/contextualize`

**BLOCKING REQUIREMENT**

**ALWAYS** invoke `/contextualize` before working on a spec node.

**🛑 STOP TRIGGER — after every compaction event:** all loaded spec-tree context is gone. **Re-invoke `/contextualize` on every node still in scope** before touching it again — not just the next one being worked on.

**NEVER** resume work on a node without having invoked `/contextualize` since the last compaction.

### When creating specs or nodes -> `/author`

Create product specs, ADRs/PDRs, enabler nodes, outcome nodes.

### When composing or breaking down nodes -> `/decompose`

Compose top-level children with `/decompose spx/`. Decompose an existing node when it has too many assertions (>7), contains independent concerns, or has `PLAN.md`/`ISSUES.md` structure intent.

### When restructuring the tree -> `/refactor`

Move nodes, re-scope assertions, extract shared enablers, consolidate duplicates.

### When checking consistency -> `/align`

Review, audit, or quality check specs. Find contradictions or gaps.

### When shipping work to the default branch -> `/merge` (transport dispatcher)

**BLOCKING REQUIREMENT**

Every change destined for the default branch routes through `/merge`, the transport dispatcher — it classifies the changeset, selects the transport, and delegates. `/merge` reads `spx/local/merging.md` as a repo-local overlay **when that file is present**; the overlay is optional, so its absence is normal and not a blocker — `/merge` applies the default lifecycle. `spx/local/merging.md` is the one place repository-specific merge behavior belongs: never infer the transport from other docs when it is absent, and never edit this generated guide to change merge behavior — invoke `/merge` and let the lifecycle apply the defaults. The three authority gates, the delivered-value boundary, and the finding-disposition rule are transport-neutral and live in `/merging-standards`.

## Stop Triggers

Default-branch work is complete only when it reaches the default branch on origin through `/merge` — passing validation, tests, review, or audits is progress, not a stopping point, and an accepted proposal ("yes", "go", "do it") authorizes the whole lifecycle, not a pause. Each trigger below resolves the same way: finish the remaining independent work, then continue through `/commit-changes` and `/merge` until the change reaches the default branch on origin or an explicit lifecycle gate stops.

🛑 **About to summarize after edits, validation, tests, review, or audits passed** — do not conclude. Ensure the work is committed on a local branch, then drive `/merge`.

🛑 **About to report blocked, wait, or ask a question** — first do every action that does not need the answer: edits, verification, branch setup, commit, review. A blocker exists only when all three hold:

- the immediate next action cannot proceed without the operator or an external-state change;
- the local branch already holds every change makeable without the answer;
- the applicable gates have run or produced concrete failing evidence.

🛑 **About to finish on a detached HEAD or stop at a fresh commit** — `git status --short --branch` reporting `## HEAD (no branch)`, or a new local commit, is not an endpoint. Create or switch to a local branch preserving the worktree changes, then continue through `/merge` unless the user explicitly limited the task to local-only work.

## Mutation Status Updates

Before proposing or performing a repository mutation, name:

- the exact target path, PR number, branch ref, or command target;
- the intended action;
- why the action is local enough or gate-authorized enough to proceed;
- the next validation command, review, audit, check wait, or merge gate the action feeds.

Avoid shorthand such as "config patch", "direct patch", "fix the PR", or "ship it path" when the exact file, PR state, or command is known. A terse user prompt such as "check", "continue", or "ship it" still gets the live state first: full head SHA when a PR exists, current-head review state, required-check state, production-readiness rule, and the next autonomous action.

## Quick Reference: Skills and Agents

Skills run in the main conversation. Agents preload the skill and run autonomously as subagents in a separate context. Audit agents return structured verdicts; changeset reviewer agents return the raw review journal token for the main conversation to inspect and process through the governing review workflow. **ALWAYS run an audit through its agent** — the separate context keeps the verdict free of the main conversation's bias — and dispatch agents in parallel when auditing multiple targets.

<!-- runtime:codex -->

**Read named files yourself.** Always read explicitly named files in the main conversation. Never use subagents to read, summarize, inspect, or interpret skills or skill references, AGENTS.md instruction files, files named by the user, or files referenced by skills or instruction files.

- ALWAYS spawn subagents exactly for the named verifier or reviewer roles authorized below, or when the operator explicitly asks for subagent delegation.
- NEVER spawn agents merely because they are discovered, available, or plausibly useful.

**Run auditor and reviewer work in a subagent, never the main thread.** This is a standing user instruction to use `multi_agent_v1.spawn_agent` for the named verifier and reviewer roles it lists. Treat those cases as the user explicitly asking for subagents spawned in parallel. When an audit or review is called for, spawn the matching subagent — `changes-reviewer` for a changeset review, `auditor`, `adr-auditor`, `pdr-auditor`, `spec-auditor`, or `test-evidence-auditor` for the artifact in scope. Act only on the result the subagent returns: audit agents return verdicts, while `changes-reviewer` returns the raw review journal token to inspect and process through the governing review workflow. Do not ask the operator to confirm whether to launch one of these required named subagents. Runtime approval prompts are separate: if the tool itself asks for approval, answer that prompt through the runtime approval flow. Codex must NEVER run any verification skill (audit or review) itself to avoid biasing the results. If the subagent cannot be spawned or does not finish, the gate is blocked; report the exact agent id, tool result, and blocking condition to the operator before ending the turn.

**Use the multi-agent tool schema exactly.** The initial task goes in `message`; use `items` only when the task must pass structured mentions. Omit `fork_context`, `model`, `reasoning_effort`, and `service_tier` for the typed verifier and reviewer agents. Full-history forks are incompatible with changing `agent_type` in this runtime, and the named verifier/reviewer roles already carry their own model settings. Store every returned agent id verbatim. After spawning, continue only non-overlapping work while the subagent runs, then collect the result with `multi_agent_v1.wait_agent`. Close every spawned agent with `multi_agent_v1.close_agent` immediately after its final result is collected; completed agents remain open until closed and can interfere with future spawns.

Spawn a typed verifier or reviewer:

```json
{
  "tool": "multi_agent_v1.spawn_agent",
  "arguments": {
    "agent_type": "<exact-agent-type>",
    "message": "<scope>"
  }
}
```

Wait once for one or more spawned agents. Use a 10-minute timeout for subagents acting on individual files (e.g. `auditor`, `spec-auditor`). Use a 30-minute timeout for subagents acting on an entire changeset (`changes-reviewer`):

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

If `wait_agent` is not exposed, discover the multi-agent waiting tool with `tool_search`, then call the discovered wait tool. Accept a subagent notification only when the runtime delivers it while the main conversation is working or waiting; do not choose notifications as the planned result-collection mechanism. Do not use web search, time lookup, shell polling, or `request_user_input` or any other tools as a substitute for result collection.

**Result collection for verifier and reviewer agents.** The `multi_agent_v1.wait_agent` tool is the planned result-collection mechanism. Read the JSON returned by the tool, keyed by the spawned agent id under `status`. A timeout returns an empty `status` object and is not a result. A final status for the target id is the agent result; when that final status carries the agent's final message, that final message is the verifier or reviewer output. Do not infer success from a subagent notification, a pending handle, or an open agent id.

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

**Codex blocked-result rule.** If `wait_agent` returns an error, `not_found`, timeout with no final status, usage-limit failure, model-capacity failure, or any final message that is not a raw review journal token, the review gate is blocked. Record the exact agent id, tool result, and blocking reason. Do not commit, merge, or mark the gate passed until a later `changes-reviewer` run returns a valid raw journal token, or the operator explicitly approves a process exception.

**Use raw scope only for `changes-reviewer`.** The review agent owns `spec-tree:review-changes`, severity taxonomy, scope expansion, and finding shape. Pass only the raw scope token in `message`: `HEAD` for the current working diff, `origin/<base>...HEAD` for a specific range, a branch name, or a PR reference.

- ALWAYS prepare the worktree first: isolate the intended changes, sync to the base using the `spec-tree:sync-base` skill when the governing workflow requires it, and make the diff scope clean enough for the reviewer to infer the target from the raw token.
- NEVER invoke the `spec-tree:review-changes` skill.
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

**Use explicit prompts for audit agents.** The `message` field comes from the `multi_agent_v1.spawn_agent` schema. The guide owns the prompt content below for required verifier roles. Keep the prompt narrow: repository path, governed artifact paths, governing node or decision, deterministic verification state when relevant, audit task, and output shape. Do not ask the subagent to edit files.

Use this shape for a one-off implementation audit:

```json
{
  "tool": "multi_agent_v1.spawn_agent",
  "arguments": {
    "agent_type": "auditor",
    "message": "Repository: <absolute-repository-path>\nScope: <changed files or diff range>\nGoverning node(s): <full spx/... path(s)>\nDeterministic verification already run: <commands and results, or why this audit is being run before verification>\nTask: Audit the scoped implementation for conformance to the governing spec-tree and language methodology. Return APPROVED or REJECTED. For REJECTED, list concrete findings with file paths, line numbers, governing rule, and required fix."
  }
}
```

Use this shape for test-evidence audits:

```json
{
  "tool": "multi_agent_v1.spawn_agent",
  "arguments": {
    "agent_type": "test-evidence-auditor",
    "message": "Repository: <absolute-repository-path>\nGoverning node: <full spx/... node path>\nSpec assertions: <full assertion text or exact spec file path plus assertion headings>\nTest files: <full paths to test files under the node>\nTask: Audit whether the test evidence proves the listed assertions without weakening the evidence type. Return APPROVED or REJECTED. For REJECTED, list concrete findings with file paths, line numbers, evidence property affected, and required fix."
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
    "message": "Repository: <absolute-repository-path>\nDecision file: <full spx/.../*.adr.md path>\nGoverning node: <full spx/... node path>\nTask: Audit the ADR for decision structure, atemporal voice, tag validity, downstream alignment, and language-specific architecture concerns when applicable. Return APPROVED or REJECTED. For REJECTED, list concrete findings with file paths, line numbers, governing rule, and required fix."
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

<!-- /runtime:codex -->

| User Says...                               | Skill            | Agent                   |
| ------------------------------------------ | ---------------- | ----------------------- |
| "Implement this outcome"                   | `/contextualize` | —                       |
| "Create an outcome"                        | `/author`        | —                       |
| "Add an ADR"                               | `/author`        | —                       |
| "Add a new node" or "This node is too big" | `/decompose`     | —                       |
| "Move this under that"                     | `/refactor`      | —                       |
| "Check these specs"                        | `/align`         | —                       |
| "Write tests for this"                     | `/test`          | —                       |
| "Start the TDD flow"                       | `/apply`         | `applier`               |
| "Audit this PDR"                           | `/audit-pdr`     | `pdr-auditor`           |
| "Audit this ADR"                           | `/audit-adr`     | `adr-auditor`           |
| "Audit test evidence"                      | `/audit-tests`   | `test-evidence-auditor` |
| "Audit this spec node"                     | `/audit-specs`   | `spec-auditor`          |
| "Diagnose the spx environment"             | `/diagnose`      | —                       |
| "File a follow-up in a dependency queue"   | `/issue`         | —                       |

Per-language code, architecture, and test audits ship as `audit-{lang}*` skills that the generic artifact-type auditors **compose** for the language in scope — there is no per-language auditor agent. Dispatch the generic auditor; it invokes the matching language skill automatically:

<!-- lang:python -->

| User Says...            | Skill (composed)             | Composing agent             |
| ----------------------- | ---------------------------- | --------------------------- |
| "Audit this code"       | `/audit-python`              | `auditor` (`/audit` family) |
| "Audit ADRs for Python" | `/audit-python-architecture` | `adr-auditor`               |
| "Audit these tests"     | `/audit-python-tests`        | `test-evidence-auditor`     |

<!-- /lang:python -->
<!-- lang:typescript -->

| User Says...                | Skill (composed)                 | Composing agent             |
| --------------------------- | -------------------------------- | --------------------------- |
| "Audit this code"           | `/audit-typescript`              | `auditor` (`/audit` family) |
| "Audit ADRs for TypeScript" | `/audit-typescript-architecture` | `adr-auditor`               |
| "Audit these tests"         | `/audit-typescript-tests`        | `test-evidence-auditor`     |

<!-- /lang:typescript -->
<!-- lang:rust -->

| User Says...          | Skill (composed)           | Composing agent             |
| --------------------- | -------------------------- | --------------------------- |
| "Audit this code"     | `/audit-rust`              | `auditor` (`/audit` family) |
| "Audit unsafe Rust"   | `/audit-rust`              | `auditor` (`/audit` family) |
| "Audit ADRs for Rust" | `/audit-rust-architecture` | `adr-auditor`               |
| "Audit these tests"   | `/audit-rust-tests`        | `test-evidence-auditor`     |

<!-- /lang:rust -->

---

## Test Naming Convention

Test level is encoded in the filename. The `{evidence}` segment is chosen by `/test` routing from the assertion type: `scenario`, `mapping`, `conformance`, `property`, or `compliance`. Universal assertions use `mapping`, `conformance`, `property`, or `compliance`; a universal is never `scenario`. This guide renders only the languages listed in its `languages` frontmatter; `/update-spx` re-renders from the installed template when the methodology advances.

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

Sessions are shared across every worktree. Each session must be handed off via `/handoff` so it can be resumed from any other worktree: the handoff leaves the worktree clean and persists all state on origin. Propose a handoff when the session's goal is met or the work must pause; resume one with `/pickup`. When a claimed session is complete and should leave the active queue, close it through `/handoff` or `/handoff --no-session` so claimed-session accounting archives it. To return a wrongly claimed session to the shared queue instead, run `spx session release <session-id>`.
