---
template_version: "0.39.0"
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

<!-- harness:codex -->

## Canonical Agent Registry

The selected `$CODEX_HOME/agents/` directory is the canonical registry for marketplace-delivered custom agents. It contains exactly one current canonical subagent definition per authored marketplace agent, with each name formed as `<plugin>_<unchanged-authored-role>`.

The plugin distribution and its digest-bound ownership record establish membership. A repeated word across the plugin and authored role components is valid. A filename prefix alone never authorizes replacement or pruning.

When a named subagent is unavailable, invoke the owning plugin's `/<plugin>-plugin init` to refresh its definitions in the selected `$CODEX_HOME/agents/`, then reload the harness plugin index or start a new session. `/<plugin>-plugin check` proves whether the selected home carries that plugin's current shipped definitions, writing nothing. A running session retains its already-loaded registry; repeated discovery in that session cannot prove the refresh failed.

**NEVER** create or commit marketplace-delivered agent definitions into a checkout; no generated instruction requires it. A plugin-owned checkout definition whose invoked skills live in the selected agent home is a scope split: remove only a byte-identical generated copy, and inspect every changed or unrecognized copy as a shadowing collision before any removal.

<!-- /harness:codex -->

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

A compacted summary, Handoff, statement that `/understand` ran, or read of the skill file does not prove the foundation is live. After every compaction, invoke `/understand` again before the next product-content access.

The methodology a repository follows is declared in `spx.config.yaml` at the repository root, under `methodology.source` and `methodology.version`. **ALWAYS** read that declaration before applying methodology rules, and read it again whenever `/understand` runs. When the file is absent, the `methodology` block is missing, or `methodology.version` is the sentinel `installed`, the repository declares no methodology version; never infer one from a plugin's distribution version, a changelog, or prose.

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

### Before a resource-intensive command -> `/wait-for-load`

🛑 **STOP TRIGGER — Before any resource-intensive command, ALWAYS invoke `/wait-for-load` and run its waiter chained ahead of that command on the same shell line.**
A resource-intensive command is a test suite, an eval, a full gate, a compiling build, or an install verification; a lightweight command — formatting, a single-file lint, a markdown or link validation, an instruction-block render, a status read — runs without the waiter.
**ALWAYS** let the waiter's zero exit start the selected command unchanged; a lost or truncated result re-runs the same line.
**NEVER** use host load to reduce scope, workers, limits, deadlines, or verification.

<!-- harness:codex -->

**Codex process lifecycle.** The chained line is one `functions.exec` call. Every nested `exec_command` that returns a `session_id` creates an owned process handle. Record it immediately, collect it with `write_stdin` until an `exit_code` is observed, and reconcile every known handle before another process sequence, an operator question, merge or publication, or turn end. If the work is abandoned, interrupt that process and collect its terminal result. Error output or sufficient-looking partial output never closes the handle and never permits leaving its background terminal dangling.

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

## Commit Before Another Session Reads

Changes may remain uncommitted while the Author's agent session works on them. When repository writes are authorized, commit the exact current version through `/commit-changes` before another agent session or human reads it for collaboration or reusable verification; the commit may record `passing`, `failing`, or `not-run`. After any further change, commit the new version before another such reading. An explicit advisory audit or review may inspect modified or untracked work, but its verdict is not reusable gate evidence. Without repository-write authorization, defer a reading that requires a committed subject. Agentic gate dispatch additionally requires its declared deterministic verification to pass on the exact committed subject.

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

Every subagent supplied by a plugin listed below is explicitly pre-authorized by the operator. A harness rule may require the operator to request sub-agent use before one is dispatched; treat this section as that standing request.

<!-- harness:claude -->

Authorized plugins: instructions, frontend, typescript, python, prose, spec-tree, coding-agents, work, hdl, rust, go, contribute.

<!-- /harness:claude -->
<!-- harness:codex -->

Authorized plugins: instructions, frontend, hdl, prose, python, rust, go, spec-tree, coding-agents, typescript, work, contribute.

<!-- /harness:codex -->

- **ONLY** launch a subagent when an active skill explicitly instructs that launch. The skill selects the exact configured subagent and supplies the prompt. Authorization permits the call; it does not request one.
- **NEVER** infer a launch instruction from task wording, a role description, pattern matching, availability, or apparent usefulness.
- **NEVER** ask the operator to confirm dispatching a subagent supplied by a listed plugin. This standing authorization applies to every role that plugin supplies.
- **ALWAYS** make exactly one native launch call for each skill-requested invocation. If the launch fails or its result is unusable, analyze and report the failure without retry, substitution, a model override, another launch mechanism, or a replacement audit in the main conversation.
- **NEVER** run a verification skill — audit or review — in the main conversation; the separate Verifier's agent session keeps the verdict free of the Author's agent session's bias.
- **ALWAYS** start every audit and review without the Author's conversation, reasoning, summaries, or suggested verdict. A separate session with inherited authoring history does not establish isolation. Pass only the skill's target; never append an author-written context packet. The Verifier independently discovers evidence from the target and its configured instructions.
- **ALWAYS** persist accepted requirements in decisions and specs before verification, so the Verifier reads them independently. An approval produced with inherited authoring context supplies no independent gate evidence.
- **ALWAYS** treat the gate as blocked when a required subagent cannot be launched or produces an unusable result. Follow the calling skill's result contract and finding-repair workflow.

### Agent identity in generated artifacts

**NEVER** name the agent identity in an operational artifact — a branch name, commit message, pull-request title or body, review comment, or authorship marker written into a product file. Describe the work, never who performed it. Exact filesystem paths, package and tool names, quoted command output, and operator-supplied text keep their required spelling.

