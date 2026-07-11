<!-- SPEC-TREE v0.23.0 langs:python -->

# Spec Tree Instructions

These instructions explain WHEN to invoke spec-tree skills for this product. They are a **router** — the skills contain the HOW.

**Read this entire file before you act.** This managed router block is only the first section of the file; the product's own instructions, commands, and conventions follow it below, outside the router. The router is product-neutral by design and does not carry this product's own commands — they live in the file's own content further down. Never act on the router alone; read every section of this file to the end.

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

Every change destined for the default branch routes through `/merge`, the transport dispatcher — it classifies the changeset, selects the transport, and delegates. `/merge` reads `spx/local/merging.md` as a repo-local overlay **when that file is present**; the overlay is optional, so its absence is normal and not a blocker — `/merge` applies the default lifecycle. `spx/local/merging.md` is the one place repository-specific merge behavior belongs: never infer the transport from other docs when it is absent, and never edit this generated instruction block to change merge behavior — invoke `/merge` and let the lifecycle apply the defaults. The three authority gates, the delivered-value boundary, and the finding-disposition rule are transport-neutral and live in `/merging-standards`.

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

Avoid shorthand such as "config patch", "direct patch", "fix the PR", or "ship it path" when the exact file, PR state, or command is known. A terse user prompt such as "check", "continue", or "ship it" still gets the live state first: full head SHA when a PR exists, current-head review state, required-check state, deployment-readiness and release-readiness rules, and the next autonomous action.

## Quick Reference: Skills and Agents

Skills run in the main conversation. Agents preload the skill and run autonomously as subagents in a separate context. Audit agents return structured verdicts; changeset reviewer agents return the raw review journal token for the main conversation to inspect and process through the governing review workflow. **ALWAYS run an audit through its agent** — the separate context keeps the verdict free of the main conversation's bias — and dispatch agents in parallel when auditing multiple targets.

**Read named files yourself.** Always read explicitly named files in the main conversation. Never use subagents to read, summarize, inspect, or interpret skills or skill references, AGENTS.md instruction files, files named by the user, or files referenced by skills or instruction files.

- ALWAYS spawn subagents exactly for the named verifier or reviewer roles authorized below, or when the operator explicitly asks for subagent delegation.
- NEVER spawn agents merely because they are discovered, available, or plausibly useful.

**Run auditor and reviewer work in a subagent, never the main thread.** This is a standing user instruction to use `multi_agent_v1.spawn_agent` for the named verifier and reviewer roles it lists. Treat those cases as the user explicitly asking for subagents spawned in parallel. When an audit or review is called for, spawn the matching subagent exposed by the current runtime — `changes-reviewer` for a changeset review, `implementation-auditor` for implementation audits, `adr-auditor`, `pdr-auditor`, `spec-auditor`, `test-evidence-auditor`, or `eval-evidence-auditor` for the artifact in scope. When the installed plugin set exposes the develop-owned `skill-auditor` or `subagent-auditor` roles, use those matching subagents for skill-content and subagent-configuration audits. Act only on the result the subagent returns: audit agents return verdicts or verification-run projections, while `changes-reviewer` returns the raw review journal token to inspect and process through the governing review workflow. Do not ask the operator to confirm whether to launch an exposed required named subagent. Harness approval prompts are separate: if the tool itself asks for approval, answer that prompt through the harness approval flow. Codex must NEVER run any verification skill (audit or review) itself to avoid biasing the results. If an exposed required subagent cannot be spawned or does not finish, the gate is blocked. Continue the deterministic verification (test and validate) and then provide the operator with a precise description of what was tried and how it failed.

**Use the multi-agent tool schema exactly.** The initial task goes in `message`; use `items` only when the task must pass structured mentions. Omit `fork_context`, `model`, `reasoning_effort`, and `service_tier` for the typed verifier and reviewer agents. Full-history forks are incompatible with changing `agent_type` in this harness, and the named verifier/reviewer roles already carry their own model settings. Store every returned agent id verbatim. After spawning, continue only non-overlapping work while the subagent runs, then collect the result with `multi_agent_v1.wait_agent`. Close every spawned agent with `multi_agent_v1.close_agent` immediately after its final result is collected; completed agents remain open until closed and can interfere with future spawns.

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

