# Known issues — source and templating enabler

## FOLLOW-UP [evidence]: require_skill target-equivalence assertion is implicit

The compliance assertion says `{!% require_skill 'plugin:skill' %!}` expands to
identical coding-agent-neutral invocation text in both targets. Current tests
verify that the directive expands and that the rendered text names the required
skill, but they do not explicitly compare Claude-target and Codex-target output
bytes for the same source input.

The implementation guarantee is structural: `expand_require_skill` has no target
parameter, and target-specific path rewriting does not change the expansion
because the text contains no `${CLAUDE_SKILL_DIR}` token. Future evidence work in
this node should add a direct two-target comparison so the assertion remains
visible from the tests rather than only from source structure.

## FOLLOW-UP [architecture]: `scenarios.py` is filed under `harnesses/` but is not a harness

`outcomeeng_testing/harnesses/scenarios.py` exposes frozen `IncludeScenario`
dataclass instances (`SCENARIO_SIMPLE_INCLUDE`, `SCENARIO_MULTILINE_INCLUDE`)
carrying invented `fragment_body` payloads and the queries tests run against
them. Per `spx/15-test-infrastructure.pdr.md` Category Semantics, a harness
mediates resources and lifecycle; this module manages no resources — it is a
named whole-payload scenario bag closer to an inert fixture (or a generator if
the shapes should vary). The test-evidence audit flagged the mislabeling while
confirming it commits none of the PDR's prohibitions (it owns no source-owned
domain truth and replaces no behavior under test).

Required handling: decide the correct category for `scenarios.py` (inert fixture
vs. generator), move it to the matching `outcomeeng_testing/` subdirectory, and
update the imports in `test_expand_include.scenario.l1.py` and
`test_render_text.scenario.l1.py`. Deferred as a separate test-infrastructure
refactor rather than folded into the governance-inventory changeset.

Surfaced by the test-evidence audit during the test-infrastructure governance
inventory.
