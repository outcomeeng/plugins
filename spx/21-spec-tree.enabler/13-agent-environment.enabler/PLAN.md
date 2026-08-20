# Plan: Agent Environment

## Retire the env-file identity and project-dir assertions

Governing artifacts: `spx/21-spec-tree.enabler/15-hook-state-delegation.adr.md`,
`spx/15-hook-safety.pdr.md`, and this node's own spec.

`spx/21-spec-tree.enabler/13-agent-environment.enabler/21-identity.enabler/identity.md`
now declares session identity as the variable each agent publishes —
`$CLAUDE_CODE_SESSION_ID` under Claude Code and Pi, `$CODEX_THREAD_ID` under Codex — and every
skill that consumes identity reads that variable. The `$CLAUDE_ENV_FILE` exports the
`spx` hook runner still writes remain asserted here because the pinned floor still
produces them.

### Gate — start only when all hold

1. The `spx` CLI removes the `$CLAUDE_ENV_FILE` exports — the session identity, the
   worktree claim path, and the two project-directory variables.
2. An `@outcomeeng/spx` release carrying that removal is published to npm.
3. `REQUIRED_SPX_VERSION` (`outcomeeng/validation/spx_version.py`) and `SPX_VERSION`
   (`.github/workflows/check.yml`) are advanced to that published release.

Asserting the absence before the floor advances would leave these tests describing a CLI
the gate does not run, per the published-capability rule in the root `CLAUDE.md`.

### Worklist — re-derive exact edits against current `main`

Specs:

- `spx/21-spec-tree.enabler/13-agent-environment.enabler/agent-environment.md` — the
  `l1` scenario asserting `CLAUDE_SESSION_ID` reaches `$CLAUDE_ENV_FILE`, and the `l3`
  scenario asserting `CLAUDE_SESSION_ID`, `CLAUDE_PROJECT_DIR`, and `PROJECT_DIR`. The
  worktree-occupancy claim each scenario also asserts survives the change and stays.
- `spx/21-spec-tree.enabler/13-agent-environment.enabler/21-identity.enabler/identity.md`
  — the `PROVIDES` line's "written into the agent's environment at session start", and
  the scenario, property, and mapping assertions covering the export.

Evidence:

- `spx/21-spec-tree.enabler/13-agent-environment.enabler/tests/test_agent_environment.scenario.l1.py`
- `spx/21-spec-tree.enabler/13-agent-environment.enabler/tests/test_agent_environment.scenario.l3.py`
- `spx/21-spec-tree.enabler/13-agent-environment.enabler/21-identity.enabler/tests/test_identity.scenario.l1.py`
- `spx/21-spec-tree.enabler/13-agent-environment.enabler/21-identity.enabler/tests/test_identity.property.l1.py`
- `spx/21-spec-tree.enabler/13-agent-environment.enabler/21-identity.enabler/tests/test_identity.mapping.l1.py`
- `outcomeeng_testing/harnesses/hooks.py`

Decisions, once the hook's remaining effect is the worktree-occupancy claim alone:

- `spx/21-spec-tree.enabler/15-hook-state-delegation.adr.md` — the identity and
  project-dir writes named in its opening statement, its invariants, and its audit
  assertion.
- `spx/15-hook-safety.pdr.md` — the canonical-case clause naming the env-file identity
  export as the justification for shipping a hook. The rule it illustrates is unchanged;
  the surviving justification is the worktree-occupancy claim, which no skill or child
  process can record for its parent session.

Both decisions carry their own auditor gate, so they belong in the same changeset as the
spec and evidence alignment rather than a later sweep.