If `wait_agent` is not exposed, discover the multi-agent waiting tool with `tool_search`, then call the discovered wait tool. Accept a subagent notification only when the harness delivers it while the main conversation is working or waiting; do not choose notifications as the planned result-collection mechanism. Do not use web search, time lookup, shell polling, or `request_user_input` or any other tools as a substitute for result collection.

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
    "message": "Repository: <absolute-repository-path>\nScope: <base>..<head> committed changeset scope\nLive file list: none for a gating audit; full modified and untracked paths only for an advisory pre-commit audit\nGoverning node(s): <full spx/... path(s)>\nDeterministic verification already run: <commands and results>\nTask: Run the implementation audit through spx verification run. Return the run token and rendered projection, or the exact blocked spx verification command."
  }
}
```

**Codex `implementation-auditor` output contract.** A successful final message carries the raw `spx verification run` token and rendered projection, without a competing prose verdict envelope. Treat the projection's `terminalStatus` as authoritative: `approved` passes the implementation-audit gate and `rejected` requires repair. A missing token or projection, a terminal status outside that vocabulary, or an exact blocked SPX command leaves the gate blocked.

**Committed gate subject.** A gating implementation audit runs only after deterministic verification passes and the subject is committed locally. A run carrying a live modified or untracked file list is advisory and cannot satisfy an apply or merge gate.

**Full deterministic gate ordering.** When the repository requires `just check-full` or another full deterministic bundle, run it only after all applicable evidence auditors, implementation audits, and changeset review have converged on the same clean committed head. Never launch it before agentic verification, from inside an agent, or concurrently with another heavy command. Any later change invalidates the full-gate result and requires the affected agentic checks to converge again before rerunning the full bundle.

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

| User Says...                               | Skill                  | Agent                   |
| ------------------------------------------ | ---------------------- | ----------------------- |
| "Implement this outcome"                   | `/contextualize`       | —                       |
| "Create an outcome"                        | `/author`              | —                       |
| "Add an ADR"                               | `/author`              | —                       |
| "Add a new node" or "This node is too big" | `/decompose`           | —                       |
| "Move this under that"                     | `/refactor`            | —                       |
| "Check these specs"                        | `/align`               | —                       |
| "Write tests for this"                     | `/test`                | —                       |
| "Start the TDD flow"                       | `/apply`               | `applier`               |
| "Audit this PDR"                           | `/audit-pdr`           | `pdr-auditor`           |
| "Audit this ADR"                           | `/audit-adr`           | `adr-auditor`           |
| "Audit test evidence"                      | `/audit-tests`         | `test-evidence-auditor` |
| "Audit eval evidence"                      | `/audit-eval-evidence` | `eval-evidence-auditor` |
| "Audit this spec node"                     | `/audit-specs`         | `spec-auditor`          |
| "Diagnose the spx environment"             | `/diagnose`            | —                       |
| "File a follow-up in a dependency queue"   | `/issue`               | —                       |

Per-language code, architecture, and test audits ship as `audit-{lang}-{code|tests|architecture}` skills that generic artifact-type auditors compose for the language in scope. There is no per-language auditor agent. Dispatch `implementation-auditor` for implementation audits; it invokes the matching language concern skills automatically:

| User Says...            | Skill (composed)             | Composing agent          |
| ----------------------- | ---------------------------- | ------------------------ |
| "Audit this code"       | `/audit-python-code`         | `implementation-auditor` |
| "Audit ADRs for Python" | `/audit-python-architecture` | `adr-auditor`            |
| "Audit these tests"     | `/audit-python-tests`        | `test-evidence-auditor`  |

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

Sessions are shared across every worktree. Each session must be handed off via `/handoff` so it can be resumed from any other worktree: the handoff leaves the worktree clean and persists all state on origin. Propose a handoff when the session's goal is met or the work must pause; resume one with `/pickup`. When a claimed session is complete and should leave the active queue, close it through `/handoff` or `/handoff --no-session` so claimed-session accounting archives it. To return a wrongly claimed session to the shared queue instead, run `spx session release <session-id>`.

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

- `.claude-plugin` for Claude Code plugins, commands, and agents
- `.codex-plugin` for Codex skill bundles

Shared plugins ship both manifests where supported.

## Agent Harness Guidance

This file is shared by Claude Code and Codex. Follow the rule's intent with the tool names available in the current harness.

| Capability                       | Claude Code                      | Codex                                        |
| -------------------------------- | -------------------------------- | -------------------------------------------- |
| Structured question with choices | `AskUserQuestion`                | `request_user_input`                         |
| Read files                       | `Read`                           | `exec_command` with `rg`, `sed`, or `cat`    |
| Edit files                       | `Edit` / `Write`                 | `apply_patch`                                |
| Search files                     | `Glob` / `Grep`                  | `exec_command` with `rg` or `rg --files`     |
| Read-only research agents        | `Task` / configured subagents    | `spawn_agent` only when explicitly requested |
| Product plugin settings          | `.claude/settings.json`          | `.codex/config.toml`                         |
| User-scope plugin registration   | `~/.claude/` via `claude plugin` | `~/.codex/config.toml` via `codex plugin`    |

When these instructions say `AskUserQuestion`, Codex must use `request_user_input`. When these instructions say `Read`, `Edit`, or `Write`, Codex must use its local shell and patch tools in a way that preserves the same behavior.

## Marketplace Methodology

This file covers repository rules that apply across both agents.

Claude Code-specific methodology — skill structure patterns, testing philosophy, research on skill activation — lives in [`methodology/`](methodology/CLAUDE.md). Read [`methodology/CLAUDE.md`](methodology/CLAUDE.md) when creating or restructuring skills, writing tests, or tuning skill descriptions for reliable activation.

Spec-tree methodology rules (node types, states, assertion types, ordering) live in `src/plugins/spec-tree/skills/understand/references/` and are authoritative over `methodology/`.

## Historical Context

The Outcome Engineering methodology has evolved through three generations. Only the current one is active.

| Generation              | Plugin       | Directory     | Node types                     | Context skill              | Status      |
| ----------------------- | ------------ | ------------- | ------------------------------ | -------------------------- | ----------- |
| 1st (Jul 2025–Jan 2026) | `specs`      | `specs/work/` | `capability → feature → story` | legacy context entry point | **Legacy**  |
| 2nd (Jan–Mar 2026)      | `spx-legacy` | `spx/`        | `capability → feature → story` | legacy context entry point | **Legacy**  |
| 3rd (Mar 2026–)         | `spec-tree`  | `spx/`        | `enabler`, `outcome`           | `/contextualize`           | **Current** |

**What changed across generations:**

- **1st → 2nd**: Moved from `specs/work/` to `spx/`, adopted durable map principles and sparse integer ordering. The three-level hierarchy (`capability/feature/story`) remained.
- **2nd → 3rd**: Replaced the fixed three-level hierarchy with two recursive node types (`enabler`, `outcome`) that nest to arbitrary depth. Replaced the second-generation context entry point with `/contextualize`. Merged the separate `spx` and `code` plugins into `spec-tree`.

Historical plugin implementations are pruned from this repository. The history table explains why old product directories or installed plugins may still appear outside this checkout.

## Critical Rules

- ⚠️ **NEVER answer ANY question without invoking at least one skill first** - If the question touches testing, specs, code, architecture, or any topic covered by a skill, invoke the relevant skill BEFORE answering. Skills are the authoritative source — not grep results, not existing files, not your training data. See the plugin catalog in [`README.md`](README.md#plugins) for the available skills.
- ⚠️ **NEVER write code without invoking a skill first** - See the plugin catalog in [`README.md`](README.md#plugins) for language-specific coding skills.
- ⚠️ **NEVER read, analyze, or propose changes to product work without invoking `/understand` then `/contextualize` first** - The trigger is *engaging with product state*, not editing one enumerated artifact type. Before you read any file under `spx/`, `src/plugins/`, or `outcomeeng*/` **to analyze, propose, or change product work** — a spec, a decision record, a coordination note (`PLAN.md`/`ISSUES.md`), an authored skill/command/agent/template, or implementation code governed by a node — invoke `/understand` (once per session) to load the methodology foundation, then `/contextualize <full-path>` on each involved node to load its ancestry (product → decisions → ancestors → target) deterministically. Locating the target path with `ls`/`Glob` is fine; `/contextualize` performs the authoritative read. **NEVER form a judgment, proposal, or edit from a bare `Read` before the methodology and the node's ancestry are loaded** — that is exactly what made `spx/ISSUES.md` look like "just a coordination note" instead of spec-tree work. Reading the root agent guide (`AGENTS.md` / `CLAUDE.md`) to learn the rules is the sole exemption — it is the only file readable before `/understand` loads. Concretely, this pair is required before implementing work on an existing node, editing an existing spec file, cleaning or reconciling a `PLAN.md`/`ISSUES.md`, **editing an authored skill, command, agent, or template under `src/plugins/` whose behavior an `spx/` node governs** (a `SKILL.md` body is implementation that an `spx/` `[eval]` or conformance test evaluates — it counts even though no module *imports* the markdown and the file is not under `spx/`; e.g. the `manage-pr` and `review-changes` skills implement `spx/21-spec-tree.enabler/76-merging.enabler/`), or opening a PR whose diff sits inside `spx/` or imports modules tested by `spx/`. **This pair runs BEFORE `develop:create-skills` or any other authoring-mechanics skill** — editing a skill that implements a node is spec-tree work first and skill-authoring work second; reaching for `create-skills` (or its `skill-standards` router) first is the exact mistake this rule exists to prevent. The "Spec-tree navigation" section below explains how to identify the governing node from a diff, including the inverse path from an authored skill body to its node.
- ⚠️ **ALWAYS use the root managed Spec Tree instruction block before spec-tree work** - The instruction block in this root instruction file is the spec-tree skill router. Read it before working with files under `spx/` or applying spec-tree lifecycle rules from the product-owned root instruction content.
- ⚠️ **NEVER create a spec-tree artifact without invoking `/author` first** - Before creating a product spec, ADR, PDR, enabler, or outcome, invoke `/author`. The skill carries the templates, the index-assignment procedure, and chains into `/contextualize` on the parent directory so sibling enumeration prevents index collisions. Do not invoke `/contextualize` directly on a not-yet-existing node path — it will abort with "Target path not found"; the bootstrap-mode entry point belongs to `/author`.
- ⚠️ **ALWAYS read harness guide files in subdirectories** - When working with files in `spx/`, or any other directory, read that directory's active harness guide first if it exists: `CLAUDE.md` in Claude Code, `AGENTS.md` in Codex.
- ⚠️ **Skills are ALWAYS authoritative over existing files** - When a skill template prescribes a structure (e.g., Architectural Constraints table), follow the skill — not patterns found in existing spec files. Existing files may contain non-standard sections added before skills existed. Never infer framework conventions from existing files; always read the skill.
- ⚠️ **NEVER maintain backward compatibility** - When rewriting a module, replace it entirely. No legacy aliases, no re-exports of old names, no shims. Update all imports across the codebase to use the new API.
- ⚠️ **NEVER reference specs or decisions from code** - No `ADR-21`, `PDR-13`, or similar in code comments or docstrings. Specs are the source of truth; code should not duplicate or point to them. Review and audit enforce this convention; no automated lint rule covers the shorthand form. (The separate `reference-portability` gate step catches real-digit `spx/<digits>-…` node paths and product roots in shipped `src/plugins/` content, not bare `ADR-21` shorthand.)
- ⚠️ **No docstring-length or "no comments" rule exists** - The spec-reference rule above is the *only* prohibition on code comments and docstrings. Multi-line module/function docstrings and explanatory comments that capture non-obvious invariants are expected (clarity over brevity); peer code carries them — `outcomeeng/validation/reference_portability.py` opens with a multi-paragraph module docstring. A review finding that cites a CLAUDE.md/AGENTS.md rule such as "default to writing no comments", "one short line max", or "never multi-paragraph docstrings/multi-line comment blocks" is **unbacked** — no such rule exists in this repository (`grep` it and see). Refute such a finding on the thread; do **not** collapse docstrings or comments to satisfy it. (A reviewer may be importing a personal-scope style preference that does not govern this repo.)
- ⚠️ **Depend on an `spx` CLI capability only after it is PUBLISHED and the floor is advanced** - The shipped skills and their tests invoke the `@outcomeeng/spx` CLI; a skill or test that assumes a capability merged only to spx `main` (not yet published to npm) ships a contract the consumer's installed CLI cannot honor, and surfaces as an opaque CI test failure or a consumer regression. Merged-to-spx-main is **not** "available." A capability is available only when (1) an `@outcomeeng/spx` release containing it is published to npm, (2) `REQUIRED_SPX_VERSION` in `outcomeeng/validation/spx_version.py` is advanced to that version, and (3) `SPX_VERSION` in `.github/workflows/check.yml` is bumped to a published version at or above the floor. The `spx-version` gate step enforces pin ≥ floor, and the pin can only reach a published version — so a dependency on an unpublished capability fails `just check-full` in CI with a named gap, governed by `spx/13-infrastructure.enabler/21-test-infrastructure.enabler/15-ci-gate.adr.md`.
- ⚠️ **NEVER manually delete untracked files** - use `just clean` (`git clean -fdX`) to remove gitignored caches such as `.DS_Store` and `__pycache__`; it does not touch non-gitignored untracked files or empty directories, and git-untracked empty dirs are invisible to version control and harmless, so leave them be
- ⚠️ **NEVER use general-purpose agents to create or modify ANY files** - Agents (subagents, background agents) must ONLY be used for read-only research: searching code, reading files, running read-only commands. ALL file creation, editing, and writing MUST be done by the `applier` agent (see `spec-tree` plugin) or remain in the main conversation context
- ⚠️ **The methodology is multi-language** - Skill content shipped under `dist/` that names a test filename pattern, an import syntax, or any other language-specific token is wrong unless framed per-language with a cross-reference. Authoritative conventions live in `spx/15-test-language.adr.md` for this product and in each language plugin's `{language}-test-standards` skill for consumers. Never write `test_*.py` (or any single-language pattern) into a skill body that ships to consumer projects — the file under audit may be a `.test.ts`, a `.rs` test module, or whatever the consumer's language plugin declares.
- ⚠️ **Authored skill content names "Claude" as the subject — never strip it to satisfy the self-reference policy** - Per `develop`'s `agent-prompt-standards` `<voice>` rule, skill and methodology content drops the subject (imperative mood) by default and names **"Claude"** for behavioral claims, tendencies, and failure modes; **"the agent"**, **"an agent"**, **"the model"**, and **"you"** are banned subjects. The `<self_reference_policy>` ban on "Claude" in generated content governs **operational artifacts only** — branch names, commit messages, PR titles and bodies, review comments — NOT authored skill content under `src/plugins/`. The build ships authored "Claude" verbatim to both `dist/claude/` and `dist/codex/` (no identity substitution today); other-agent targeting is a downstream replacement step, so the authored canon is always "Claude". Conflating the two — removing "Claude" from skill content because the self-reference policy forbids it in commits — is a real, recurring error.
- ⚠️ **Editing skill content requires the skill auditor as a gate** - After editing any `SKILL.md` or skill reference under `src/plugins/`, run `develop:skill-auditor` (or `/audit-skills`) before shipping. The `changes-reviewer` local review and the CI `spec-tree-review` do NOT load the skill-authoring standards (`skill-standards`, `agent-prompt-standards`) and will not catch voice (named-subject), structure, or progressive-disclosure violations — only the skill auditor does.
- ⚠️ **NEVER weaken a spec to match code or tests** - When an audit finds an unfulfilled assertion, write the missing test or fix the implementation. The declaration governs. Removing or downgrading an assertion to make the audit pass is the exact failure mode the methodology exists to prevent.

- 🛑 **STOP TRIGGER — NEVER abbreviate a session ID, or any identity value** - A session ID is `YYYY-MM-DD_HH-MM-SS` and is reproduced **verbatim and in full** every single time — in prose, questions, commits, and tool calls. NEVER shorten it to a fragment (e.g. the `HH-MM-SS` tail, the date, or any substring): a fragment identifies nothing, is ambiguous across sessions, breaks `spx session show/pickup/archive` lookups, and obscures the user's comparison against the source. The same rule binds every agent-surfaced identity value — commit SHA, run ID, `owner/repo`, host account, agent-session ID: copy it exactly from its source, never paraphrase or truncate it (this is the product-level verbatim-identity compliance rule in `spx/outcomeeng.product.md`). If a value is long, paste the whole value; do not "tidy" it.

- ✅ **Use this repo's command surface exactly** - Skills decide when validation, tests, review, audit, merge, and marketplace sync are required. `AGENTS.md` records this repo's concrete command forms and how to pass the file set:
  - `[test]` evidence: `just test <pytest-target>...`. Pass co-located spec test files, node test directories, or pytest node IDs, for example `just test spx/21-spec-tree.enabler/76-merging.enabler/tests/test_merge_gate_policy.mapping.l1.py`. When a source file under `outcomeeng/`, `outcomeeng_testing/`, `outcomeeng_evals/`, or `src/plugins/` changes, pass the spec test file(s) or node test directory that exercise it; do not pass implementation paths as if they were tests. Never run bare `pytest`.
  - Verbose failing test rerun: `just test-v <same pytest-target>...`.
  - `[eval]` evidence: `just eval <eval-toml>`, `just eval-case <eval-toml> <case-id>`, or `just eval-node <node-path>`. These wrap `uv run outcomeeng-evals run`, read `plugin_dir` from `eval.toml` unless `PLUGIN_DIR` is set, and default to `MAX_BUDGET_USD=0.50`, `WORKERS=1`, and `TIMEOUT_SECONDS=120`. Do not run bare `outcomeeng-evals`; do not raise `MAX_BUDGET_USD`, `WORKERS`, or `TIMEOUT_SECONDS` without structured operator approval.
  - Spec-only or Markdown-instruction-only changes: `spx validation markdown` and `spx spec status --format json`. These commands take no changed-file list; the scope is the markdown/spec lane.
  - Markdown formatting: `just fmt <changed-markdown-file>...`. Pass every changed Markdown file that dprint formats, for example `just fmt AGENTS.md spx/local/open-pr.md`.
  - Python formatting: `just fmt-python <changed-python-file>...`. Pass every changed Python file that ruff formats.
  - Skill or plugin Markdown under `src/plugins/` or generated `dist/`: `just check-skills` and `just docs-check`. These commands take no changed-file list; they check the committed skill/catalog surfaces.
  - Selected local deterministic gate: `just check`. This automatically selects the gate steps that cover the changed paths and prints the selected steps with reasons before running them through the recipe runner.
  - Full deterministic gate: `just check-full`. CI invokes this full gate on `pull_request` and push to `main`; run it locally only when the active skill, `spx/local/merging.md`, the governing node, risk evidence, or the user explicitly requires the full gate.
  - Generated plugin trees after `src/plugins/` edits: `just build-skills`. Do not hand-edit `dist/`.
  - Generated root Spec Tree instruction blocks after instruction-block-template or distribution-render changes: `just build-skills`, then `just build-instructions`. Do not hand-edit the managed instruction blocks in `CLAUDE.md` or `AGENTS.md`; regenerate them from the rendered harness templates in `dist/`, then verify with `just instructions-check`.
  - Generated eval CI trigger paths after an `eval.toml` `owned_paths` edit: `just build-eval-triggers`. Do not hand-edit the marker-delimited `paths:` blocks in `.github/workflows/spec-tree-evals.yml`; the gate's `eval-triggers` step fails on drift.
  - Marketplace install refresh after merged plugin-distribution changes: `just sync-marketplace <previous-main-ref>` from the marketplace-source worktree, as directed by `spx/local/merging.md`.
- 🛑 **STOP TRIGGER — NEVER raise command expense ceilings without explicit operator approval** - Command defaults are authority for cost-bearing and quota-bearing runs. Do not add or increase flags, environment variables, or config values that raise spend, quota use, hosted minutes, paid API usage, token budget, worker parallelism, retry count, timeout, or external-service capacity without structured operator approval in the same turn. Examples include `--max-budget-usd`, model/API budget caps, worker or parallelism counts, retry limits, hosted-runner minutes, and paid-provider switches. If a command fails because the default ceiling is too low, stop and ask with `request_user_input`, naming the exact failed command, the blocked ceiling, the proposed new ceiling, and a pause/inspect option.
- ✅ **Use the Justfile as this repo's command interface** - Use `just --list` / `just help` only to confirm exact recipe spelling after a governing instruction has selected the command class; do not use recipe discovery to choose an independent validation strategy. Repository-local Python modules (`python3 -m outcomeeng.*`, `uv run python -m outcomeeng.*`, and similar module invocations) run through `just` recipes only; inside the `Justfile`, those invocations are recipe implementation details. If a needed repository operation exists only as a Python module, add or fix the narrow Just recipe first, then run the recipe. Plugin-shipped skill scripts are different: when an active skill instructs a direct `python3 "${CLAUDE_SKILL_DIR}/scripts/..."` command, run that exact portable skill script. To understand a recipe, inspect `Justfile` and the underlying source with read-only tools; execute through `just`.
- ✅ **When uncertain, ASK STRUCTURED QUESTIONS. Never guess implementation patterns, test methodology or requirements.**
- ✅ **ALWAYS USE the harness structured-question tool for questions with predefined options.** Claude Code uses `AskUserQuestion`; Codex uses `request_user_input`. Do NOT use structured questions for open-ended questions where the user needs to provide free-form context — ask in plain text instead.
- ✅ **When you are wrong, KEEP ASKING STRUCTURED QUESTIONS. Never assume that you are bothering the user. As long as you are thinking deeply and asking high-leverage questions, you are doing the right thing.**
- ✅ **Dog-food platform features in skills** - When you discover an undocumented Claude Code capability (e.g., `skills:` field in subagents), check whether our skills teach it and update them if not
- ⚠️ **Spec-only validation stays on the spec lane** - When the change only adds or edits specs, decisions, EXCLUDE entries, or Markdown instructions, use the spec-only command pair in this repo's command surface above. Do not run `spx validation all`, install Node dependencies, or run ESLint/TypeScript validation unless JavaScript/TypeScript source, package manager files, validation config, or the validation pipeline changed, or the user explicitly asks for the full gate.

## Process hygiene

This harness spawns helper processes — a periodic `pgrep` to monitor background tasks, plus a shell and its children for every Bash call — and does not reliably reap them. A construct that creates many short-lived children (a poll loop), a long-lived child the monitor keeps polling (`gh run watch`, a backgrounded `sleep`, an idle keep-alive command), or several heavy process trees running at once will exhaust the per-user process limit: `posix_spawn` then returns `EAGAIN`, the monitor's `pgrep` keeps failing, and the agent is force-killed. The leak is not fixable here, so the rules below keep agents from triggering it. They apply with the tool names of the current harness — Codex's `exec_command` is the equivalent of Bash, and so on.

### Waiting and re-checking never use shell polling

No `while`/`until` poll loop. No `gh run watch`, in any form. No `sleep` to wait or pace work — foreground *or* backgrounded, on its own or in a loop. For GitHub PR checks inside the merge lifecycle, the exact wait command is:

```bash
gh pr checks <pr-number> --watch --fail-fast --interval 30
```

Run it as the active wait command. Do not append `&`, do not wrap it in a loop, and do not substitute `gh run watch`. After it exits, inspect the terminal check result, then run one full merge-gate inspection before acting: PR state, check rollup, PR-level comments, formal reviews, and review-thread comments. The foreground watcher exception applies only to `gh pr checks` inside the PR lifecycle.

For non-PR waits where no process needs to stay open, use the runtime timer or automation facility instead of shell polling. The scheduled prompt must name the repository, branch or PR, current thread purpose, and exact state to inspect.

If an earlier turn left a `sleep` or a poll loop running, identify it and terminate it by PID before doing anything else.

### Background commands: one at a time, short-lived, never a keep-alive

Every backgrounded command is a process the monitor `pgrep`s on a timer. Run one at a time, only when the work genuinely must continue across a wait, and only when it will exit on its own. Never start a background command whose job is to "stay alive" — a pile of monitored processes (or one that never exits) is the `pgrep` storm itself.

### Heavy subprocess trees: sparingly, serially, load-aware

`just check-full`, a full `pytest` run, `uv run …`, and similar each fork dozens of children. Before launching one, read `uptime` and compare the sustained loadavg (the 5- and 15-minute figures) to the host's core count (`nproc`, or `sysctl -n hw.ncpu` on macOS): if loadavg exceeds it the machine is overcommitted — defer rather than pile on. Never run two heavy commands concurrently. Run the targeted local gate first; reserve `just check-full` for CI parity or explicit full-gate requirements.

### Other forks add up

- Don't spawn subagents you don't need — each is its own process tree.
- Redirect a long-running command's output to a file (`> /tmp/check.log 2>&1`) and read it in a separate call, rather than piping through `grep`/`tail`/`head` — the pipeline holds extra processes and file descriptors open for the command's lifetime.
- Search patterns that contain backticks, `$()`, `!`, or shell metacharacters must be single-quoted or passed as fixed strings (`rg -F`) so the shell never performs command substitution while composing a read-only search.

## Plugin Portability Constraints

Plugins from this product are installed into consumer projects that share none of this repository's tooling. When a skill or agent invokes a script that ships inside a plugin, the script runs against the consumer's environment — not against this repo's `uv`, `pyproject.toml`, or `outcomeeng_*` packages.

Authors of skills, agents, and the scripts they invoke must assume:

- ⚠️ **Only the installed plugin tree is guaranteed present.** Consumer checkouts do not contain `src/`, `dist/`, `outcomeeng/`, `outcomeeng_evals/`, `outcomeeng_testing/`, `spx/`, or any other top-level directory from this repo. Anything a plugin script needs at runtime must render into that plugin's own generated runtime tree under `dist/claude/` and `dist/codex/`.
- ⚠️ **`python3` only — no `uv`.** Skill content invokes scripts via `python3 "${CLAUDE_SKILL_DIR}/path/to/script.py"` — the skill loader substitutes the path before the agent sees it. Hooks (in `hooks/hooks.json`) and MCP server configs use `${CLAUDE_PLUGIN_ROOT}` instead, since they have no skill directory. Agent definition files (under `agents/`) get neither variable substituted in the prompt body and `${CLAUDE_PLUGIN_ROOT}` is not a Bash environment variable, so agents must reach `scripts/` only by invoking a skill that resolves the path. **Shipped scripts support the two most recent Python feature releases (currently 3.14 and 3.13), with the older as the floor (3.13)**, per `spx/12-shipped-scripting.adr.md`. Use a managed interpreter (Homebrew or equivalent), never the system macOS Python, which lags years behind (macOS 26 ships 3.9). Scripts may use `StrEnum`, `tomllib`, exception groups, `type` aliases, and other features the floor provides without conditional fallbacks; consumers on older Python must upgrade. The linter and type-checker that govern shipped scripts are pinned to the floor (currently 3.13) so a shipped script never uses a feature the floor lacks. No `uv run`, no `pip install`, no project-scoped virtualenv.
- ⚠️ **Stdlib only.** No `click`, no `pydantic`, no third-party JSON Schema, no `tomllib`-via-package. `argparse`, `json`, `dataclasses`, `enum`, `pathlib`, `subprocess`, `sys`, `typing` — that's the toolbox. Anything richer must be vendored or replaced.
- ⚠️ **No on-the-fly dependency installation.** Skills must not run `pip install`, `uv pip install`, `npm install`, or any other package fetch as part of their normal flow. Consumers approve plugin installation once; runtime side effects must not include further installations.

The `outcomeeng_*` Python packages in this repo are part of the product's own toolchain (validation, distribution, eval harness) — they exist to build and test the plugins, not to be invoked by skills inside consumer projects. Code that lives outside a generated plugin runtime tree is not portable.

When a skill genuinely needs richer Python machinery, the right answer is usually to write the logic in stdlib-only form, ship it inside the plugin, and document the `python3 "${CLAUDE_SKILL_DIR}/..."` invocation in the skill body.

## Read Tool Output

The `</output>` tag at the end of Read tool results is the tool's output delimiter — it is NOT part of the file content. Never treat it as a "stray closing tag" or attempt to remove it from files.

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

Every skill, agent, and command across every plugin is listed in the auto-generated catalog in [`README.md`](README.md#plugins), sourced from `.claude-plugin/marketplace.json` and the YAML frontmatter of each plugin's `SKILL.md`, `agents/*.md`, and `commands/*.md`. Run `just docs` to regenerate; `just check-full` enforces freshness in CI. Do not maintain plugin tables in this file.

## Spec Tree Methodology

The Spec Tree methodology for [Outcome Engineering](https://outcome.engineering). Three steps drive the methodology: **declare, spec, apply**. Audit gates operate within each step. See `src/plugins/spec-tree/skills/understand/references/durable-map.md` for the authoritative methodology reference.

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

`spx/` contains only specs, decision records, coordination notes, and `tests/` subdirectories. Implementation code lives outside `spx/` (in `src/plugins/`, `outcomeeng/`, generated `dist/`, etc.). The inverse navigation walks from an outside-`spx/` file in the diff, through the import graph into an inside-`spx/` test, then up to the spec assertion linking that test, then up to the containing node.

If multiple implementation files in the diff resolve to multiple nodes, take their lowest common ancestor in the tree — `/contextualize` on the LCA pulls constraining context for every descendant.

An implementation file in the diff that no test imports has no governing spec assertion — a coverage gap the PR is shipping. Specs declare; tests verify; code complies. Surface the gap; do not invent a node to load.

Per-language test conventions live in `spx/15-test-language.adr.md` (this product uses pytest with `test_<subject>.<evidence>.<level>.py`) and in each language plugin's `{language}-test-standards` skill. In a consumer repo, the consumer's spec tree and language plugin determine the conventions; the inverse-navigation procedure is the same.

## Before Making Changes

### After Adding/Modifying Skills, Agents etc.

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

- `src/plugins/` — authored skills, agents, commands, manifests, and templates. One subdirectory per plugin.
- `dist/claude/`, `dist/codex/` — generated runtime plugin trees (rebuilt from `src/plugins/` by `just build-skills`) shipped to consumer repos. The plugin catalog in [`README.md`](README.md#plugins) is authoritative for what each plugin contains; this file does not duplicate it.
- `spx/` — this product's spec tree (durable map). The managed Spec Tree instruction block in this root file is the skill router. Per-node `local/` holds product-specific skill overlays.
- `outcomeeng/`, `outcomeeng_testing/`, `outcomeeng_evals/` — this product's Python toolchain (validation, distribution, eval harness) and its test infrastructure. Not portable to consumer projects; do not import from inside any plugin.
- `.claude-plugin/marketplace.json` — Claude Code marketplace catalog (one entry per shipped plugin).
- `.agents/plugins/marketplace.json` — Codex marketplace catalog (mirror of the above).
- `.spx/` — gitignored operational files (sessions, audit state).
- `.claude/settings.json`, `.codex/config.toml` — product-scoped harness settings, committed for collaborators.
- `AGENTS.md` (this file), `CLAUDE.md` (harness-specific copy) — repo-level instruction surfaces.

For the contents of any plugin or `spx/` subdirectory, run `ls` or read the catalog. The authored directory layout under each plugin follows the conventions in `src/plugins/develop/skills/`.

## Git workflow

### Autonomy

The managed Spec Tree instruction block in this root file is the skill router for spec-tree work. For any change destined for the default branch, invoke `/merge`; it classifies the changeset, reads `spx/local/merging.md` when present, selects the transport, and delegates to the transport skills. Do not reimplement transport selection, gate predicates, review disposition, base-sync, or PR management from the product-owned root instruction content.

The agent never invokes `git commit`, `git push`, `gh pr create`, or `gh pr merge` outside the governing skill flow. The only permitted direct git/GitHub command forms are those an active skill or this repository command section names exactly.

The autonomy does **not** cover blind force-push (`git push --force`), force-push of a shared or protected branch, branch deletion outside the merge flow, skipping pre-commit hooks (`--no-verify`), skipping commit signing, or any action explicitly forbidden by the Git Safety Protocol or `<self_reference_policy>`. Those require explicit human instruction in the same turn. The guarded `--force-with-lease` push that `/manage-github-pr` performs for its own PR branch after base-sync is part of the skill flow.

### Lifecycle

The lifecycle authority is: the managed Spec Tree instruction block routes to skills; `/merge`, `/merging-standards`, `/manage-github-pr`, `/open-pr`, and `/manage-pr` define behavior; `spx/local/merging.md` provides this product's overlay values. Root `AGENTS.md` supplies exact repository commands only where a skill asks for this product's concrete command surface.

### Marketplace Publish Commands

When an active workflow calls for the product's marketplace push wrapper, use `just push-marketplace` rather than bare `git push`; the recipe pushes first, then refreshes the local marketplace only when the pushed range changed plugin distribution files. Pass the same remote and ref arguments that would have gone to `git push`:

```bash
just push-marketplace               # git push (current branch) + just sync-marketplace
just push-marketplace origin main   # explicit remote/branch
```

Bare `git push origin main` skips the change-aware publish wrapper. For plugin distribution changes that means the local marketplace stays stale, the Codex compatibility symlinks are not created, and `validate_install` never runs.

⚠️ **NEVER run `claude plugin update`, `claude plugin marketplace update`, or `codex plugin marketplace upgrade` by hand.** These are the primitives that `just sync-marketplace` (and therefore `just push-marketplace`) already orchestrates in the right order. Running them manually risks the wrong product scope, steps out of order, or skipped post-install validation. Read the Justfile before any marketplace operation.

### How skill content reaches a session

This repository registers the `outcomeeng` marketplace with Claude Code as a **Directory source** at the repo root — `claude plugin marketplace list` reports `Source: Directory (.../outcomeeng/plugins)`, and each plugin's `marketplace.json` entry uses a relative `source: "./dist/claude/<name>"`.

**Claude** loads a plugin's skills from the source tree in place: a skill invocation reports its base directory as `<repo>/dist/claude/<plugin>/skills/<skill>/`, the `dist/claude/` of the checkout registered as the marketplace source — which in a multi-worktree setup may differ from the worktree you are editing in. When `claude plugin marketplace update outcomeeng` runs and a plugin's version has bumped, Claude repoints each running session from that source directory to a versioned snapshot under `~/.claude/plugins/cache/outcomeeng/<plugin>/<version>/`, so the session stays on one consistent version while the source `dist/` advances — the load path moves (source → cache) but the version a session sees does not change underneath it. A session can therefore show a source `dist/` path while the cache holds other versions; the snapshot it is pinned to, if any, is the one its last version-bumped update repointed it to.

**Codex** maintainer sync uses the default-branch local marketplace root for `outcomeeng`. `just sync-marketplace` repairs absent, Git-backed, or stale local Codex marketplace registration to that source, refreshes every generated Codex plugin exposed under `dist/codex` with `codex plugin add <plugin>@outcomeeng`, and then repairs compatibility symlinks so each plugin cache keeps exactly one real version directory: the Codex-reported installed version. Older in-window versions remain direct symlinks to that directory so running sessions keep resolving, and out-of-window or unmanaged plugin roots are pruned. A Git-backed Codex registration re-enters Codex's startup auto-upgrade path, which can replace a plugin cache root with only the staged current version directory and strand sessions on removed paths.

The Skill tool loads SKILL.md content into per-session memory the first time the skill is invoked and keeps it for the rest of the session, re-attaching it (truncated) after compaction. `/reload-plugins` re-indexes the marketplace and re-reads each SKILL.md from disk during registration — from the path the session resolves to, the source `dist/` or a pinned cache snapshot — so the first invocation after a reload picks up the current content.

### Smoke-testing skill changes

Work in the checkout registered as the marketplace source (`claude plugin marketplace list` shows which directory that is):

1. Edit `src/plugins/<plugin>/` and run `just build-skills` so the change lands in `dist/claude/<plugin>/`.
2. Run `/reload-plugins`. For a Claude session serving from the source `dist/` — the usual case while developing — this re-reads the edited SKILL.md directly, so no version bump or sync is needed to smoke-test a Claude change in the source checkout.
3. Invoke the skill — the first invocation after the reload loads the new content.

`just sync-marketplace` is for the cross-runtime install state, not for serving a Claude edit in the source checkout. It runs `claude plugin marketplace update outcomeeng` (which, on a version bump, repoints running Claude sessions to the versioned cache snapshot), reconciles Claude and Codex `outcomeeng` registrations to the default-branch local marketplace source, refreshes every generated Codex plugin from that source with `codex plugin add <plugin>@outcomeeng`, repairs compatibility symlinks, and then runs `validate_install` and `check-installed`. After a PR merge or direct `main` publication that changes plugin distribution files, fast-forward the **marketplace-source worktree's** `main` to the merged state and refresh installs — `git -C "$src" fetch origin main && git -C "$src" merge --ff-only origin/main`, then `(cd "$src" && just sync-marketplace <previous-main-ref>)`, where `$src` is the Directory-source path from `claude plugin marketplace list --json` (the exact steps and rationale are in [`spx/local/merging.md`](spx/local/merging.md) Post-merge marketplace sync) — then `/reload-plugins`. `sync-marketplace` must run from the source worktree: its `validate_install` reads `current_versions` from its own working directory, so running it from a feature worktree behind `origin/main` false-fails against that worktree's stale versions. Detaching the current feature worktree onto `origin/main` does not advance the source worktree the marketplace serves from.

## Missing plugins or skills

### Claude Code

When product-required Claude plugins are missing, ask the user before changing project-scoped Claude settings. Use Claude's project scope so the marketplace and enabled plugins are written to `.claude/settings.json`; commit that file so collaborators get the same plugin set.

```bash
claude plugin marketplace add outcomeeng/plugins --scope project

for plugin in develop python prose spec-tree; do
  claude plugin install "${plugin}@outcomeeng" --scope project
done
```

If an installed product-scoped plugin has been disabled, re-enable it at product scope:

```bash
for plugin in develop python prose spec-tree; do
  claude plugin enable "${plugin}@outcomeeng" --scope project
done
```

After changing plugin state in a running Claude Code session, run `/reload-plugins`.

### Codex

Codex marketplace registration is user-scoped. Ask the user before changing `~/.codex/config.toml`, then register the marketplace once:

```bash
codex plugin marketplace add outcomeeng/plugins
```

Enable plugins per product by committing `.codex/config.toml`. Keep the product list explicit so each repo gets only the plugins it needs:

```toml
[plugins."develop@outcomeeng"]
enabled = true

[plugins."prose@outcomeeng"]
enabled = true

[plugins."spec-tree@outcomeeng"]
enabled = true
```

Add language or domain plugins only for projects that use them:

```toml
[plugins."python@outcomeeng"]
enabled = true

[plugins."typescript@outcomeeng"]
enabled = true
```

If a user's global Codex config already enables a plugin that the product should keep off, add an explicit product override:

```toml
[plugins."typescript@outcomeeng"]
enabled = false
```

<!-- SPEC-TREE:shared commands -->

## Spec Tree Phase Commands

- **author** — Regenerate the generated trees after `src/plugins/` edits: `just build-skills`. Regenerate the root instruction blocks after instruction-template edits: `just build-instructions`.
- **verify** — Node and changeset tests: `just test <pytest-target>...`. Spec-only or Markdown-only changes: `spx validation markdown` and `spx spec status --format json`. Skill/plugin Markdown: `just check-skills` and `just docs-check`.
- **gate** — Full local deterministic gate: `just check-full`.
- **merge** — Ship to the default branch through `/merge`; the GitHub-PR transport merges with `gh pr merge <pr-number> --merge --delete-branch=false`.

<!-- /SPEC-TREE:shared commands -->
