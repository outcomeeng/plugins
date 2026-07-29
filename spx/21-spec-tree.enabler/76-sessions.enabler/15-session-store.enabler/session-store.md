# Session Store

PROVIDES the `.spx/sessions/` document store and the `spx session` command contract — document creation from a stdin JSON header, `git_ref` derivation and its refusals, and the `todo`/`doing` transitions
SO THAT the handoff and pickup workflows, and an operator inspecting session state directly
CAN create, claim, release, and read session documents through one published contract rather than constructing store paths or parsing session frontmatter

## Assertions

### Scenarios

- Given continuation by the agent is impossible because the user halted the work, context is exhausted, or an external blocker prevents the next action, when `/handoff` runs without `--no-session`, then a session document is created in `.spx/sessions/todo/` with the current tree state and active node path ([test](tests/test_sessions.scenario.l1.py))
- Given a session document in `.spx/sessions/todo/`, when `/pickup` runs, then the session is moved to `.spx/sessions/doing/` and its content is emitted to stdout for context loading ([test](tests/test_sessions.scenario.l1.py))
- Given one or more session documents in `.spx/sessions/doing/`, when `spx session release` runs with their IDs, then each session is moved back to `.spx/sessions/todo/` without modifying its content ([test](tests/test_sessions.scenario.l1.py))
- Given coordination-note content is included in the session payload, when the session document is created, then that content appears verbatim in the stored session file ([test](tests/test_sessions.scenario.l1.py))
- Given a root worktree checked out on a named branch, when `spx session handoff` runs, then it creates the session and records `git_ref` as the branch name ([test](tests/test_sessions.scenario.l1.py))
- Given a root worktree with a detached HEAD, when `spx session handoff` runs, then it creates the session and records `git_ref` as the HEAD commit SHA ([test](tests/test_sessions.scenario.l1.py))
- Given a linked worktree with a clean tree detached at the `origin/<default-branch>` tip, when `spx session handoff` runs, then it creates the session and records `git_ref` as that tip commit SHA ([test](tests/test_sessions.scenario.l1.py))
- Given a linked worktree on a named branch, when `spx session handoff` runs, then it is refused and no session file is written ([test](tests/test_sessions.scenario.l1.py))
- Given a linked worktree detached away from the `origin/<default-branch>` tip, when `spx session handoff` runs, then it is refused and no session file is written ([test](tests/test_sessions.scenario.l1.py))
- Given a linked worktree at the `origin/<default-branch>` tip and an explicit work-branch ref naming a branch on `origin` in the JSON header, when `spx session handoff` runs, then it records `git_ref` as that branch name rather than the tip SHA ([test](tests/test_sessions.scenario.l1.py))
- Given an explicit work-branch ref naming a branch absent from `origin`, when `spx session handoff` runs, then it is refused and no session file is written ([test](tests/test_sessions.scenario.l1.py))

### Compliance

- ALWAYS: `spx session handoff` reads a JSON header object on the first line of stdin followed by the body bytes — YAML frontmatter is never piped to the command; the CLI renders YAML frontmatter itself from the JSON fields, prefills `created_at` and `agent_session_id`, and records the header's `git_ref` as the work branch after verifying it exists on origin — deriving `git_ref` from the git context when the header omits it ([audit])
- ALWAYS: `spx session handoff` refuses a linked worktree that is not clean and detached at the `origin/<default-branch>` tip with `SessionHandoffBaseError`, and an explicit work-branch ref absent from `origin` with `SessionWorkBranchNotOnOriginError`; the raising source is the `spx` CLI, so this agreement between the recorded names and the CLI's behavior carries no importable oracle and is established by inspection, per `spx/12-shipped-scripting.adr.md` ([audit])
- ALWAYS: store sessions in `.spx/sessions/` — session state is operational, not part of the durable map ([audit])
- ALWAYS: execute an operator's explicit `spx session` request against identified session documents — including inspection, archive, and release — as operational-state management without requiring `SPEC_TREE_FOUNDATION`; require the marker only before following session output into `spx/`, source, or test content ([audit])
- NEVER: include session state in committed files — sessions are ephemeral conversation artifacts ([audit])
