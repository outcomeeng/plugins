# PLAN — Python test standards follow-ups

## Why

`docs/cross-language-test-standards-drift-audit.md` records one Python-specific follow-up: the Python test-writing path does not load the repo-local `spx/local/python-tests.md` overlay, while the TypeScript and Rust test-standard surfaces already teach their overlay paths.

The previous Python tests `PLAN.md` in this node covered boundary-validation wording that now exists in `python-test-standards`; this note replaces that resolved plan with the remaining overlay gap.

## Steps

1. Decide whether overlay loading belongs in `python-test-standards`, `test-python`, or both.
2. Add the Python test overlay read path so product-local rules in `spx/local/python-tests.md` can affect Python test-writing guidance.
3. Keep `audit-python-tests` overlay handling intact.
4. Gate with `just check-skills`, `just docs-check`, and `python:audit-python-tests`.

## Revisit condition

Pick this up after the `review-changes` vocabulary boundary is clarified, so later Python changes are reviewed with the corrected review vocabulary.
