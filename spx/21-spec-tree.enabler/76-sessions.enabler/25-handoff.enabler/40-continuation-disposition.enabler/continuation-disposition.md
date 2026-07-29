# Continuation Disposition

PROVIDES the per-thread decision of whether a continuation session is created, reused from an existing owner, or omitted, together with the archiving that follows it
SO THAT a closure spanning several independent threads
CAN leave exactly one canonical continuation per thread and no queue entry that duplicates an existing one

## Assertions

### Compliance

- ALWAYS: before `/handoff` proposes or creates any continuation session, it searches existing `todo` and `doing` sessions for overlapping node paths and topic terms, reconciles whether an existing session already owns the continuation, archives only sessions this conversation owns, and refuses to add a new `todo` entry when doing so would duplicate existing queue state ([audit])
- NEVER: `/handoff` mutates an existing session document; when a continuation supersedes a same-conversation artifact, `/handoff` creates a fresh session through `spx session handoff`, verifies the new session, and archives the superseded artifact ([audit])
- ALWAYS: every fresh `/handoff` resolves the current runtime identity before filing, requires the stored session's `agent_session_id` to equal that identity, and archives no superseded artifact until the identity and pickup anchor are verified — so post-compaction recovery can rediscover every same-conversation continuation by exact identity ([audit])
- ALWAYS: when a claimed session's original deliverable is complete but any anchored node still has unrelated `PLAN.md` or unresolved `ISSUES.md` continuation, `/handoff` archives the completed claimed session only after the note is fixed, reconciled, or continuation by the agent is impossible; an ordinary unresolved coordination note is not a reason to create a thin handoff ([audit])
- ALWAYS: partition anchored work and same-conversation artifacts into independent closure threads, recording each thread's queue ownership and continuation state; decide each thread's session-file creation independently of `CLAIMED_SESSIONS`, which governs only which sessions are archived ([audit])
- NEVER: omit the session file for unfinished in-scope work because its steps are already persisted to PLAN.md or ISSUES.md — coordination notes and the session pointer serve different roles; close without a session file only when the in-scope work has reached its user-approved stopping state with no continuation remaining, since a session file with no continuation reader is queue noise that splits truth away from the durable map ([audit])
- ALWAYS: for every closure thread with no unresolved continuation, `/handoff` completes approved persistence without creating a session document; plain merge lifecycle automation needs no `--no-session` option to reach zero-handoff closeout ([audit])
- ALWAYS: when `/handoff` runs with `--no-session`, each closure thread may omit a session only when its continuation is absent or another `todo` or `doing` session owns it; claimed and superseded same-conversation sessions are archived according to that thread's approved partition ([audit])
- ALWAYS: `--no-session` asserts per closure thread that no unowned continuation remains, never "skip every session regardless" — when any thread has unresolved continuation and no existing owner, `/handoff` surfaces that thread-specific contradiction and does not let another thread's valid zero-handoff state suppress its session file ([audit])
- NEVER: automation passes `--no-session` to `/handoff` on the user's behalf — a transport's post-merge closure invokes `/handoff` plain and the skill decides session-file creation per continuation state; a hardcoded `--no-session` in the merge lifecycle is forbidden because it overrides a user-intent flag the user did not give ([audit])
