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

