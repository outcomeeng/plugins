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

The user's stated goal governs what "task complete" means. When the user says "fix CI", the task is unfinished while CI is red. Component milestones (a single test passes, a single migration commits) are progress, not completion. Closing the session before the goal is achieved is a violation of the user's instruction.

**Handling 1 — Address discovered imperfections first.** Use when one or more imperfections were observed and not yet fixed.

**Handling 2 — Record unresolved imperfections and proceed.** Use when the user may rationally prefer to postpone the fix. The destination must match the artifact taxonomy: specs/ADRs/PDRs for truth changes, methodology for workflow rules, PLAN.md for pending node work, and ISSUES.md for known node issues.

**Handling 3 — Proceed to the next governed workflow step.** Use only when the imperfection ledger is empty and the user's stated goal for this session has reached its acceptance state. An empty ledger alone does not authorize closure. Invoke `/handoff` only when cross-session handoff is the actual next workflow step.

</closing_protocol>

<spec_tree_integration>

Spec-tree skills that close sessions (notably `/handoff`) lean on the ledger rather than re-implementing reflection. Workflow 02 of `/handoff` reviews remaining imperfections and classifies them by destination. Skills that do not close sessions still record imperfections during their work — a fix-now resolution within a workflow is the most common path.

The ledger is per-conversation and does not persist by itself. Resolved imperfections don't need to carry forward. Unresolved entries persist only when written to the right artifact: spec amendments for product truth, methodology updates for workflow rules, or node-local PLAN.md / ISSUES.md coordination notes for future-session coordination. PLAN.md and ISSUES.md entries are committed to git in the same change that introduces them — git-tracking carries the coordination to the next session, but the content stays a stale-prone input the next session must reconcile against the specs, decisions, assertions, tests, implementation, and current user intent before acting on it, never product truth. Session files under `.spx/sessions/` are the only spec-tree artifacts that remain outside git; `spx session` shares them across worktrees.

</spec_tree_integration>
