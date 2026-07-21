# ISSUES — agents conversion enabler

Coordination note; not spec truth.

## DEBT [structure]: split overloaded agent-conversion boundaries

`changes-reviewer` runs `2026-07-03_08-02-43-874-6887784d925b` and `2026-07-03_09-26-23-414-a5d4fd1ca5be` raised debt finding `F-001`: `spx/18-plugin-build.enabler/54-conversion.enabler/21-agents.enabler/agents.md` carries more than roughly seven assertions and mixes independently validated concerns:

- agent conversion output shape
- tool and policy inference
- duplicate-filename installation behavior

The reviewer cited `spx/21-spec-tree.enabler/54-decomposing.enabler/decomposing.md`, whose decomposition rule treats more than roughly seven assertions as a signal for analysis and separates independent concerns when each concern has a meaningful validation boundary.

Revisit condition: when structural work on `spx/18-plugin-build.enabler/54-conversion.enabler/21-agents.enabler` is scheduled, invoke `/decompose` on the agents node. Split the remaining conversion and policy-inference concerns into focused child nodes when the ordering-evidence matrix supports the split.

Deferral reason: this branch targets the bounded generated Codex-agent config enforcement change. The sync-order assertion was re-scoped to `spx/32-distribution.enabler/21-sync.enabler` in this branch; the remaining proposed fix is a tree-structure refactor inside the agents node.

## DEBT [evidence]: linked tests delegate every predicate to harness assertion helpers

`implementation-auditor` run `2026-07-21_05-52-33-446-37005aaf2bef` raised ten blocking findings, all one class. Every test function in this node's linked test files is a bare call to an `assert_*` helper in `outcomeeng_testing/harnesses/agent_conversion.py`, so no assertion is lexically visible in the executed test: `tests/test_agents.compliance.l1.py` carries zero lexical `assert` statements across nine tests, and `tests/test_agents.mapping.l1.py` carries zero across twenty-three.

`spx/31-outcomeeng.enabler/31-verification.enabler/31-test-verification.enabler/15-test-infrastructure.pdr.md` governs the opposite arrangement: the linked executed test owns every behavioral predicate and assertion API call, while harnesses expose observations or resource handles and never return verdicts, call assertion APIs, or expose verdict-shaped helpers. An `assert_*` helper is a verdict-shaped helper.

Resolution shape: invert the harness so each helper returns the observation and its oracle expectation, then move every predicate into the thirty-two test functions that link to it. The oracle independence the harness already provides through its PyYAML document oracle is preserved by the inversion — the harness keeps producing the independent expectation and stops rendering the verdict.

Revisit condition: the pattern spans twenty-seven of the one hundred forty-two test files under `spx/**/tests/`, so the inversion is one migration with a shared harness contract rather than a per-node repair. Schedule it as that migration and take this node's two files as its first unit.

Deferral reason: the changeset that surfaced this is a subtraction — it withdraws the Codex configured-agent identity preflight and the two spec nodes authored with it. Inverting a roughly one-thousand-line harness and thirty-two test functions inside it would more than double a reduction changeset, and the same inversion is owed across twenty-five further files that this changeset does not touch.
