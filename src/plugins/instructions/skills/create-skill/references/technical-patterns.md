<overview>

Apply these patterns when a skill processes files or data, invokes external services, mutates state, or bundles executable automation. Skill structure remains governed by `/skill-standards`.

</overview>

<error_contract>

Define every expected failure with an observable signal and one terminal action:

| Failure class              | Detection                                          | Required action                                                            |
| -------------------------- | -------------------------------------------------- | -------------------------------------------------------------------------- |
| Invalid input              | Schema or precondition failure                     | Reject before mutation and name the invalid field                          |
| Missing resource           | Path, dependency, or capability absent             | Name the resource and exact acquisition step                               |
| Transient external failure | Timeout, rate limit, or retryable service response | Retry only when the service contract permits it and keep a bounded default |
| Authority failure          | Authentication or permission rejection             | Stop and request the required authority without exposing credentials       |
| Partial mutation           | One step fails after state changed                 | Reconcile or roll back through the declared recovery contract              |
| Unknown failure            | Unclassified exception or response                 | Preserve diagnostics and stop without claiming success                     |

Catch only failures the workflow can classify. Broad catch-all handling belongs at a process boundary where it produces diagnostics and a non-success exit; never convert an unknown failure into a successful fallback.

</error_contract>

<security>

- NEVER embed, print, commit, or return secrets.
- Resolve credentials through the target environment's declared mechanism.
- Validate and normalize untrusted paths, then prove the resolved path is inside the authorized root using path-component semantics.
- Use parameterized database queries and context-appropriate output escaping.
- Validate untrusted input before side effects and bound size, count, recursion, and concurrency.
- Keep mutation authority explicit; read-only inspection never implies permission to write or publish.

</security>

<dependencies>

Document only dependencies the execution path requires:

| Field             | Required content                                                             |
| ----------------- | ---------------------------------------------------------------------------- |
| Runtime           | Supported versions and authoritative source                                  |
| Required packages | Exact capability and installation owner                                      |
| Optional packages | Behavior gained and fallback when absent                                     |
| External services | Endpoint class, authentication owner, rate limits, and current documentation |
| Bundled files     | Exact `${CLAUDE_SKILL_DIR}` path and consumer                                |

Never install dependencies during normal skill execution. A repository or plugin installation workflow owns dependency acquisition.

</dependencies>

<resource_boundaries>

| Resource      | Contract to declare                                              |
| ------------- | ---------------------------------------------------------------- |
| Time          | Per-operation timeout and terminal timeout behavior              |
| Files         | Accepted types, maximum size, temporary-storage owner, cleanup   |
| Requests      | Batch and concurrency limits, retry ceiling, rate-limit handling |
| Memory        | Streaming or chunking threshold                                  |
| External cost | Default budget and authority required to raise it                |

Defaults are authority. Never raise a cost, retry, worker, timeout, or external-capacity ceiling without operator approval when the governing repository requires it.

</resource_boundaries>

<state_and_cleanup>

- Create temporary state through an invocation-unique mechanism.
- Assign cleanup to the process that created the state.
- Clean up on success, classified failure, interruption, and validation failure.
- Preserve user-owned files and unrelated working-tree state.
- Verify postconditions from observable state rather than from the absence of an exception.

</state_and_cleanup>

<edge_case_inventory>

| Surface    | Minimum cases                                                                  |
| ---------- | ------------------------------------------------------------------------------ |
| Input      | Empty, absent, malformed, oversized, Unicode, boundary values                  |
| Filesystem | Missing, symlinked, unreadable, unwritable, concurrent change                  |
| Network    | DNS failure, timeout, rate limit, authentication rejection, malformed response |
| State      | Already applied, partial prior run, concurrent actor, stale read               |
| Output     | Empty result, invalid encoding, destination collision, verification failure    |

</edge_case_inventory>

<validation>

- Every side effect has a precondition, authority boundary, observable postcondition, and recovery path.
- Every expected failure maps to one terminal action.
- Dependency and version claims cite current authoritative sources when they can change.
- Resource ceilings are explicit and are never raised implicitly.
- Temporary state is invocation-unique and removed on every exit path.

</validation>
