# PLAN: Disentangle `fix/auditor-agents` into a reviewed, merged PR stack

## Why

`fix/auditor-agents` was a `wip` grab-bag (~146 files, ~8 concerns). It is split
into four stacked, independently-reviewable PRs plus one deliberately-deferred
follow-up. This note carries the merge coordination and the parallelizable work
across sessions and worktrees. The original combined branch `fix/auditor-agents`
is kept as a backup — do not delete until all four merge.

## The stack (merge order, bottom-up)

| # | Branch                     | PR   | Base                       | Concern                                                                                                                                                         |
| - | -------------------------- | ---- | -------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1 | `fix/auditor-rename`       | #158 | `main`                     | `audit-adr`/`audit-pdr` agents → `adr-auditor`/`pdr-auditor`; `spx/local` overlay rename to `skills.md`                                                         |
| 2 | `feat/sentinel-55-example` | #159 | `fix/auditor-rename`       | `spx/NN-` → `spx/55-example` sentinel; portability gate + spec + test; tree-wide example-path migration; `spx-claude.md` template (0.18.6) + guide              |
| 3 | `feat/agent-model-sonnet`  | #160 | `feat/sentinel-55-example` | `model: sonnet` on the 3 audit agents; verification `PLAN.md` single-source section deleted; `32-decisions/ISSUES.md` note corrected                            |
| 4 | `docs/repo-guidance`       | #161 | `feat/agent-model-sonnet`  | root `AGENTS.md` `marketplace`→`product` restructure (reconciled onto `origin/main`'s 2-severity taxonomy); README ABC/DCI principles; eval-harness ISSUES note |

State at last write: #158 in CI on head `5fdd4b46` (`UNSTABLE`, checks running).
#159/#160/#161 still sit on the **old** #158 tip — each base-syncs onto `main`
after its predecessor merges.

## Per-branch merge loop (each branch, in order)

1. **Base-sync.** After the prior PR merges, rebase this branch onto `origin/main`.
2. **Converge locally.** Run `changes-reviewer` to **exhaustion** on the branch's
   diff vs its base; fix every valid finding BEFORE pushing. Never push-and-let-CI-
   find — that burns one ~7-min CI cycle per finding.
3. `just check` green + `<branch_hygiene>`.
4. Push (`--force-with-lease` after a rebase, plain push otherwise).
5. Heartbeat; on a clean current-head CI review + every check terminal-green,
   `MERGE_READINESS` holds (overlay declares no production-relevance) → merge via
   `gh pr merge <n> --merge` then `git push origin --delete <branch>`.

## Parallelizable now (while #158 is in CI)

- **Pre-converge #159, #160, #161:** run `changes-reviewer` to exhaustion on each
  (against its current base) in parallel; fix piece-local findings so each is
  merge-ready when its turn arrives. Re-converge after each base-sync, since the
  rebase produces a tree no prior review covered.
- **Prepare the deferred follow-up (below)** off `main`, independent of the stack.

## Deferred follow-up — agentic verdict alignment (own PR, after the stack)

Removed from #158 to keep it a clean rename. Scope:

- Scenario actors in `adr-auditing.md` / `pdr-auditing.md` → the agent form
  (`when audited by the \`adr-auditor\` agent`).
- Verdict-context token → canonical `REJECTED` — the **Status** value per
  `spx/21-spec-tree.enabler/16-verification.enabler/15-verdict-toolchain.enabler/verdict-toolchain.md`
  (`Status ∈ {APPROVED, REJECTED, PASS, FAIL, UNKNOWN}`). The per-finding
  **Severity** stays `REJECT` (`Severity ∈ {REJECT, WARNING, INFO}`) — NEVER
  blanket-replace `REJECT`→`REJECTED`; only verdict-context occurrences change.
- Propagate `REJECTED` to verdict-context prose in `audit-adr/SKILL.md` and
  `audit-pdr/SKILL.md` (keep finding-severity `REJECT`), so spec + skills + agents
  agree. Rebuild `dist`.

Rationale: the audit skills use `REJECT` for the overall verdict (a pre-existing
imprecision); the agents already declare `REJECTED`. Aligning to the Status enum
is correct per "spec governs," but it is a verdict-terminology concern, not a
rename — so it ships separately.

## Model handling — #160's `model: sonnet` is REQUIRED; amend the ADR

There is NO build step substituting the wrapper model per runtime today. So every
wrapper agent MUST declare `model: sonnet` (or `model: inherit`) explicitly — a
missing model field falls back to the session model (Opus 4.8), which is
unacceptable for verification agents. #160's addition of `model: sonnet` to the
three audit agents that lacked it is CORRECT and necessary; without it they
default to Opus. **#160 stands.**

The defect is in the decision, not in #160:
`spx/21-spec-tree.enabler/16-verification.enabler/13-architecture.adr.md` line 21
(`NEVER pin a literal sonnet the build cannot substitute`) presumes a build step
that does not exist. Applied now it strips the literals and breaks every agent —
the inverse-of-intended outcome. **Amend the ADR** to state the current
requirement (every wrapper declares `model: sonnet` or `inherit`) and frame
build-substitution — `sonnet` as the default-if-unspecified, a Codex-equivalent
substituted — as the target end-state to implement FIRST, never a rule that
strips literals before the build exists.

Single-sourcing IS the eventual design (author once for Claude, adapt for Codex
at build), but it is gated on building that substitution step and must not break
agents in the meantime. (A prior pass in this effort inverted this — "remove the
literals and single-source now" — which would have defaulted every agent to Opus.
Do not repeat it.)

## Carried stale-ref notes

- Both #158 and #160 edit `32-decisions/ISSUES.md`. After #158 merges, #160's
  base-sync will touch that file — resolve by keeping #158's agent-name rename
  and #160's model-conformance note.

## Lessons (apply to the rest of this effort)

1. Converge the local `changes-reviewer` to exhaustion BEFORE each push — one pass
   catches the bounded finding set; CI then confirms in a single round.
2. Keep each piece's scope tight — when a rename edit starts forcing semantic
   changes elsewhere (e.g. verdict terminology), that work belongs in a different
   piece, not absorbed into the rename.
