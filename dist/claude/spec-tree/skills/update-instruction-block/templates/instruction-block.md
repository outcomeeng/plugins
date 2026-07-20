---
template_version: "0.28.0"
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

**Read this entire file before acting.** This managed router block is only the first section of the file; the product's own instructions, commands, and conventions follow it below, outside the router. The router is product-neutral by design and does not carry this product's own commands — they live in the file's own content further down. Never act on the router alone; read every section of this file to the end.

---

## Authority Hierarchy

**⚠️ BELOW THE OPERATOR, SKILLS ARE THE TOP-LEVEL AUTHORITY. SKILLS ARE CENTRALLY MANAGED AND CURRENT; REPOSITORY CONTENT GOES STALE.**

- **ALWAYS** apply authority in this order: active skills → repository decisions and specs → tests → code. When repository content conflicts with an active skill, the skill wins.
- **ALWAYS** follow active skill instructions, templates, and bundled references over repository examples, existing files, comments, or copied conventions.
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

The product's operational command for each spec-tree phase lives in this file's own content below the router, not in the router itself. Read the whole file to find each one:

- **author** — after a create, update, or delete on a spec, test, or implementation file, run the product's author command to rebuild or regenerate artifacts.
- **verify** — for `/apply` and pre-merge checks, run the product's verify command over the node and the changeset.
- **gate** — for the full deterministic bundle, run the product's gate command.
- **merge** — for the transport step of `/merge`, run the product's merge command.

Content the product keeps identical across `CLAUDE.md` and `AGENTS.md` sits in a `shared` region — `<!-- SPEC-TREE:shared {name} -->` … `<!-- /SPEC-TREE:shared {name} -->`, present in both files under the same name. `/update-instruction-block` keeps a `shared` region in sync by taking the git-more-recent side; it never merges the two bodies.

---

## When to Invoke Skills

### Before product-content access -> `/understand`

**BLOCKING REQUIREMENT**

Require a live `<SPEC_TREE_FOUNDATION>` marker before directly reading, searching, listing, or changing anything under `spx/` or any source or test file. Invoke `/understand` when the marker is absent. This includes repository-content access through Read, Edit, Write, Glob, Grep, `rg`, `grep`, `find`, `cat`, `sed`, and Git commands that emit file contents or patches.

`spx session` operations — including inspection, archive, and release — plus `spx worktree status`, `spx diagnose`, and no-patch Git status, history, and topology are exempt. Never follow paths from their output into repository content without the marker.

A compacted summary, session file, statement that `/understand` ran, or read of the skill file does not prove the foundation is live. After every compaction, require `/understand` again before the next product-content access.

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

### Before tests, evals, builds, or validation -> `/wait-for-load`

🛑 **STOP TRIGGER — Before any test, eval, build, or validation command, ALWAYS invoke `/wait-for-load`.**
**ALWAYS** wait for `ready: true`, then run the selected command unchanged.
**NEVER** use host load to reduce scope, workers, limits, deadlines, or verification.

### When shipping work to the default branch -> `/merge` (transport dispatcher)

**BLOCKING REQUIREMENT**

Every change destined for the default branch routes through `/merge`, the transport dispatcher — it classifies the changeset, selects the transport, and delegates. `/merge` reads `spx/local/merging.md` as a repo-local overlay **when that file is present**; the overlay is optional, so its absence is normal and not a blocker — `/merge` applies the default lifecycle. `spx/local/merging.md` is the one place repository-specific merge behavior belongs: never infer the transport from other docs when it is absent, and never edit this generated instruction block to change merge behavior — invoke `/merge` and let the lifecycle apply the defaults. The four authority gates, the delivered-value boundary, and the finding-disposition rule are transport-neutral and live in `/merging-standards`.

## Stop Triggers

Default-branch work is complete only when it reaches the default branch on origin through `/merge` — passing validation, tests, review, or audits is progress, not a stopping point, and an accepted proposal ("yes", "go", "do it") authorizes the whole lifecycle, not a pause. Each trigger below resolves the same way: finish the remaining independent work, then continue through `/commit-changes` and `/merge` until the change reaches the default branch on origin or an explicit lifecycle gate stops.

🛑 **About to summarize after edits, validation, tests, review, or audits passed** — do not conclude. Ensure the work is committed on a local branch, then drive `/merge`.

🛑 **About to report blocked, wait, or ask a question** — first do every action that does not need the answer: edits, verification, branch setup, commit, review. A blocker exists only when all three hold:

