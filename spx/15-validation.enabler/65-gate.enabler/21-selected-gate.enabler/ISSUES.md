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
