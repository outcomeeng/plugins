# Queued-Work Discoverability

PROVIDES a session-start directive that surfaces claimable handoff sessions in a spec-tree repository
SO THAT an agent beginning a session
CAN act on queued `/pickup` work instead of starting unaware it exists

## Assertions

### Scenarios

- Given a `SessionStart` payload whose pool holds one or more `todo` sessions, when the hook runs, then stdout carries a directive listing each claimable session's id, goal, and next step and naming `/spec-tree:pickup` as the way to claim it ([test](tests/test_queued_work_discoverability.scenario.l1.py))

### Mappings

- The `spx session todo` projection maps to the directive output: a non-empty `todo` set maps to a directive surfacing each session's id, goal, and next step; an empty set maps to no directive ([test](tests/test_queued_work_discoverability.mapping.l1.py))

### Compliance

- ALWAYS: fire only in a spec-tree repository — detected by an `spx/*.product.md` product spec under the project directory, the same signal the understanding directive uses — then gather the queue through a single `spx session todo --fields id,priority,goal,next_step,git_ref` invocation that degrades to a silent no-op when the project is not a spec tree, the CLI is absent, exits non-zero, or yields no sessions; reading the durable `spx/` tree is never a probe of `.spx/` state ([test](tests/test_queued_work_discoverability.compliance.l1.py))
- ALWAYS: present the pool-global queue unfiltered by the current worktree's branch — the session store is pool-shared across every worktree (`spx/21-spec-tree.enabler/11-repository-layout.pdr.md`) and a session is a cross-worktree pointer (`spx/21-spec-tree.enabler/76-sessions.enabler/sessions.md`), so `git_ref` identifies a session's branch, not a discoverability filter ([test](tests/test_queued_work_discoverability.compliance.l1.py))
- NEVER: claim, pick up, or otherwise mutate a session — the directive surfaces queued work and leaves all session state to `/spec-tree:pickup` ([test](tests/test_queued_work_discoverability.compliance.l1.py))
- ALWAYS: word the directive so it never implies a queued session's work is recoverable — origin-persistence is a precondition of a valid handoff, not a guarantee the directive can assert, since a session whose work branch is unpushed points at unrecoverable state (`spx/21-spec-tree.enabler/76-sessions.enabler/13-handoff-persistence.adr.md`) ([audit])
