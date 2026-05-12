# PLAN — auditing toolchain: three-step rollout

The audit capability lands in three steps. The `auditing` skill owns the audit policy: the six-phase run, language-partition dispatch, aggregation, and JSON-verdict emission through the toolchain in `scripts/`. Agents wrap the skill — they never invoke `scripts/` through a path the skill does not already resolve.

Naming: agents that run only the audit are `audit*` (`auditor`, `audit-orchestrator`); agents that bundle the existing PR-review prompt with the audit are `*review*` (`pr-reviewer`, `pr-review-orchestrator`) — review is the umbrella, the audit is one part of it. Bare name = one-off, no persisted state; `-orchestrator` suffix = stateful, tracks finding resolution across runs. A workflow mirrors the agent it runs: `claude-` prefix, agent name without the `pr-` prefix.

| Agent                    | Step                              | Runs in                               | Job                                                                                                          | State surface                               |
| ------------------------ | --------------------------------- | ------------------------------------- | ------------------------------------------------------------------------------------------------------------ | ------------------------------------------- |
| `auditor`                | 1 (this branch)                   | local                                 | one-off: invoke `auditing` on a scope, render per `--json` / `--markdown` / `--markdown+json`                | none                                        |
| `pr-reviewer`            | 1 (this branch)                   | CI (`claude-reviewer.yml`)            | one-off: invoke the review-prompt skill + `auditing`, post one combined review+audit PR comment              | none                                        |
| `audit-orchestrator`     | 2 (`work/audit-orchestrator`)     | local                                 | stateful: maintain `.spx/audits/<lang>/<branch-slug>.md` across commits; observable precursor to CI          | `.spx/audits/` (gitignored, worktree-local) |
| `pr-review-orchestrator` | 3 (`work/pr-review-orchestrator`) | CI (`claude-review-orchestrator.yml`) | stateful: ingest existing PR review comments → feed `auditing` → update the PR via a `markdown+json` comment | PR comment thread                           |

## Step 1 — this branch (`work/audit-verdict-toolchain`, PR #11)

Scope: the verdict toolchain plus the one-off agents plus the `claude-reviewer` workflow. No persisted state anywhere.

### Landed

- Verdict toolchain: `verdict.py` (canonical schema + `roll_up`), `emit_verdict.py` / `read_verdict.py` / `aggregate_verdicts.py` / `pass_results.py`, the `spx/15-audit-verdict-format.pdr.md` flip to JSON + carrier+payload + format axis, the `65-verdict-toolchain.enabler` spec node + its five scenario test files, the eleven-skill marketplace alignment.
- `spec(spec-tree): scope the auditing node and ADR to a one-off audit` (`778accf`) — `auditing.md` rewritten to the step-1 scope (six-phase audit on a frozen scope, `detect_base_ref` / `branch_scope` / `expand_diff_range` scenario assertions, scope-hash property, the `auditor`/`pr-reviewer` agent-wrapper compliance rules); `17-auditing.adr.md` amended (skill owns policy, agents are wrappers, the `${CLAUDE_SKILL_DIR}` vs `${CLAUDE_PLUGIN_ROOT}` path constraint, the `.spx/audits/` state text removed).
- `refactor(spec-tree): trim audit_orchestrator to the git/scope helpers` (`cf029b3`) — `audit_orchestrator.py` 887 → 168 lines: kept `compute_scope_hash`, `expand_diff_range`, `branch_scope`, `detect_base_ref` (stdlib-only); removed `AuditState`, `Finding`/`ResolvedFinding`, `load_state`/`save_state`, `assign_finding_id`, `find_resolved_by_identity`/`reopen_finding`/`resolve_finding`, `RunLock`, `branch_slug`, `detect_current_branch`, `modified_since`, `is_sha_reachable`, the three exception classes, the unused `verdict` module load. `tests/test_auditing.scenario.l1.py` 1443 → 318 lines (kept the `detect_base_ref` / `expand_diff_range` / `branch_scope` scenarios + the module-surface guard; `test_auditing.property.l1.py` untouched). 16 node tests pass; ruff clean; `python-code-auditor` APPROVED, `python-test-auditor` APPROVED.
- `refactor(spec-tree): slim the auditing skill and auditor agent to the one-off flow` (`8702044`) — `auditing/SKILL.md`: added the `<codex_fallback>` block for the `scripts/` paths, removed `<re_run_protocol>` and the Phase 0 "read prior verdict" step (renumbered Phase 0 steps), carved out `/tmp` scratch in `<determinism_contract>`, removed `.spx/audits/` references. `agents/auditor.md`: 297 → 50 lines, a thin one-off wrapper (resolve scope → map `--json`/`--markdown`/`--markdown+json` → invoke `spec-tree:auditing` → relay verbatim), no `Write` tool, no `${CLAUDE_PLUGIN_ROOT}` heredocs, no state machinery. `subagent-auditor` + `skill-auditor` REJECTED → all findings fixed before commit.

