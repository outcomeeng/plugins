# PLAN: Build the `spx-doctor` diagnostic skill

This node governs the `spx-doctor` skill — a portable environment doctor for any spec-tree / spx environment. The spec declares the first slice; this note tracks the remaining authoring work and the deferred checks. Coordination only; the spec and its `[eval]`/`[audit]` evidence are the truth.

## Resolved decisions

- **Architecture — thin skill over existing `spx`/harness surfaces.** The skill orchestrates existing commands (`spx worktree status`, harness env vars, and later `spx session list` / marketplace listing) and classifies their output in its body. It ships in this repository now. Per `spx/12-shipped-scripting.adr.md`, a check that outgrows light orchestration extracts into the `spx` CLI then — not preemptively. No new `spx doctor` CLI subcommand in this slice.
- **First slice — seed + `spx` reachability/version.** The `SessionStart`-hook session-environment check (working / identity-only / silent no-op) plus the `spx`-on-PATH-and-version-floor check. Heavier checks are deferred (below).

## First-slice authoring steps

1. `/contextualize spx/43-develop.enabler` (the skill-authoring node) before touching skill mechanics.
2. Author the skill with `develop:create-skills`. Keep the shipped body portable — no product-internal node paths inside it; the node references in this note are coordination only.
   - Session-environment check: read `CLAUDE_SESSION_ID`, `CLAUDE_WORKTREE_CLAIMED`, `CLAUDE_PROJECT_DIR`, and `spx worktree status --format json`; classify per the table below. The contract is the same env-var + `spx worktree status` round-trip already proven by `spx/21-spec-tree.enabler/13-agent-environment.enabler/tests/test_agent_environment.scenario.l3.py` — reuse it, do not re-derive.
   - spx-reachability check: probe `spx` on PATH and compare its reported version to the consumer's declared minimum; classify reachable-and-current / reachable-below-floor / unreachable.
   - Aggregate into one report: a named verdict per check plus an overall verdict, each verdict carrying a remediation hint.
3. Write the `[eval]` evidence with `/test` for the three behavior assertions (`evals/session-environment-check/`, `evals/spx-reachability-check/`, `evals/diagnostic-report/`), and confirm the `[audit]` assertions. Remove the node from `spx/EXCLUDE` once evidence exists.
4. Gate every changed skill with `develop:skill-auditor` (`/audit-skills`) and the node with `spec-auditor` / `test-evidence-auditor`.
5. `just build-skills`, run the narrow validation lane, then `/merge`.

### Session-environment classification table

| Reading                                               | Verdict                                                                                                                                  |
| ----------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------- |
| `id`=UUID, `claimed=1`, `proj` set, status `occupied` | **working** — the hook reached spx, which wrote identity + project dirs and claimed the worktree; spx recognizes the claim               |
| `id`=UUID, `claimed=UNSET`, status `unclaimed`        | **identity-only** — an older, pre-delegation hook is active for this session, not the spx-delegating hook                                |
| `id=UNSET`, status `unclaimed`                        | **silent no-op** — `spx` not on the hook's PATH, or `SPECTREE_SESSION_HOOK_DISABLED=1` is set; fail-open, but session identity is absent |

The strongest single signal is `spx worktree status` = `occupied` together with `CLAUDE_WORKTREE_CLAIMED=1`: that pair is reachable only if the hook reached spx, spx claimed the worktree, and the claim's controlling process (the live session) is alive.

## Deferred checks (follow-up slices)

Each grows the report by extension; the heavier ones are the candidates `spx/12-shipped-scripting.adr.md` would push into the `spx` CLI once they prove themselves.

- **Marketplace install state** — are the expected plugins installed at the expected versions on both the Claude and Codex surfaces.
- **Worktree-pool health** — is the checkout a compliant single working tree or bare-repository pool, and are any worktree claims stale.
- **Session-store sanity** — `.spx/sessions/` `todo`/`doing`/`archive` consistency, and orphaned `doing` claims whose holding process is dead.