- the immediate next action cannot proceed without the operator or an external-state change;
- the local branch already holds every change makeable without the answer;
- the applicable gates have run or produced concrete failing evidence.

🛑 **About to finish on a detached HEAD or stop at a fresh commit** — `git status --short --branch` reporting `## HEAD (no branch)`, or a new local commit, is not an endpoint. Create or switch to a local branch preserving the worktree changes, then continue through `/merge` unless the user explicitly limited the task to local-only work.

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

## Mutation Status Updates

Before proposing or performing a repository mutation, name:

- the exact target path, PR number, branch ref, or command target;
- the intended action;
- why the action is local enough or gate-authorized enough to proceed;
- the next validation command, review, audit, check wait, or merge gate the action feeds.

Avoid shorthand such as "config patch", "direct patch", "fix the PR", or "ship it path" when the exact file, PR state, or command is known. A terse user prompt such as "check", "continue", or "ship it" still gets the live state first: full head SHA when a PR exists, current-head review state, required-check state, deployment-readiness and release-readiness rules, and the next autonomous action.

## Quick Reference: Skills and Agents

Skills run in the main conversation. Agents preload the skill and run autonomously as subagents in a separate context. Audit agents return structured verdicts; changeset reviewer agents return the raw review journal token for the main conversation to inspect and process through the governing review workflow. **ALWAYS run an audit through its agent** — the separate context keeps the verdict free of the main conversation's bias — and dispatch agents in parallel when auditing multiple targets.

<!-- harness:codex -->

**Read named files yourself.** Always read explicitly named files in the main conversation. Never use subagents to read, summarize, inspect, or interpret skills or skill references, AGENTS.md instruction files, files named by the user, or files referenced by skills or instruction files.

- ALWAYS spawn subagents exactly for the named verifier or reviewer roles authorized below, or when the operator explicitly asks for subagent delegation.
- NEVER spawn agents merely because they are discovered, available, or plausibly useful.

**Run auditor and reviewer work in a subagent, never the main thread.** This is a standing user instruction to use the runtime's exposed typed-subagent spawn capability (`multi_agent_v1.spawn_agent` when that identifier is available) for the named verifier and reviewer roles it lists. Treat those cases as the user explicitly asking for subagents spawned in parallel. When an audit or review is called for, spawn the matching subagent exposed by the current runtime — `changes-reviewer` for a changeset review, `implementation-auditor` for implementation audits, `adr-auditor`, `pdr-auditor`, `spec-auditor`, `test-evidence-auditor`, or `eval-evidence-auditor` for the artifact in scope. When the installed plugin set exposes the instructions-owned `skill-auditor` or `subagent-auditor` roles, use those matching subagents for skill-content and subagent-configuration audits. Act only on the result the subagent returns: audit agents return verdicts or verification-run projections, while `changes-reviewer` returns the raw review journal token to inspect and process through the governing review workflow. Do not ask the operator to confirm whether to launch an exposed required named subagent. Harness approval prompts are separate: if the tool itself asks for approval, answer that prompt through the harness approval flow. The main Codex conversation must NEVER run a verification skill (audit or review) itself to avoid biasing the result. If an exposed required subagent cannot be spawned or does not finish, the gate is blocked. Continue the deterministic verification (test and validate) and then provide the operator with a precise description of what was tried and how it failed.

**Already-dispatched verifier boundary.** Apply the typed-spawn rules above only in the main authoring conversation. Once running as a named verifier or reviewer, treat the current context as the required isolation and execute the configured audit or review skill directly. NEVER search for or spawn another verifier, use `tool_search` to discover multi-agent tools, or invoke `codex exec`, `claude`, `pi`, or another agent CLI. Missing nested-verifier tools is expected inside the dispatched verifier and does not block direct execution.

**Use the exposed multi-agent tool schema exactly.** The examples below use the `multi_agent_v1` identifiers emitted by this Codex harness. When the runtime exposes different identifiers, discover the equivalent typed spawn, wait, and close capabilities and preserve the same fields and result contracts. The initial task goes in `message`; use `items` only when the task must pass structured mentions. Omit `fork_context`, `model`, `reasoning_effort`, and `service_tier` for the typed verifier and reviewer agents. Full-history forks are incompatible with changing `agent_type` in this harness, and the named verifier/reviewer roles already carry their own model settings. Store every returned agent id verbatim. After spawning, continue only non-overlapping work while the subagent runs, then collect the result with the exposed wait capability. Close every spawned agent with the exposed close capability immediately after its final result is collected; completed agents remain open until closed and can interfere with future spawns.

