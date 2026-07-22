# Issues: Selected Gate

## Full-gate selection runs untargeted pytest

`just check` treats any path matching the selected-gate full-gate surface as
permission to run `CHECK_RECIPES`. `CHECK_RECIPES` includes the untargeted
pytest-backed `TEST_RECIPE`, so a local selected gate can pay full pytest cost
for a changeset whose changed surface is Markdown, spec text, skill prose, or
another non-test-bearing surface.

The selected local gate preserves time-to-value:

- Markdown, spec, and skill prose changes run the formatting, Markdown/spec,
  skill, docs, and generated-output validation steps that cover those files.
- Pytest runs only when changed paths include `[test]` evidence, test-runner
  wiring, implementation/runtime code that requires test evidence, or another
  source contract the governing node maps to pytest coverage.
- `just check-full` and CI remain the full validation-plus-full-pytest
  regression gate.

Revisit condition: update `outcomeeng.validation.selected_gate` and the
selected-gate tests so selecting a full validation surface does not
automatically imply untargeted pytest for Markdown-only or other
non-pytest-bearing changes.

## Gate-step path selection duplicates the generated-sources declaration

`outcomeeng/validation/selected_gate.py` selects gate steps from hardcoded `dist/claude/**`, `dist/codex/**`, and instruction-block path lists that duplicate relations 1 and 2 of `spx/local/generated-sources.toml`, while `spx/31-outcomeeng.enabler/31-verification.enabler/15-generated-attribution.pdr.md` makes the committed declaration the single source of generated-path knowledge for verifiers and consumers.

**Resolution shape**: derive the selector's generated-path patterns from `spx/local/generated-sources.toml`. The migration and the superseding `spx` verification scope projection are tracked in `spx/31-outcomeeng.enabler/31-verification.enabler/PLAN.md`.

## DEBT [evidence]: this node's linked tests hold every predicate in their harnesses

All three of this node's linked tests delegate their whole body to a harness that owns the assertion calls, so none carries a predicate a reader can see: `test_selected_gate.mapping.l1.py::test_selected_gate_mapping_contract` to `assert_selected_gate_mapping_contract` (roughly fifty assertion calls across sixteen changed-path cases), `test_selected_gate.property.l1.py::test_selection_is_deterministic_for_path_order_and_duplicates` to `assert_selected_gate_selection_is_deterministic` (whose nested closure holds the changed-path, full-gate, and ordered-argv comparisons), and `test_selected_gate.compliance.l1.py::test_selected_gate_compliance_contract` to `assert_selected_gate_compliance_contract` (both compliance rules, including the nested git-discovery-failure assertions). `spx/31-outcomeeng.enabler/31-verification.enabler/31-test-verification.enabler/15-test-infrastructure.pdr.md` governs the opposite arrangement: the linked executed test owns every behavioral predicate and assertion API call, while a harness exposes observations and never calls an assertion API. An `assert_*` helper is a verdict-shaped helper.

Resolution shape: give each case an observation helper returning the selected steps beside their independently derived expectation, as `template_script_gate_mapping` already does, then move every comparison into its own test function. The same inversion is tracked for the agent-conversion node in `spx/18-plugin-build.enabler/54-conversion.enabler/21-agents.enabler/ISSUES.md`; both are instances of one repository-wide migration rather than a defect this node introduced.
