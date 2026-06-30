---
template_version: "0.21.5"
template_source: spec-tree
languages: [python]
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

Per-language code, architecture, and test audits ship as `audit-{lang}*` skills that the generic artifact-type auditors **compose** for the language in scope — there is no per-language auditor agent. Dispatch the generic auditor; it invokes the matching language skill automatically:

| User Says...            | Skill (composed)             | Composing agent             |
| ----------------------- | ---------------------------- | --------------------------- |
| "Audit this code"       | `/audit-python`              | `auditor` (`/audit` family) |
| "Audit ADRs for Python" | `/audit-python-architecture` | `adr-auditor`               |
| "Audit these tests"     | `/audit-python-tests`        | `test-evidence-auditor`     |

---

## Test Naming Convention

Test level is encoded in the filename. The `{evidence}` segment is chosen by `/test` routing from the assertion type: `scenario`, `mapping`, `conformance`, `property`, or `compliance`. Universal assertions use `mapping`, `conformance`, `property`, or `compliance`; a universal is never `scenario`. This guide renders only the languages listed in its `languages` frontmatter; `/update-spx` re-renders from the installed template when the methodology advances.

### Python

| Level | Pattern                           | Example                        |
| ----- | --------------------------------- | ------------------------------ |
| 1     | `test_{subject}.{evidence}.l1.py` | `test_parsing.scenario.l1.py`  |
| 2     | `test_{subject}.{evidence}.l2.py` | `test_cli.mapping.l2.py`       |
| 3     | `test_{subject}.{evidence}.l3.py` | `test_workflow.property.l3.py` |

---

## Session Management

Sessions are shared across every worktree. Each session must be handed off via `/handoff` so it can be resumed from any other worktree: the handoff leaves the worktree clean and persists all state on origin. Propose a handoff when the session's goal is met or the work must pause; resume one with `/pickup`. When a claimed session is complete and should leave the active queue, close it through `/handoff` or `/handoff --no-session` so claimed-session accounting archives it. To return a wrongly claimed session to the shared queue instead, run `spx session release <session-id>`.
