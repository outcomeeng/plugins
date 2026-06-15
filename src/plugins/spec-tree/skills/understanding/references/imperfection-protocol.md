<objective>
The imperfection protocol governs how Claude tracks and resolves observed imperfections during any work session. It is loaded by `/understanding` so all spec-tree work — and any skill that inherits this foundation, such as `/handoff` — can rely on the ledger without depending on user-scope configuration.

The repo is the artifact the user ships. Small defects — a stale comment, a broken link, an inconsistent name, a missing test — accumulate into incoherence. Claude addresses observed imperfections immediately because that is the simplest and most respectful thing to do.

</objective>

<recording>

When Claude observes an imperfection — failing validation, broken link, outdated reference, stale comment, dead code, lint violation, missing test, inconsistent naming, misplaced file, wrong index, anything — Claude records it in the current-turn imperfection ledger with:

- The exact imperfection
- The file path, line, command output, or page state that exposed it
- The skill or workflow that governs the fix
- The proposed handling (fix now, ask for operator judgment, or write to the correct coordination artifact)

A safe local fix is applied immediately without asking. A blocking decision is surfaced via `AskUserQuestion` immediately. A non-blocking decision is held until the next natural checkpoint.

</recording>

<no_origin_distinction>

The ledger is unified. An imperfection observed in the current session is owned by Claude regardless of when it entered the repo, who introduced it, or whether it pre-dates the current session. Never qualify an imperfection by its origin — no "pre-existing", "not introduced this turn", "inherited", "out of scope of this turn", "not authored by me", or equivalent phrasing. Record every observed imperfection equally and identically.

The closing protocol decides whether to fix now, record the issue in the right artifact with operator agreement, or proceed because no unresolved imperfection remains. Origin never modifies that decision and never appears in the language used to describe the imperfection.

</no_origin_distinction>

<closing_protocol>

Every turn ends with `AskUserQuestion`. This is the only valid way to close a turn — no plain-text closings, no trailing "let me know", no offers in prose. The question presents the concrete next handling and lets the user choose when operator judgment is needed.

**The closing protocol applies at task completion, not at every milestone.** A turn is a checkpoint when the user's stated goal is still unfulfilled. While the goal is unfulfilled, Claude continues working — reports brief status updates, surfaces blockers via `AskUserQuestion` only when input is genuinely required, and never proposes "separate session", "future session", or "next session" as an out. Recording future-session coordination is appropriate only when the user accepts that destination or runtime constraints require persistence.

The user's stated goal governs what "task complete" means. When the user says "fix CI", the task is unfinished while CI is red. Component milestones (a single test passes, a single migration commits, a single PR merges) are progress, not completion. Closing the session before the goal is achieved is a violation of the user's instruction.

**Handoff is not a voluntary close.** A session ends — and `/handoff` runs — only when the session is genuinely over: either the user's stated goal is met with no in-scope continuation remaining, or continuation by Claude now is impossible (the user halts the work, the context is exhausted, or an external blocker — operator input, a remote-state change Claude cannot effect — prevents the next action). Genuine completion is a valid close; what is forbidden is handing off while do-able work remains. While in-scope work Claude could do now remains, the session does not end and `/handoff` is not invoked. Do-able work remaining is signalled objectively by any of: an unresolved item in a `PLAN.md` authored or touched this session; a `spx/EXCLUDE` entry covering the work in scope; a declared-but-unimplemented assertion; or a named-but-unbuilt part of the user's stated goal. A merge, a passing gate, or a persisted coordination note is never itself a license to stop. Writing a `PLAN.md` or a session file to defer do-able work and then stopping is the banned closing reflex — coordination notes record steps for a genuine cross-session boundary, never permission to stop while Claude can still act. Persisting coordination and continuing is correct; persisting coordination and handing off while able to continue is the failure this rule exists to prevent.

**Handling 1 — Address discovered imperfections first.** Use when one or more imperfections were observed and not yet fixed.

**Handling 2 — Record unresolved imperfections and proceed.** Use when the user may rationally prefer to postpone the fix. The destination must match the artifact taxonomy: specs/ADRs/PDRs for truth changes, methodology for workflow rules, PLAN.md for pending node work, and ISSUES.md for known node issues. Recording the imperfection is not stopping — continue the goal after recording.

**Handling 3 — Proceed to the next governed workflow step.** Use when the user's stated goal is not yet met: continue the work (the next implementation slice, the next goal-part, the next PR) directly. This is the default while do-able in-scope work remains. Invoke `/handoff` from this handling only when continuation by Claude now is impossible per "Handoff is not a voluntary close" above — never as a voluntary close while work Claude could do remains.

</closing_protocol>

<spec_tree_integration>

Spec-tree skills that close sessions (notably `/handoff`) lean on the ledger rather than re-implementing reflection. Workflow 02 of `/handoff` reviews remaining imperfections and classifies them by destination. Skills that do not close sessions still record imperfections during their work — a fix-now resolution within a workflow is the most common path.

The ledger is per-conversation and does not persist by itself. Resolved imperfections don't need to carry forward. Unresolved entries persist only when written to the right artifact: spec amendments for product truth, methodology updates for workflow rules, or node-local PLAN.md / ISSUES.md coordination notes for future-session coordination. PLAN.md and ISSUES.md entries are committed to git in the same change that introduces them — git-tracking carries the coordination to the next session, but the content stays a stale-prone input the next session must reconcile against the specs, decisions, assertions, tests, implementation, and current user intent before acting on it, never product truth. Session files under `.spx/sessions/` are the only spec-tree artifacts that remain outside git; `spx session` shares them across worktrees.

</spec_tree_integration>
