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

## DEBT [standards]: the shipped placement script's line ceiling excludes script-standards additions

`instructions:skill-auditor` raised two WARNING findings against
`src/templates/plugin/scripts/place_agents.py`: it carries no `Tested with:` documentation comment
recording sample-input, expected-output, and error-case coverage, and it lets a malformed
`placement.json` surface a bare `JSONDecodeError` or `KeyError` rather than a message naming the file
and the invalid field.

Both are correct against `/skill-standards`. Both also add raw lines to a script that sits at exactly
fifty, the ceiling `spx/12-shipped-scripting.adr.md` sets before a shipped script becomes debt
awaiting extraction into the SPX CLI. The two standards pull in opposite directions on the same file,
and neither yields to the other by its own terms.

The auditor's own severity reasoning bounds the risk: `placement.json` is build-generated and
trusted, never consumer input, so the unguarded parse cannot be reached by a malformed file a
consumer authored.

**Resolution shape**: decide which standard governs a shipped script at the ceiling — raise the
ceiling for scripts carrying mandated documentation and validation, exempt those two categories from
the raw-line count, or treat reaching the ceiling as the extraction trigger the ADR describes and
move placement into the SPX CLI, leaving the skill its instruction and no script. The third option is
what the ADR already prescribes for a proven script, so this may be an extraction decision rather
than a standards conflict.

**Revisit condition**: when placement next needs a behavior change, since any addition crosses the
ceiling and forces the decision.