### Subagent lifecycle — preserve every handle and close every thread

Treat every spawned subagent as an owned resource. Maintain a registry in the main conversation containing its exact `agent_id`, role or task, and lifecycle state. Record a successful spawn's returned id before issuing another spawn or making any unrelated tool call. Preserve every unresolved registry entry across interruption and compaction.

**Acquire handles sequentially while agents execute concurrently.** Call `multi_agent_v1.spawn_agent` once per tool call. Several sequential spawn calls may occur within one main-agent tool-call sequence before control returns to the operator, and every agent already spawned may run concurrently while later calls are issued. NEVER place multiple spawn calls in `Promise.all`, another fail-fast combinator, or one parallel tool-call batch: one rejected call can suppress successful sibling results and lose their ids even though those agents remain open. Respect the runtime's configured `agents.max_threads` limit; NEVER hard-code a maximum such as eight and NEVER fill capacity with agents that are not required.

Before each spawn sequence, reconcile the registry: preserve any final results already returned, close their agents, and close work that has been abandoned or superseded. If a spawn fails, stop issuing new spawns, retain every id already acquired, and collect or close those known agents before retrying. A failed individual spawn yields no id for that call and does not erase ids returned by earlier calls.

**Collect, preserve, then close.** Use `multi_agent_v1.wait_agent` with only exact ids from the registry. A timeout with no final status is non-final. When the result remains required, wait again; when the work is explicitly abandoned or superseded, close the agent. For every final status, preserve the complete final message, structured verdict, or journal token first, then immediately call `multi_agent_v1.close_agent` for that id and mark it closed in the registry. A notification, pending handle, or open id is never a final result.

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

Wait once for one or more spawned agents. Use a 10-minute timeout for subagents acting on individual files (e.g. `implementation-auditor`, `spec-auditor`). Use a 30-minute timeout for subagents acting on an entire changeset (`changes-reviewer`):

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

In the main authoring conversation, if `wait_agent` is not exposed, discover the multi-agent waiting tool with `tool_search`, then call the discovered wait tool. Accept a subagent notification only when the harness delivers it while the main conversation is working or waiting; do not choose notifications as the planned result-collection mechanism. Do not use web search, time lookup, shell polling, or `request_user_input` or any other tools as a substitute for result collection.

**Result collection for verifier and reviewer agents.** The exposed typed wait capability (`multi_agent_v1.wait_agent` in the examples below) is the planned result-collection mechanism. Read its returned JSON, keyed by the spawned subagent id under `status`. A timeout returns an empty `status` object and is not a result. A final status for the target id is the verifier result; when that final status carries a final message, that message is the verifier or reviewer output. Do not infer success from a subagent notification, a pending handle, or an open subagent id.

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

After a successful `changes-reviewer` result, invoke the `spec-tree:project-run-journal` skill and use its `render_review_run.py <run-token>` helper to inspect the sealed review run. That helper calls `spx journal render --type review --run <run-token>`, resolves a not-found current-scope miss through `spx journal list --type review --sealed sealed --limit 200`, re-renders with the listed branch slug when exactly one sealed run matches the token, reads the sealed event prefix, and prints the review status, full head/base identity, scope coverage, and finding counts. Treat this as journal inspection; the sealed prefix remains the only review result.

**Codex blocked-result rule.** If `wait_agent` returns an error, `not_found`, timeout with no final status, usage-limit failure, model-capacity failure, or any final message that is not a raw review journal token, the review gate is blocked. Record the exact agent id, tool result, and blocking reason. Do not publish, merge, or mark the gate passed. When repairing a finding or blocked subject, rerun deterministic verification, create a new local checkpoint commit, and review that new head; an operator-approved process exception is the only other path past the gate.

**Use raw scope only for `changes-reviewer`.** The review agent owns `spec-tree:review-changes`, severity taxonomy, scope expansion, and finding shape. Pass only the raw scope token in `message`: `HEAD` for the current worktree scope, `origin/<base>...HEAD` for a specific committed range, a branch name, or a PR reference. A `HEAD` review satisfies a gate only when the caller first confirms the worktree is clean; on a dirty tree it includes staged, unstaged, and untracked sections and is advisory.

- ALWAYS prepare the worktree first: isolate the intended changes, sync to the base using the `spec-tree:sync-base` skill when the governing workflow requires it, pass deterministic verification, create a local checkpoint commit, and leave the worktree clean so the reviewer judges an exact committed head. A review over a working diff is advisory and never satisfies a gate.
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

