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

`outcomeeng/validation/selected_gate.py` selects gate steps from hardcoded `dist/claude/**`, `dist/codex/**`, and instruction-block path lists that duplicate relations 1 and 2 of `spx/local/generated-sources.toml`, while [`spx/31-outcomeeng.enabler/31-verification.enabler/15-generated-attribution.pdr.md`](spx/31-outcomeeng.enabler/31-verification.enabler/15-generated-attribution.pdr.md) makes the committed declaration the single source of generated-path knowledge for verifiers and consumers.

**Resolution shape**: derive the selector's generated-path patterns from `spx/local/generated-sources.toml`. The migration is deferred because it is an implementation change with its own test evidence in the validation infrastructure, and the `spx` verification scope projection partly supersedes the selector's consumption of the declaration; revisit the migration scope when that projection lands. `spx/31-outcomeeng.enabler/31-verification.enabler/ISSUES.md` records the agentic-runner side of the same projection.

## DEBT [evidence]: the lane-mapping oracle reuses the production lane table `spx/15-validation.enabler/65-gate.enabler/21-selected-gate.enabler/tests/test_selected_gate.mapping.l1.py`, `_lane_steps`, `evidence`

Defect class: `oracle-independence`.

Finding: the helper `_lane_steps` in `spx/15-validation.enabler/65-gate.enabler/21-selected-gate.enabler/tests/test_selected_gate.mapping.l1.py` computes the expected `(argv, reason)` set from `VALIDATION_LANES` in `outcomeeng/validation/selected_gate.py`, the same table `build_selected_gate_plan` iterates to choose steps. The assertion that changed repository paths map to a deterministic ordered subset of source-owned validation steps, each with a human-readable reason, therefore has no oracle independent of the production path for the category-to-step correspondence: a defect in the table moves the expectation and the selection together. Only the path-to-category classification is independent, because git's pathspec matcher supplies it.

Remediation target: an independent oracle. The test states the category-to-step correspondence from a source the lane table does not feed, such as a hand-authored correspondence the spec declares.

Settlement condition: a mutation of a `VALIDATION_LANES` entry fails the mapping test, because the expected steps and reasons derive from a source other than that table.
