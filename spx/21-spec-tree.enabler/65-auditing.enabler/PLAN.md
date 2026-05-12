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

Already landed: `verdict.py` (canonical schema + `roll_up`), `emit_verdict.py` / `read_verdict.py` / `aggregate_verdicts.py` / `pass_results.py`, the `spx/15-audit-verdict-format.pdr.md` flip to JSON + carrier+payload + format axis, the `65-verdict-toolchain.enabler` spec node + its five scenario test files, the eleven-skill marketplace alignment.

Remaining:

1. **Slim `agents/auditor.md`** to a one-off wrapper. Remove `<state_file_format>`, `<helper_invocation>` (the eight `${CLAUDE_PLUGIN_ROOT}` heredocs — broken: `${CLAUDE_PLUGIN_ROOT}` is not substituted in agent prompts and is not a shell env var), and the Phase 0/F/R `<protocol>` state machinery. Keep: accept a scope plus `--json | --markdown | --markdown+json`; invoke `spec-tree:auditing` (already declared via the `skills:` frontmatter field); forward the format to `emit_verdict.py`; emit the rendered result. The agent invokes nothing the `auditing` skill does not already resolve.
2. **Trim `scripts/audit_orchestrator.py`** to the git/scope helpers the `auditing` skill uses in Phase 0 — `detect_base_ref`, `branch_scope` / `expand_diff_range`, `compute_scope_hash`. Move the `.spx/`-state machinery — `AuditState`, `load_state` / `save_state`, `assign_finding_id`, `find_resolved_by_identity`, `reopen_finding`, `RunLock` — to `work/audit-orchestrator` (step 2). Drop the corresponding scenarios from `tests/test_auditing.scenario.l1.py`; keep the scope-hash property test.
3. **New review-prompt skill.** Duplicate the existing PR-review prompt from `outcomeeng/gh-actions` into this repo as a skill. The `gh-actions` source is upstreamed once this is stable.
4. **New `agents/pr-reviewer.md`** — CI one-off agent: invoke the review-prompt skill + `spec-tree:auditing`, post one combined review+audit PR comment.
5. **Revise `skills/auditing/SKILL.md`** as needed for the one-off flow; add a `<codex_fallback>` block for the `scripts/` paths — Codex does not substitute `${CLAUDE_SKILL_DIR}`, so the fallback says to locate `scripts/` as a sibling of this SKILL.md.
6. **New `.github/workflows/claude-reviewer.yml`**, modeled on `claude-code-review.yml`, running the `pr-reviewer` agent and posting the combined comment. The reusable-workflow logic is duplicated into this repo from `gh-actions` for now; upstreamed once stable. `claude-code-review.yml` stays in place transitionally — it posts a redundant review-only comment alongside the combined one and is removed once `claude-reviewer.yml` is solid.
7. **Rewrite `spx/21-spec-tree.enabler/65-auditing.enabler/auditing.md`** around the step-1 scope: the `auditing` skill runs the six-phase audit on a frozen scope and emits a JSON verdict conforming to `verdict.py`; the `auditor` agent invokes the skill and renders per the format flag; the scope-hash determinism property; the orchestrator rollup contract. The `.spx/`-state assertions move to step 2.
8. **Amend `spx/21-spec-tree.enabler/17-auditing.adr.md`**: the `auditing` skill owns the audit policy; the `auditor` agent is a one-off renderer; stateful local orchestration (`audit-orchestrator`) and PR-review re-auditing (`pr-review-orchestrator`) are separate agents. Remove the `.spx/audits/<lang>/<branch-slug>.md` compliance rule — that text belongs to step 2.

Audit gates: `/auditing-subagents` on `auditor.md` and `pr-reviewer.md`; `/auditing-skills` on the new review-prompt skill and the revised `auditing/SKILL.md`; `/auditing-python` plus `/auditing-python-tests` on the trimmed `audit_orchestrator.py` and its tests; `/aligning` on `auditing.md` and `17-auditing.adr.md`. Then `just check`, commit, push via `just push-marketplace`, and let `claude-code-review` re-review the new shape.

## Step 2 — `work/audit-orchestrator`

The `audit-orchestrator` agent: a stateful auditing workflow that maintains worktree-local `.spx/audits/<lang>/<branch-slug>.md` so local agents iterate quickly and observably — a precursor to running the same policy on GitHub's opaque PR infrastructure.

This branch carries the `.spx/`-state machinery removed from step 1 (`AuditState`, `load_state` / `save_state`, `assign_finding_id`, `find_resolved_by_identity`, `reopen_finding`, `RunLock` in `audit_orchestrator.py`, plus the scenario tests). The agent reaches `scripts/` only through the `auditing` skill (which resolves it via `${CLAUDE_SKILL_DIR}`) or through a CLI added to `audit_orchestrator.py` — `base-ref`, `current-branch`, `branch-slug`, `scope-hash`, `branch-scope`, `modified-since`, `sha-reachable`, `acquire-lock`, `release-lock`, `state-transition` — that the skill invokes; never via `${CLAUDE_PLUGIN_ROOT}` in the agent body. Adds a `.spx/audits/` spec sub-node under `65-auditing.enabler` and the matching `17-auditing.adr.md` compliance text. Rebase onto current main once step 1 merges.

## Step 3 — `work/pr-review-orchestrator`

The `pr-review-orchestrator` agent: run in CI. Reads existing PR review comments (including the prior `markdown+json` audit comment via `read_verdict.py`), feeds them into the `auditing` skill, diffs new findings against the prior verdict to derive resolved/reopened, and updates the PR with a fresh `markdown+json` comment. State lives in the PR comment thread — the durable cross-CI-run surface named in `spx/15-audit-verdict-format.pdr.md` — not in `.spx/`.

New `.github/workflows/claude-review-orchestrator.yml`, modeled on step 1's `claude-reviewer.yml`. Builds on the `auditing` skill and the review-prompt skill from step 1. Adds the PR-comment ingest/persist contract to `17-auditing.adr.md`. Rebase onto current main once steps 1 and 2 merge.