**Use explicit prompts for audit agents.** The `message` field comes from the `multi_agent_v1.spawn_agent` schema. This instruction block owns the prompt content below for required verifier roles. Keep the prompt narrow: repository path, governed artifact paths, governing node or decision, deterministic verification state when relevant, audit task, and output shape. Do not ask the subagent to edit files.

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
    "message": "Repository: <absolute-repository-path>\nGoverning node: <full spx/... node path>\nSpec assertions: <full assertion text or exact spec file path plus assertion headings>\nTest files: <full paths to test files under the node>\nTask: Audit whether the test evidence proves the listed assertions without weakening the selected verification type or test assertion type. Return APPROVED or REJECTED. For REJECTED, list concrete findings with file paths, line numbers, evidence property affected, and required fix."
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
    "message": "Repository: <absolute-repository-path>\nSkill content: <full paths to changed SKILL.md files and changed files under references/, workflows/, templates/, scripts/, or other skill subdirectories>\nGoverning node(s): <full spx/... path(s) when known>\nDeterministic verification already run: <commands and results, or why this audit is being run before verification>\nTask: Audit the changed skill content for skill-authoring standards, agent-prompt standards, progressive disclosure, portability, voice, and structure. Return APPROVED or REJECTED. For REJECTED, list concrete findings with file paths, line numbers, governing rule, and required fix."
  }
}
```

Use this shape for subagent audits:

```json
{
  "tool": "multi_agent_v1.spawn_agent",
  "arguments": {
    "agent_type": "subagent-auditor",
    "message": "Repository: <absolute-repository-path>\nSubagent files: <full paths to changed agents/*.md files>\nGoverning node(s): <full spx/... path(s) when known>\nDeterministic verification already run: <commands and results, or why this audit is being run before verification>\nTask: Audit the changed subagent configuration for subagent-authoring standards, prompt voice, tool boundaries, model settings, skill preloads, and output contract. Return APPROVED or REJECTED. For REJECTED, list concrete findings with file paths, line numbers, governing rule, and required fix."
  }
}
```

<!-- /harness:codex -->

| User Says...                               | Skill                  | Agent                   |
| ------------------------------------------ | ---------------------- | ----------------------- |
| "Implement this outcome"                   | `/apply`               | `applier`               |
| "Create an outcome"                        | `/author`              | —                       |
| "Add an ADR"                               | `/author`              | —                       |
| "Add a new node" or "This node is too big" | `/decompose`           | —                       |
| "Move this under that"                     | `/refactor`            | —                       |
| "Check these specs"                        | `/align`               | —                       |
| "Establish evidence for this"              | `/verify`              | —                       |
| "Write tests for this"                     | `/verify`              | —                       |
| "Start the TDD flow"                       | `/apply`               | `applier`               |
| "Audit this PDR"                           | `/audit-pdr`           | `pdr-auditor`           |
| "Audit this ADR"                           | `/audit-adr`           | `adr-auditor`           |
| "Audit test evidence"                      | `/audit-tests`         | `test-evidence-auditor` |
| "Audit eval evidence"                      | `/audit-eval-evidence` | `eval-evidence-auditor` |
| "Audit this spec node"                     | `/audit-specs`         | `spec-auditor`          |
| "Diagnose the spx environment"             | `/diagnose`            | —                       |
| "File a follow-up in a dependency queue"   | `/issue`               | —                       |

Per-language code, architecture, and test audits ship as `audit-{lang}-{code|tests|architecture}` skills that generic artifact-type auditors compose for the language in scope. There is no per-language auditor agent. Dispatch `implementation-auditor` for implementation audits; it invokes the matching language concern skills automatically:

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

---

## Test Naming Convention

Test level is encoded in the filename. The `{evidence}` segment is chosen by `/test` routing from the assertion type: `scenario`, `mapping`, `conformance`, `property`, or `compliance`. Universal assertions use `mapping`, `conformance`, `property`, or `compliance`; a universal is never `scenario`. This instruction block renders only the languages recorded in its opening `<!-- SPEC-TREE v{version} langs:{list} -->` marker; `/update-instruction-block` re-renders from the installed template when the methodology advances.

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

An explicit request to inspect, archive, or release identified session documents routes directly through the corresponding `spx session` command as operational-state management. Reserve `/handoff` for closing active work through reflection, persistence, continuation disposition, and claimed-session accounting. Direct session operations require `/understand` only before following their output into `spx/`, source, or test content.
