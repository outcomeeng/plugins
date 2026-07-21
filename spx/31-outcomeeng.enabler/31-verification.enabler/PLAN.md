# Plan

Governing decision: `spx/31-outcomeeng.enabler/31-verification.enabler/15-generated-attribution.pdr.md`.

Pending implementation: `outcomeeng/validation/selected_gate.py` selects gate steps from hardcoded generated-path lists (`dist/claude/**`, `dist/codex/**`, instruction-block template paths) that duplicate relations 1 and 2 of `spx/local/generated-sources.toml`. Property 1 of the governing decision makes the committed declaration the single source of generated-path knowledge for verifiers and consumers, so the gate-step selector migrates to deriving those path patterns from the declaration. Deferred from the declaration changeset because the migration is an implementation change with its own test evidence in validation infrastructure, and the single-projection consumer is partially superseded by the pending `spx` verification scope projection (SPX queue follow-ups `2026-07-17_17-21-34` and `2026-07-21_05-08-28`); revisit the migration scope when that projection lands.

Assessed outside the rule's subject: `outcomeeng/catalog/plugin_catalog.py` reading `.claude-plugin/marketplace.json` and `outcomeeng_evals/ci_triggers.py` discovering `eval.toml` files are generators consuming their own declared inputs — generation itself, not a verifier or consumer deriving generated-source attribution — so they carry no migration obligation under the decision.
