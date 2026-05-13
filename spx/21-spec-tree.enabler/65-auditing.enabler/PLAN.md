# PLAN — auditing toolchain: three-step rollout

The audit capability lands in three steps. The `auditing` skill owns the audit policy: the six-phase run, language-partition dispatch, aggregation, and JSON-verdict emission through the toolchain in `scripts/`. Agents wrap the skill — they never invoke `scripts/` through a path the skill does not already resolve.

Naming: agents that run only the audit are `audit*` (`auditor`, `audit-orchestrator`); agents that bundle the existing PR-review prompt with the audit are `*review*` (`pr-reviewer`, `pr-review-orchestrator`) — review is the umbrella, the audit is one part of it. Bare name = one-off, no persisted state; `-orchestrator` suffix = stateful, tracks finding resolution across runs. A workflow mirrors the agent it runs: `claude-` prefix, agent name without the `pr-` prefix.

| Agent                    | Step                              | Runs in                               | Job                                                                                                          | State surface                               |
| ------------------------ | --------------------------------- | ------------------------------------- | ------------------------------------------------------------------------------------------------------------ | ------------------------------------------- |
| `auditor`                | 1 (this branch)                   | local                                 | one-off: invoke `auditing` on a scope, render per `--json` / `--markdown` / `--markdown+json`                | none                                        |
| `pr-reviewer`            | 1 (this branch)                   | CI (`claude-reviewer.yml`)            | one-off: invoke the review-prompt skill + `auditing`, post one combined review+audit PR comment              | none                                        |
| `audit-orchestrator`     | 2 (`work/audit-orchestrator`)     | local                                 | stateful: maintain `.spx/audits/<lang>/<branch-slug>.md` across commits; observable precursor to CI          | `.spx/audits/` (gitignored, worktree-local) |
| `pr-review-orchestrator` | 3 (`work/pr-review-orchestrator`) | CI (`claude-review-orchestrator.yml`) | stateful: ingest existing PR review comments → feed `auditing` → update the PR via a `markdown+json` comment | PR comment thread                           |

## Step 1 — `auditor` half landed in PR #11 (merged 2026-05-13); `pr-reviewer` half deferred

PR #11 (commit `27c95e8` on `main`) shipped the verdict toolchain plus the one-off **local** `auditor` agent. The one-off **CI** `pr-reviewer` agent that the table above pairs with it is **not yet landed** — it lives on `work/pr-reviewer` and ships in a follow-up PR.

### Landed in PR #11