The two future-PR branches `work/audit-orchestrator` and `work/pr-review-orchestrator` are cut off `7edfdd1` and carry the pre-trim `audit_orchestrator.py` + tests + the un-slimmed `auditor.md`, so the deleted state machinery is preserved for steps 2 and 3.

### Remaining

1. **New review-prompt skill.** Duplicate the existing PR-review prompt from `outcomeeng/gh-actions` (public — `gh repo view outcomeeng/gh-actions`; the review logic lives in its reusable workflow `claude-code-review.yml@main` and the prompt it loads) into this repo as a skill. The `gh-actions` source is upstreamed once this is stable. Audit gate: `/auditing-skills`.
2. **New `agents/pr-reviewer.md`** — CI one-off agent: invoke the review-prompt skill + `spec-tree:auditing` on the PR diff, post one combined review+audit PR comment (the audit verdict embedded as the `markdown+json` carrier). Zero language-specific tokens; reaches `scripts/` only through `/auditing`. Audit gate: `/auditing-subagents`.
3. **New `.github/workflows/claude-reviewer.yml`**, modeled on `claude-code-review.yml`, running the `pr-reviewer` agent and posting the combined comment. The reusable-workflow logic is duplicated into this repo from `gh-actions` for now; upstreamed once stable. `claude-code-review.yml` stays in place transitionally — it posts a redundant review-only comment alongside the combined one and is removed once `claude-reviewer.yml` is solid.
4. **Doc updates.** Add the `pr-reviewer` agent and the review-prompt skill to the spec-tree tables in `AGENTS.md` / `CLAUDE.md`. Bump considerations: the branch already bumped `spec-tree` to `0.30.0` at branch start (a MINOR bump from `0.29.1`); that covers this PR's delta — no further bump unless `origin/main` has since advanced `spec-tree` to `0.30.x` (re-check at the rebase step).
5. **`just check`**, then rebase onto current `origin/main` (it advanced past `0dd1bf2` mid-session — re-evaluate the `spec-tree` version against the new base per `spx/local/committing-changes.md`), then push: `git push --force-with-lease` followed by `just push-marketplace` (cache preservation + post-push `validate_install`); also `git push -u origin work/audit-orchestrator work/pr-review-orchestrator`. Then `claude-code-review` re-reviews the new shape.

### Known issue, not blocking

`aggregate_verdicts.py`'s `aggregate()` produces `rows=()`, but `auditing/SKILL.md` `<verdict_format>` and `auditor.md`'s expected output both show the wrapper carrying three orchestrator rows (`automated-gates`, `test-execution`, `determinism-contract`). A `--row name=STATUS` repeatable flag on `aggregate_verdicts.py` (threaded into `aggregate(rows=...)`, with the rollup over `[r.status for r in rows] + [c.overall for c in children]`) would make the documented shape achievable. Pre-existing; flagged by an earlier bot-review round. Fold into Remaining #1–#3 or a follow-up commit.

## Step 2 — `work/audit-orchestrator`

The `audit-orchestrator` agent: a stateful auditing workflow that maintains worktree-local `.spx/audits/<lang>/<branch-slug>.md` so local agents iterate quickly and observably — a precursor to running the same policy on GitHub's opaque PR infrastructure.

This branch carries the `.spx/`-state machinery removed from step 1 (`AuditState`, `load_state` / `save_state`, `assign_finding_id`, `find_resolved_by_identity`, `reopen_finding`, `RunLock` in `audit_orchestrator.py`, plus the scenario tests). The agent reaches `scripts/` only through the `auditing` skill (which resolves it via `${CLAUDE_SKILL_DIR}`) or through a CLI added to `audit_orchestrator.py` — `base-ref`, `current-branch`, `branch-slug`, `scope-hash`, `branch-scope`, `modified-since`, `sha-reachable`, `acquire-lock`, `release-lock`, `state-transition` — that the skill invokes; never via `${CLAUDE_PLUGIN_ROOT}` in the agent body. Adds a `.spx/audits/` spec sub-node under `65-auditing.enabler` and the matching `17-auditing.adr.md` compliance text. Rebase onto current main once step 1 merges.

## Step 3 — `work/pr-review-orchestrator`

The `pr-review-orchestrator` agent: run in CI. Reads existing PR review comments (including the prior `markdown+json` audit comment via `read_verdict.py`), feeds them into the `auditing` skill, diffs new findings against the prior verdict to derive resolved/reopened, and updates the PR with a fresh `markdown+json` comment. State lives in the PR comment thread — the durable cross-CI-run surface named in `spx/15-audit-verdict-format.pdr.md` — not in `.spx/`.

New `.github/workflows/claude-review-orchestrator.yml`, modeled on step 1's `claude-reviewer.yml`. Builds on the `auditing` skill and the review-prompt skill from step 1. Adds the PR-comment ingest/persist contract to `17-auditing.adr.md`. Rebase onto current main once steps 1 and 2 merge.
