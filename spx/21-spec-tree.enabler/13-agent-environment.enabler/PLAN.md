# PLAN: Create an `spx-doctor` diagnostic skill

Create a new skill — working name `spx-doctor` (a `/spx-doctor` command, or an `/spx doctor`-style invocation) — that diagnoses the health of a spec-tree / spx environment and reports a clear, named verdict per check plus a remediation hint. It is the self-serve form of an interrogation a user would otherwise have to remember and type by hand. The skill is consumer-facing and portable: it reasons only about surfaces every consumer has (the `spx` CLI, harness env vars, the install state), never this product's internal node addresses.

## Seed diagnostic: SessionStart hook health

The first check — and the reason the skill exists now — verifies the spec-tree `SessionStart` hook actually fired for the current session. The hook delegates to `spx hook run session-start`, which writes the session env vars and records the worktree-occupancy claim. The check reads the three observable traces and classifies:

```bash
echo "id=${CLAUDE_SESSION_ID:-UNSET}  claimed=${CLAUDE_WORKTREE_CLAIMED:-UNSET}  proj=${CLAUDE_PROJECT_DIR:-UNSET}"
spx worktree status --format json      # run from inside the repo worktree
```

| Reading                                               | Verdict                                                                                                                                                                      |
| ----------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `id`=UUID, `claimed=1`, `proj` set, status `occupied` | **working** — the hook reached spx, which wrote identity + project dirs and claimed the worktree; spx itself recognizes the claim (the round-trip)                           |
| `id`=UUID, `claimed=UNSET`, status `unclaimed`        | **identity-only** — an older, pre-delegation hook is active for this session, not the spx-delegating hook                                                                    |
| `id=UNSET`, status `unclaimed`                        | **silent no-op** — `spx` not on the hook's PATH, or the kill switch `SPECTREE_SESSION_HOOK_DISABLED=1` is set; fail-open means nothing broke, but session identity is absent |

The strongest single signal is `spx worktree status` = `occupied` together with `CLAUDE_WORKTREE_CLAIMED=1`: that pair is reachable only if the hook reached spx, spx claimed the worktree, and the claim's controlling process (the live session) is alive.

This diagnostic's contract is already proven by the L3 test `tests/test_agent_environment.scenario.l3.py`, which exercises the same env-var + `spx worktree status` round-trip against the real `spx` CLI. The skill reuses that contract as a live self-check rather than re-deriving it.

## Beyond the seed (extensible)

The skill grows into a broader environment doctor — each diagnostic a named check with a working / degraded / broken verdict and a remediation hint, aggregated into one report. Candidate checks:

- **spx reachability and version** — is `spx` on `PATH`, where it resolves, and is its version at or above the floor the installed skills depend on (the floor lives in `outcomeeng/validation/spx_version.py` for this product; consumers compare against their own installed plugin's declared minimum).
- **Marketplace install state** — are the expected plugins installed at the expected versions on both the Claude and Codex surfaces.
- **Worktree pool health** — is the checkout a compliant single working tree or bare-repository pool, and are any worktree claims stale.
- **Session store sanity** — `.spx/sessions/` `todo`/`doing`/`archive` consistency, and orphaned `doing` claims whose holding process is dead.

## Next steps for the implementing agent

1. `/understand`, then `/contextualize spx/21-spec-tree.enabler/13-agent-environment.enabler` (this seed node) and the develop skill-authoring node.
2. Decide the skill's home node via `/decompose` / `/author` — likely a new diagnostics enabler under `spx/21-spec-tree.enabler/`, since the skill spans more than agent-environment; move this seed content there and remove this PLAN.md from the agent-environment node once the skill's node exists.
3. Author the skill with `develop:create-skills`, gate with `develop:skill-auditor` (`/audit-skills`), starting with the SessionStart-hook diagnostic above and structured so checks are added incrementally.
4. Keep the shipped skill body portable — no product-internal node paths inside it; the node references in this PLAN are coordination only.
