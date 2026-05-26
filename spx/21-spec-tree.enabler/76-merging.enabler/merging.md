# PR Workflow

PROVIDES pull-request lifecycle skills (opening, managing, merging, reviewing) implementing the three PR-authority gates from `spx/15-agent-pr-authority.pdr.md`
SO THAT every product that installs the spec-tree plugin
CAN drive a changeset from review-ready to merge under three observable gates — `REVIEW_READINESS`, `MERGE_READINESS`, `PRODUCTION_READINESS` — with overlay-declared production-relevance per project

## Assertions

### Scenarios

- Given deterministic verification passes and the local `reviewing-changes` review has converged — every finding fixed or split out of the diff and captured in `ISSUES.md` / `PLAN.md` — when `/opening-pr` evaluates `REVIEW_READINESS`, then it creates the PR `ready_for_review`, never as a draft gating step ([eval](evals/review-readiness/eval.toml))
- Given the current-head CI `spec-tree-review` reports no valid finding, every other required check is terminal-green, and branch hygiene and PR state hold (`OPEN`, not draft, head SHA matches origin, rebased onto base), when `/managing-pr` evaluates `MERGE_READINESS` and `PRODUCTION_READINESS` holds, then it merges autonomously without separate human instruction ([eval](evals/merge-readiness/eval.toml))
- Given a production-relevant change (per the project's recognition mechanism) that the operator has not approved, when `MERGE_READINESS` otherwise holds, then `/managing-pr` withholds the merge and emits an explicit-approval action token; given a non-production-relevant change or operator approval, then it executes the merge ([eval](evals/production-readiness/eval.toml))
- Given a required check's `statusCheckRollup` status and conclusion, when the gate classifies it, then it is terminal-green only when terminal (`status == COMPLETED`, or `state ∈ {SUCCESS, ERROR, FAILURE}`) and successful (`conclusion == SUCCESS` or `state == SUCCESS`); a `SKIPPED`, `NEUTRAL`, `FAILURE`, `CANCELLED`, `TIMED_OUT`, still-running, or absent required check is not terminal-green and withholds `MERGE_READINESS` ([eval](evals/terminal-green/eval.toml))
- Given `MERGE_READINESS` and `PRODUCTION_READINESS` are satisfied, when `/managing-pr` selects the merge command, then it follows the overlay's declared merge command if any; when the overlay is silent, it runs rebase merge with inline branch deletion (`gh pr merge --rebase --delete-branch`) as the universal default — the agent never selects a merge commit or squash command from the gate alone, and overlay rationale is advisory documentation rather than a runtime predicate ([eval](evals/merge-command-overlay-precedence/eval.toml))

### Compliance

- ALWAYS: the PR-management skills expose exactly three gates — `REVIEW_READINESS`, `MERGE_READINESS`, `PRODUCTION_READINESS` — named with the single word "gate"; every condition a gate reads is a predicate, never a gate, per `spx/15-agent-pr-authority.pdr.md` ([review])
- ALWAYS: `MERGE_READINESS` and `PRODUCTION_READINESS` are decidable from observable PR state — an independent reader inspecting the same PR with the same overlay reaches the same verdict — and carry no time-based settle, per `spx/15-agent-pr-authority.pdr.md` ([review])
- ALWAYS: the agent acts on each review finding by validity and phase — before open, apply every valid finding that belongs and split out of the changeset any whose fix is too large; on the open PR, fix every valid finding the CI review surfaces, with no deferral — never by the finding's severity label, per `spx/15-agent-pr-authority.pdr.md` ([review])
- ALWAYS: when the CI `spec-tree-review` reports `conclusion: skipped` with cause "PR head differs from main", the agent fires the mention-triggered reviewer with the project's trigger phrase (default `@spec-tree`) and treats its posted findings as the current-head review, per `spx/15-agent-pr-authority.pdr.md` ([review])
- NEVER: gate any of the three gates on a review finding's severity label, or use a time-based settle as a `MERGE_READINESS` predicate — validity and phase decide, and the gate reads the review-landed and terminal-green events directly, per `spx/15-agent-pr-authority.pdr.md` ([review])
- NEVER: open a PR as draft as a gating mechanism or add a separate gated draft-to-ready promotion, and never execute a production-relevant merge from `MERGE_READINESS` alone — the PR opens ready once `REVIEW_READINESS` holds, and a production-relevant merge requires operator approval, per `spx/15-agent-pr-authority.pdr.md` ([review])
- NEVER: treat an agent-inferred "the work looks done" as a gate — a gate's predicates are observable or deterministically computed state, never LLM judgment, per `spx/15-agent-pr-authority.pdr.md` ([review])
