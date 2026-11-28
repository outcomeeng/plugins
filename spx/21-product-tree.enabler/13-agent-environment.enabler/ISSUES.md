# Issues: Agent environment

Known defects, contradictions and gaps in this node.

## The identity and project-directory assertions describe exports the spx hook runner still writes

`21-identity.enabler/identity.md` declares session identity as the variable each agent publishes: `$CLAUDE_CODE_SESSION_ID` under Claude Code and Pi, `$CODEX_THREAD_ID` under Codex, and every skill that consumes identity reads that variable. The `$CLAUDE_ENV_FILE` exports the `spx` hook runner still writes (the session identity, the worktree claim path and the two project-directory variables) remain asserted here because the pinned floor still produces them. Asserting their absence before the floor advances would leave these tests describing a CLI the gate does not run, against the published-capability rule in the root `CLAUDE.md`. `outcomeeng/changes#117` carries the `spx` side: SPX exports nothing into any coding agent's environment.

**Settlement condition.** The `spx` CLI removes the `$CLAUDE_ENV_FILE` exports, an `@outcomeeng/spx` release carrying the removal is published, and `REQUIRED_SPX_VERSION` in `outcomeeng/validation/spx_version.py` and `SPX_VERSION` in `.github/workflows/check.yml` advance to it. No spec, decision or test then asserts the export. The `agent-environment.md` scenarios keep the worktree-occupancy claim they also assert, `identity.md` no longer says the identity is written into the agent's environment, and the evidence and the `outcomeeng_testing/harnesses/hooks.py` coverage of the export are gone. [`spx/21-product-tree.enabler/15-hook-state-delegation.adr.md`](spx/21-product-tree.enabler/15-hook-state-delegation.adr.md) and [`spx/15-hook-safety.pdr.md`](spx/15-hook-safety.pdr.md) justify the shipped hook by the worktree-occupancy claim alone, which no skill or child process can record for its parent session.

## Per-runtime wording names the agent concept

The node's specs and evidence speak of a "per-runtime session directory" where [`spx/15-agent-terminology.pdr.md`](spx/15-agent-terminology.pdr.md) requires "per-agent": the prohibited-terminology table maps `per-runtime` and `runtime-specific` to `per-agent` and `agent-specific`. "Runtime" stays valid for execution-time behavior and for an execution environment such as Python.

**Settlement condition.** The node's wording aligns to the decision's required wording, as part of the tree-wide sweep `spx/18-plugin-build.enabler/ISSUES.md` records.

## The node's harness raises AssertionError for lifecycle failures

`outcomeeng_testing/harnesses/hooks.py` raises `AssertionError` when a resource fails to start or a process fails to announce itself. The predicate-seam rule in `/test-evidence-standards` reserves assertion failures for the linked test; infrastructure raises only setup, dependency, lifecycle or execution errors, so raising `AssertionError` from infrastructure reports a failure away from every `assert` site and can read as a verdict the harness owns. Other harnesses carry the same shape, each recorded in the `ISSUES.md` of the node whose tests import it.

**Settlement condition.** Each infrastructure `AssertionError` in the harnesses this node's tests import becomes a lifecycle or dependency error type the harness owns, with every behavioral predicate left in the linked tests, and the node passes its test-evidence audit. The `RuntimeError` subclass that the harness of `spx/13-infrastructure.enabler/13-host-readiness.enabler` raises from a harness-owned horizon is the model.

## `l1` tests cross an `l2` boundary

**Evidence:** A run of every `l1` test file of the Product Tree at commit `744cf8cf23`, traced through the Python audit events of each test's setup, call and teardown, records that these `l1` files cross a boundary [`l1-boundaries`](spx/31-outcomeeng.enabler/31-verification.enabler/31-test-verification.enabler/21-evidence-types.pdr.md) places at `l2`:

- `tests/test_agent_environment.scenario.l1.py`: write a file, start a process

**Impact:** Each run of these files starts processes or writes into temporary trees on the host every Position shares, so local and CI gates spend that load on every run.

**Settlement condition:** Each listed file covers the same linked Assertions in process, with no lower line or branch coverage of this Node's code, or the evidence that needs the boundary stands in an `l2` file written for it.
