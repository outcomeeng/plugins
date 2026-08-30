# ISSUES — agents conversion enabler

Coordination note; not spec truth.

## DEBT [consistency]: reassess `permissionMode` mapping for plugin-shipped agents

`changes-reviewer` run `2026-07-03_15-20-18-970-ba8ba57733e4` and CI review comment `2026-07-03T15:40:38Z` raised that Claude Code plugin-shipped agents do not support `permissionMode` frontmatter, while this node still specifies and tests `permissionMode` to Codex `sandbox_mode` mapping.

The question is open, not settled. `PERMISSION_MODE_MAPPINGS` in `outcomeeng/distribution/agents.py` has since widened rather than narrowed — it gained `default`, `auto`, `dontAsk`, and `bypassPermissions` entries and a `Mapping[str, str | None]` annotation, so more source values now resolve through the converter than when the question was first raised. The mapping assertion in `agents.md` is unchanged. No decision record keeps or removes the surface.

Revisit condition: when structural work on `spx/18-plugin-build.enabler/54-conversion.enabler/21-agents.enabler` is scheduled, decide whether `permission_mode`, `PERMISSION_MODE_MAPPINGS`, and the associated mapping tests belong in the plugin-agent conversion path or should be removed in favor of tool-derived Codex policy config only.

Deferral reason: removing or re-scoping `permissionMode` changes the converter's declared frontmatter surface and belongs with the planned agent-conversion boundary split above, not with a changeset that withdraws an unrelated protocol.

## DEBT [evidence]: linked tests delegate every predicate to harness assertion helpers

`implementation-auditor` run `2026-07-21_05-52-33-446-37005aaf2bef` raised ten blocking findings, all one class. Every test function in this node's linked test files is a bare call to an `assert_*` helper in `outcomeeng_testing/harnesses/agent_conversion.py`, so no assertion is lexically visible in the executed test: `tests/test_agents.compliance.l1.py` carries zero lexical `assert` statements across nine tests, and `tests/test_agents.mapping.l1.py` carries zero across twenty-three.

`spx/31-outcomeeng.enabler/31-verification.enabler/31-test-verification.enabler/15-test-infrastructure.pdr.md` governs the opposite arrangement: the linked executed test owns every behavioral predicate and assertion API call, while harnesses expose observations or resource handles and never return verdicts, call assertion APIs, or expose verdict-shaped helpers. An `assert_*` helper is a verdict-shaped helper.

Resolution shape: invert the harness so each helper returns the observation and its oracle expectation, then move every predicate into the thirty-two test functions that link to it. The oracle independence the harness already provides through its PyYAML document oracle is preserved by the inversion — the harness keeps producing the independent expectation and stops rendering the verdict.

Revisit condition: the pattern spans twenty-seven of the one hundred forty-two test files under `spx/**/tests/`, so the inversion is one migration with a shared harness contract rather than a per-node repair. Schedule it as that migration and take this node's two files as its first unit.

Deferral reason: the changeset that surfaced this is a subtraction — it withdraws the Codex configured-agent identity preflight and the two spec nodes authored with it. Inverting a roughly one-thousand-line harness and thirty-two test functions inside it would more than double a reduction changeset, and the same inversion is owed across twenty-five further files that this changeset does not touch.
