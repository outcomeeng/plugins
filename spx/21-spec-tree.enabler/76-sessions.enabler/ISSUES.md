# Issues: Sessions

## 1. Remaining executable sessions tests own reusable evidence data

`test-evidence-auditor` reported source-ownership defects in the remaining executable sessions tests:

- `spx/21-spec-tree.enabler/76-sessions.enabler/tests/test_sessions.scenario.l1.py` owns JSON header/body assembly and reusable handoff payload state inside the assertion file.
- `spx/21-spec-tree.enabler/76-sessions.enabler/tests/test_pickup_verification.mapping.l1.py` owns the finite claim-verdict case domain and expected verdicts inside the assertion file.
- `spx/21-spec-tree.enabler/76-sessions.enabler/tests/test_pickup_verification.compliance.l1.py` owns runner-policy constants and reusable evidence data inside the assertion file.

Required handling:

- Move reusable handoff command orchestration, payload builders, finite mapping cases, and runner-policy values into source-owned test infrastructure under `outcomeeng_testing/harnesses/` or the matching source contract.
- Keep the assertion files as declaration-screen evidence over the source-owned contracts.
- Re-run `uv run pytest spx/21-spec-tree.enabler/76-sessions.enabler/tests` and a `test-evidence-auditor` audit for `spx/21-spec-tree.enabler/76-sessions.enabler`.

## 2. Claim-verification extraction awaits a published SPX CLI capability

`src/plugins/spec-tree/skills/pickup/scripts/verify_session_claims.py` runs to 376 lines — reconciliation of a handoff session's recorded claims against current repository state, resolving each claim to exactly one verdict (`Confirmed`, `Discrepancy`, `Unverifiable`) and emitting the verdicts as JSON for `/pickup` to render. Past fifty lines `spx/12-shipped-scripting.adr.md` makes a shipped script debt whose logic moves into the SPX CLI once the script proves its value; the verifier has proven its value in use, so extraction is what it owes.

The extraction is a cross-repo port into `@outcomeeng/spx`, a separate product, and the plugins product may depend on the resulting capability only once it is published to npm and `REQUIRED_SPX_VERSION` advances to it. That sequencing puts the fix outside any changeset confined to this repository. The session store this script reconciles against is already SPX-owned, so the port moves claim verification beside the state it reads.

**Resolution shape**: port claim reconciliation and the three-verdict resolution into the SPX CLI beside `spx session`, publish it, advance the floor, and reduce the shipped skill to its instruction with no script. Preserve the total verdict mapping across the move — every recorded claim resolves to exactly one verdict, and an unverifiable check stays distinguishable from a discrepancy. Revisit when the capability publishes.