- **Verdict toolchain** in `plugins/spec-tree/skills/auditing/scripts/`: `verdict.py` (canonical schema + `roll_up`), `emit_verdict.py`, `read_verdict.py`, `aggregate_verdicts.py`, `pass_results.py`, plus the trimmed `audit_orchestrator.py` (887 → 168 lines: kept `compute_scope_hash`, `expand_diff_range`, `branch_scope`, `detect_base_ref`, `uncommitted_scope`; removed `AuditState` / `RunLock` / finding-resolution machinery — preserved on `work/audit-orchestrator` for step 2).
- **Decision records**: `spx/15-audit-verdict-format.pdr.md` flipped to JSON + carrier+payload + three-format axis (`markdown`, `markdown+json`, `json-only`); `spx/21-spec-tree.enabler/17-auditing.adr.md` amended (skill owns policy, agents are wrappers, `${CLAUDE_SKILL_DIR}` vs `${CLAUDE_PLUGIN_ROOT}` constraint codified); `spx/13-plugin-and-runtime-conventions.adr.md` extended with the scratch-storage rules (`tempfile.mkdtemp` / `mktemp -d` / `tmp_path`, caller-owned cleanup, pipes-over-files).
- **Spec nodes + tests**: `spx/21-spec-tree.enabler/32-evidence.enabler/65-verdict-toolchain.enabler/` (111 toolchain scenario tests across `test_verdict`, `test_emit_verdict`, `test_read_verdict`, `test_aggregate_verdicts`, `test_pass_results`; `tests/_helpers.py` + `tests/conftest.py` extracting `SCRIPTS_DIR`, `JSON_BLOCK_BEGIN`/`END`, `run_script`); `spx/21-spec-tree.enabler/65-auditing.enabler/tests/test_auditing.scenario.l1.py` extended with `uncommitted_scope` coverage. 366 tests pass across the suite.
- **Skill + agent alignment**: 11 audit skills aligned to the JSON-verdict schema (develop×3, python×2, rust×2, typescript×2, spec-tree×2); `agents/auditor.md` slimmed to a 50-line one-off wrapper that reaches `scripts/` only through the `/auditing` skill.
- **Plugin bump**: `spec-tree` 0.29.1 → 0.30.0 (initial) → 0.31.0 (after rebase past PR #10).

### Deferred to `work/pr-reviewer` (step 1's CI half — next PR)

1. **New review-prompt skill** under `plugins/spec-tree/skills/`. Duplicate the existing PR-review prompt from `outcomeeng/gh-actions` (the reusable workflow `claude-code-review.yml@main` and the prompt it loads) into this repo as a skill. Upstreamed once stable. Audit gate: `/auditing-skills`.
2. **New `agents/pr-reviewer.md`** — CI one-off agent: invokes the review-prompt skill + `spec-tree:auditing` on the PR diff and posts one combined review+audit PR comment (audit verdict embedded as the `markdown+json` carrier). Zero language-specific tokens; reaches `scripts/` only through `/auditing`. Audit gate: `/auditing-subagents`.
3. **New `.github/workflows/claude-reviewer.yml`**, modeled on `claude-code-review.yml`, running the `pr-reviewer` agent and posting the combined comment. `claude-code-review.yml` stays in place transitionally — it posts a redundant review-only comment alongside the combined one and is removed once `claude-reviewer.yml` is solid.
4. **Doc updates**. Add the `pr-reviewer` agent and the review-prompt skill to the spec-tree tables in `AGENTS.md` / `CLAUDE.md`.
5. **Rebase `work/pr-reviewer` onto current main (`27c95e8`)** before resuming — the branch was cut pre-trim and carries the un-slimmed `auditor.md` plus the deleted state machinery. After rebase, drop anything that conflicts with PR #11's slim shape and keep only the review-prompt skill + `pr-reviewer` agent + `claude-reviewer.yml`.

## Step 2 — `work/audit-orchestrator`

The `audit-orchestrator` agent: a stateful auditing workflow that maintains worktree-local `.spx/audits/<lang>/<branch-slug>.md` so local agents iterate quickly and observably — a precursor to running the same policy on GitHub's opaque PR infrastructure.

This branch carries the `.spx/`-state machinery removed from step 1 (`AuditState`, `load_state` / `save_state`, `assign_finding_id`, `find_resolved_by_identity`, `reopen_finding`, `RunLock` in `audit_orchestrator.py`, plus the scenario tests). The agent reaches `scripts/` only through the `auditing` skill (which resolves it via `${CLAUDE_SKILL_DIR}`) or through a CLI added to `audit_orchestrator.py` — `base-ref`, `current-branch`, `branch-slug`, `scope-hash`, `branch-scope`, `modified-since`, `sha-reachable`, `acquire-lock`, `release-lock`, `state-transition` — that the skill invokes; never via `${CLAUDE_PLUGIN_ROOT}` in the agent body. Adds a `.spx/audits/` spec sub-node under `65-auditing.enabler` and the matching `17-auditing.adr.md` compliance text.

**Rebase onto current main (`27c95e8`) before resuming.** PR #11 reshaped `audit_orchestrator.py`, the `auditing` skill body, ADR 17, and ADR 13 — the side branch will conflict. Re-introduce only the state machinery that step 2 actually needs; do not re-introduce anything PR #11 explicitly removed (e.g., `${CLAUDE_PLUGIN_ROOT}` heredocs in agent prompts).

## Step 3 — `work/pr-review-orchestrator`

The `pr-review-orchestrator` agent: run in CI. Reads existing PR review comments (including the prior `markdown+json` audit comment via `read_verdict.py`), feeds them into the `auditing` skill, diffs new findings against the prior verdict to derive resolved/reopened, and updates the PR with a fresh `markdown+json` comment. State lives in the PR comment thread — the durable cross-CI-run surface named in `spx/15-audit-verdict-format.pdr.md` — not in `.spx/`.

New `.github/workflows/claude-review-orchestrator.yml`, modeled on step 1's `claude-reviewer.yml`. Builds on the `auditing` skill and the review-prompt skill from step 1. Adds the PR-comment ingest/persist contract to `17-auditing.adr.md`.

**Rebase onto current main (`27c95e8`) once steps 1's `pr-reviewer` half and step 2 land.** The branch was cut pre-trim and will conflict with PR #11's reshaping of the skill and ADRs.
