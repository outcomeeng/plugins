# Issues: Agent environment

Known defects, contradictions and gaps in this node. Coordination note; not spec truth.

## The identity and project-directory assertions describe exports the spx hook runner still writes

`21-identity.enabler/identity.md` declares session identity as the variable each agent publishes: `$CLAUDE_CODE_SESSION_ID` under Claude Code and Pi, `$CODEX_THREAD_ID` under Codex, and every skill that consumes identity reads that variable. The `$CLAUDE_ENV_FILE` exports the `spx` hook runner still writes (the session identity, the worktree claim path and the two project-directory variables) remain asserted here because the pinned floor still produces them. Asserting their absence before the floor advances would leave these tests describing a CLI the gate does not run, against the published-capability rule in the root `CLAUDE.md`. `outcomeeng/changes#117` carries the `spx` side: SPX exports nothing into any coding agent's environment.

`21-identity.enabler/identity.md` still says that a `PLAN.md` in this node records the export's retirement; this entry records it, and the sentence points here when the spec next changes.

**Settlement condition.** The `spx` CLI removes the `$CLAUDE_ENV_FILE` exports, an `@outcomeeng/spx` release carrying the removal is published, and `REQUIRED_SPX_VERSION` in `outcomeeng/validation/spx_version.py` and `SPX_VERSION` in `.github/workflows/check.yml` advance to it. One changeset then retires the export assertions, re-deriving each edit against the current default branch:

- the `l1` scenario that asserts `CLAUDE_SESSION_ID` reaches `$CLAUDE_ENV_FILE` and the `l3` scenario that asserts `CLAUDE_SESSION_ID`, `CLAUDE_PROJECT_DIR` and `PROJECT_DIR` in `agent-environment.md`, keeping the worktree-occupancy claim each also asserts;
- the `PROVIDES` line's "written into the agent's environment at session start" and the scenario, property and mapping assertions that cover the export in `identity.md`;
- the evidence in `tests/test_agent_environment.scenario.l1.py`, `tests/test_agent_environment.scenario.l3.py`, `21-identity.enabler/tests/test_identity.scenario.l1.py`, `test_identity.property.l1.py`, `test_identity.mapping.l1.py` and `outcomeeng_testing/harnesses/hooks.py`;
- in `spx/21-spec-tree.enabler/15-hook-state-delegation.adr.md`, the identity and project-directory writes in its opening statement, its invariants and its audit assertion, and in `spx/15-hook-safety.pdr.md`, the canonical-case clause that names the env-file identity export as the justification for shipping a hook; the surviving justification is the worktree-occupancy claim, which no skill or child process can record for its parent session. Both decisions carry their own auditor gate, so they belong in the same changeset.

## Per-runtime wording names the agent concept

The node's specs and evidence speak of a "per-runtime session directory" where `spx/15-agent-terminology.pdr.md` requires "per-agent": the prohibited-terminology table maps `per-runtime` and `runtime-specific` to `per-agent` and `agent-specific`. "Runtime" stays valid for execution-time behavior and for an execution environment such as Python.

**Settlement condition.** The node's wording aligns to the decision's required wording, as part of the tree-wide sweep `spx/18-plugin-build.enabler/ISSUES.md` records.

## The node's harness raises AssertionError for lifecycle failures

`outcomeeng_testing/harnesses/hooks.py` raises `AssertionError` when a resource fails to start or a process fails to announce itself. The predicate-seam rule in `/test-evidence-standards` reserves assertion failures for the linked test; infrastructure raises only setup, dependency, lifecycle or execution errors, so raising `AssertionError` from infrastructure reports a failure away from every `assert` site and can read as a verdict the harness owns. Other harnesses carry the same shape, each recorded in the `ISSUES.md` of the node whose tests import it.

**Settlement condition.** Each infrastructure `AssertionError` in the harnesses this node's tests import becomes a lifecycle or dependency error type the harness owns, with every behavioral predicate left in the linked tests, and the node passes its test-evidence audit. The `RuntimeError` subclass that the harness of `spx/13-infrastructure.enabler/13-host-readiness.enabler` raises from a harness-owned horizon is the model.