**ALWAYS** confine that ban to operational artifacts. Authored guidance that documents Claude's behavior uses imperative voice or names Claude as its subject by design; stripping Claude from that guidance to satisfy this rule misapplies it rather than complying with it.

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

## Subagent invocation

Use the native tool schema for accepted arguments and call shape. Follow the active skill's exact configured subagent name and target-only prompt.

<!-- harness:codex -->

Launch through `collaboration.spawn_agent` and collect the result through the native collaboration tools.

**Already-dispatched Verifier boundary.** Apply launch instructions only in the Author's main conversation. For every audit or review launch, explicitly set `fork_turns: "none"`; omitting it inherits the entire authoring conversation. Once running as a Verifier, execute the configured audit or review skill directly. If authoring history was inherited, report the isolation failure instead of issuing an independent verdict. NEVER search for or spawn another Verifier.

<!-- /harness:codex -->
<!-- harness:claude -->

Launch through the `Agent` tool in the foreground and collect its completed result.

<!-- /harness:claude -->

## Quick Reference: Skills

The table routes tasks to skills. Only an active skill's explicit invocation instruction requests a subagent.

| User Says...                                            | Skill                  |
| ------------------------------------------------------- | ---------------------- |
| "Implement this outcome" or "Start the TDD flow"        | `/apply`               |
| "Create an outcome" or "Add an ADR"                     | `/author`              |
| "Add a new node" or "This node is too big"              | `/decompose`           |
| "Move this under that"                                  | `/refactor`            |
| "Check these specs"                                     | `/align`               |
| "Establish evidence for this" or "Write tests for this" | `/verify`              |
| "Audit this PDR"                                        | `/audit-pdr`           |
| "Audit this ADR"                                        | `/audit-adr`           |
| "Audit test evidence"                                   | `/audit-tests`         |
| "Audit eval evidence"                                   | `/audit-eval-evidence` |
| "Audit this spec node"                                  | `/audit-specs`         |
| "Diagnose the spx environment"                          | `/diagnose`            |
| "Claim this Change"                                     | `/claim-change`        |
| "Release this Change" or "Hand this off"                | `/release-change`      |
| "Close this Change as Applied"                          | `/close-change`        |

<!-- langs:present -->

Per-language code, architecture, and test audits ship as `audit-{lang}-{code|tests|architecture}` skills. The active verification workflow composes the skills for the languages recorded in this instruction block's opening marker.

<!-- /langs:present -->
<!-- lang:python -->

| User Says...            | Skill (composed)             |
| ----------------------- | ---------------------------- |
| "Audit this code"       | `/audit-python-code`         |
| "Audit ADRs for Python" | `/audit-python-architecture` |
| "Audit these tests"     | `/audit-python-tests`        |

<!-- /lang:python -->
<!-- lang:typescript -->

| User Says...                | Skill (composed)                 |
| --------------------------- | -------------------------------- |
| "Audit this code"           | `/audit-typescript-code`         |
| "Audit ADRs for TypeScript" | `/audit-typescript-architecture` |
| "Audit these tests"         | `/audit-typescript-tests`        |

<!-- /lang:typescript -->
<!-- lang:rust -->

| User Says...          | Skill (composed)           |
| --------------------- | -------------------------- |
| "Audit this code"     | `/audit-rust-code`         |
| "Audit unsafe Rust"   | `/audit-rust-code`         |
| "Audit ADRs for Rust" | `/audit-rust-architecture` |
| "Audit these tests"   | `/audit-rust-tests`        |

<!-- /lang:rust -->
<!-- lang:go -->

| User Says...              | Skill (composed)         |
| ------------------------- | ------------------------ |
| "Audit this code"         | `/audit-go-code`         |
| "Audit concurrency in Go" | `/audit-go-code`         |
| "Audit ADRs for Go"       | `/audit-go-architecture` |
| "Audit these tests"       | `/audit-go-tests`        |

<!-- /lang:go -->

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
<!-- lang:go -->

### Go

| Level | Pattern                                         | Example                               |
| ----- | ----------------------------------------------- | ------------------------------------- |
| 1     | `{subject}.{evidence}.l1_test.go`               | `parsing.scenario.l1_test.go`         |
| 2     | `{subject}.{evidence}.l2_test.go`               | `cli.mapping.l2_test.go`              |
| 3     | `{subject}.{evidence}.l3_test.go`               | `workflow.property.l3_test.go`        |
| 1-3   | `{subject}.{evidence}.{level}.{runner}_test.go` | `workflow.property.l2.ginkgo_test.go` |

<!-- /lang:go -->
<!-- lang:python -->

### Python

| Level | Pattern                           | Example                        |
| ----- | --------------------------------- | ------------------------------ |
| 1     | `test_{subject}.{evidence}.l1.py` | `test_parsing.scenario.l1.py`  |
| 2     | `test_{subject}.{evidence}.l2.py` | `test_cli.mapping.l2.py`       |
| 3     | `test_{subject}.{evidence}.l3.py` | `test_workflow.property.l3.py` |

<!-- /lang:python -->

---

## Change Lifecycle

Work is coordinated through Changes in the store `spx/local/coordination.md` declares. Hold a Change through `/claim-change` before refining or executing it. When the work stops with continuation remaining, `/release-change` writes the Handoff, removes the holder, and returns the Change to Available for any agent to claim; when the Change reaches a terminal Lifecycle, `/close-change <Applied|Refined|Abandoned>` writes the terminal record and closes it. A follow-up is a Proposed Change created through `/author-change`. Maturity moves only through `/author-change`; the three Lifecycle skills move Lifecycle and nothing else.
