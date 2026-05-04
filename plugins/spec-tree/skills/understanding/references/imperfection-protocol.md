<objective>
The imperfection protocol governs how Claude tracks and resolves observed imperfections during any work session. It is loaded by `/understanding` so all spec-tree work — and any skill that inherits this foundation, such as `/handing-off` — can rely on the ledger without depending on user-level configuration.

The repo is the artifact the user ships. Small defects — a stale comment, a broken link, an inconsistent name, a missing test — accumulate into incoherence. Claude addresses observed imperfections immediately because that is the simplest and most respectful thing to do.

</objective>

<recording>

When Claude observes an imperfection — failing validation, broken link, outdated reference, stale comment, dead code, lint violation, missing test, inconsistent naming, misplaced file, wrong index, anything — Claude records it in the current-turn imperfection ledger with:

- The exact imperfection
- The file path, line, command output, or page state that exposed it
- The skill or workflow that governs the fix
- The proposed handling (fix-now, surface, or hand off)

A safe local fix is applied immediately without asking. A blocking decision is surfaced via `AskUserQuestion` immediately. A non-blocking decision is held for the closing protocol below.

</recording>

<no_origin_distinction>

The ledger is unified. An imperfection observed in the current session is owned by Claude regardless of when it entered the repo, who introduced it, or whether it pre-dates the current session. Never qualify an imperfection by its origin — no "pre-existing", "not introduced this turn", "inherited", "out of scope of this turn", "not authored by me", or equivalent phrasing. Record every observed imperfection equally and identically.

The closing protocol decides whether to fix now (Option 1), track and defer (Option 2), or confirm absence (Option 3) — origin never modifies that decision and never appears in the language used to describe the imperfection.

</no_origin_distinction>

<closing_protocol>

Every turn ends with `AskUserQuestion`. This is the only valid way to close a turn — no plain-text closings, no trailing "let me know", no offers in prose. The question presents three options that frame Claude's recommendation and let the user choose.

**The closing protocol applies at task completion, not at every milestone.** A turn is a checkpoint when the user's stated goal is still unfulfilled. While the goal is unfulfilled, Claude continues working — reports brief status updates, surfaces blockers via `AskUserQuestion` only when input is genuinely required (not confirmation), and never proposes "separate session", "future session", or "next session" as an out. Deferring work to a future session is a closing reflex, not a real plan. If the work is in front of Claude and the goal demands it, Claude does it.

The user's stated goal governs what "task complete" means. When the user says "fix CI", the task is unfinished while CI is red. Component milestones (a single test passes, a single migration commits) are progress, not completion. Closing the session before the goal is achieved is a violation of the user's instruction.

**Option 1 — Address discovered imperfections first.** Use when one or more imperfections were observed and not yet fixed.

**Option 2 — Track imperfections and proceed.** Use when the user may rationally prefer to postpone the fix.

**Option 3 — Everything is impeccable; hand off.** Use only when Claude is 100% certain (a) the imperfection ledger is empty AND (b) the user's stated goal for this session is fully achieved. An empty ledger alone does not authorize handoff; the goal must be met.

</closing_protocol>

<spec_tree_integration>

Spec-tree skills that close sessions (notably `/handing-off`) lean on the ledger rather than re-implementing reflection. Workflow 02 of `/handing-off` reviews remaining imperfections and classifies them by destination. Skills that do not close sessions still record imperfections during their work — a fix-now resolution within a workflow is the most common path.

The ledger is per-conversation, not persistent across sessions. Resolved imperfections don't need to carry forward; the persistence hierarchy in `/handing-off` decides what becomes durable (spec amendments, methodology updates, escape hatches) and what's session-only.

</spec_tree_integration>
