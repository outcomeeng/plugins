# Sessions

PROVIDES conversation handoff and pickup via timestamped session documents and compact-summary persistence
SO THAT all Claude Code sessions
CAN maintain work continuity without context loss across explicit handoffs and context compaction events

## Assertions

### Scenarios

- Given active work on a spec node with unresolved continuation work that needs a future reader, when `/handoff` runs without `--no-session`, then a session document is created in `.spx/sessions/todo/` with the current tree state and active node path ([test](tests/test_sessions.scenario.l1.py))
- Given active work on a spec node where every remaining issue has been persisted to a spec, ADR, PDR, PLAN.md, or ISSUES.md, when `/handoff --no-session` runs, then no session document is created and every in-scope session is archived ([review])
- Given a session document in `.spx/sessions/todo/`, when `/pickup` runs, then the session is moved to `.spx/sessions/doing/` and its content is emitted to stdout for context loading ([test](tests/test_sessions.scenario.l1.py))
- Given one or more session documents in `.spx/sessions/doing/`, when `spx session release` runs with their IDs, then each session is moved back to `.spx/sessions/todo/` without modifying its content ([test](tests/test_sessions.scenario.l1.py))
- Given coordination-note content is included in the session payload, when the session document is created, then that content appears verbatim in the stored session file ([test](tests/test_sessions.scenario.l1.py))
- Given `/compact` runs mid-session, when the PostCompact hook fires, then the hook parses the compact summary from its JSON payload, emits `<SPEC-TREE_RESUMED active-node="spx/..."/>` (or `<SPEC-TREE_RESUMED/>` when no node was active), and emits `/spec-tree:understanding` and `/spec-tree:contextualizing` on the active node when the foundation marker was active pre-compact ([test](tests/test_sessions.scenario.l1.py))
- Given a root worktree checked out on a named branch, when `spx session handoff` runs, then it creates the session and records `git_ref` as the branch name ([test](tests/test_sessions.scenario.l1.py))
- Given a root worktree with a detached HEAD, when `spx session handoff` runs, then it creates the session and records `git_ref` as the HEAD commit SHA ([test](tests/test_sessions.scenario.l1.py))
- Given a linked worktree with a clean tree detached at the `origin/<default-branch>` tip, when `spx session handoff` runs, then it creates the session and records `git_ref` as that tip commit SHA ([test](tests/test_sessions.scenario.l1.py))
- Given a linked worktree in any other state — on a named branch, or detached away from the `origin/<default-branch>` tip — when `spx session handoff` runs, then it is refused with `SessionHandoffBaseError` ([test](tests/test_sessions.scenario.l1.py))

### Conformance

- The `compactPrompt` in `.claude/settings.json` contains all six state-schema section headers (active node, pre-compact markers, modified files, open questions, last user request, in-flight observations) ([test](tests/test_sessions.conformance.l1.py))

### Compliance

- ALWAYS: `spx session handoff` reads a JSON header object on the first line of stdin followed by the body bytes — YAML frontmatter is never piped to the command; the CLI renders YAML frontmatter itself from the JSON fields and prefills `created_at`, `agent_session_id`, and `git_ref` ([review])
- ALWAYS: from a linked (pool) worktree, `/handoff` invokes `spx session handoff` only after detaching the worktree to the `origin/<default-branch>` tip — the CLI refuses a linked worktree in any other state — and leaves the worktree detached afterward so the released work branch stays unoccupied for another worktree or agent to claim; the committed branch ref carries the work forward, not the worktree checkout ([review])
- ALWAYS: the `/handoff` skill reads PLAN.md and ISSUES.md from the active node directory and includes their content in the session payload — coordination-note content must not be silently omitted ([review])
- ALWAYS: store sessions in `.spx/sessions/` — session state is operational, not part of the durable map ([review])
- NEVER: include session state in committed files — sessions are ephemeral conversation artifacts ([review])
- ALWAYS: configure the `compactPrompt` field to append state-schema sections (active node, pre-compact markers, modified files, open questions, last user request, in-flight observations) to Claude Code's base summarization prompt — base-prompt-forced sections (Pending Tasks, Current Work, Optional Next Step) are accepted as residual; the schema sections are spec-tree's contribution ([review])
- NEVER: add imperative sections via the `compactPrompt` configuration ("next step", "persistence proposal", "starting point") — those compound residual imperatives in base-prompt-forced sections that the marketplace cannot remove ([review])
- NEVER: name specific skill invocations inside the `compactPrompt` configuration — skill choice belongs to the PostCompact hook directive, not to summary text the agent reads as self-direction ([review])
- NEVER: create a session file for a compaction event within an ongoing session — the compact summary carries the state; session files are only for cross-session handoffs ([review])
- NEVER: create a session file when no future reader needs it — when every remaining issue has been persisted to a spec, ADR, PDR, PLAN.md, or ISSUES.md, close with `/handoff --no-session`; a session file with no continuation reader is queue noise that splits truth away from the durable map ([review])
- ALWAYS: a `/handoff` session document initializes the next agent through repository-derived pointers — the anchored node paths and the skills to invoke — so the next agent re-derives detail from the spec tree rather than from the session file ([review])
- ALWAYS: when external infrastructure holds state the next agent cannot re-derive from the spec tree, PLAN.md/ISSUES.md, or git history — live PR, run, image, or job identifiers and their status, deployed inventories, in-flight workflows — the `/handoff` session document records that observable state and guides the next pickup from it in prose ([review])
- NEVER: structure a `/handoff` session document as a retrospective, changelog, activity log, or duplicate of PLAN.md/ISSUES.md, or encode the next pickup's decision as fixed if-then branches — the document points at durable truth and records only the external state the next agent cannot re-derive ([review])
