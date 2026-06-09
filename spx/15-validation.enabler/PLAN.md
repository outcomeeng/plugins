# PLAN — reference-portability gate check

## Landed

`spx/15-validation.enabler/32-reference-portability.enabler` is **Passing**: spec +
`tests/test_reference_portability.compliance.l1.py` + implementation
`outcomeeng/validation/reference_portability.py`. Test-evidence and code audits APPROVED;
no node ADR (sibling-proportionate, mirrors `32-skill-injection-safety.enabler`). The node
is not in `spx/EXCLUDE` — its implementation exists, so its tests run in the gate.

The detector exposes `find_nonportable(text) -> list[(line, reference)]`, `scan_file`,
`scan_paths`, and a `main` CLI. A reference is non-portable when it is a numbered
`spx/\d…` node/decision or a `src/`/`dist/`/`outcomeeng/` repository segment (caught even
inside an absolute checkout path); a non-numbered `spx/…` (universal scaffolding), a
`spx/{…}` placeholder, and `${CLAUDE_SKILL_DIR}`/`${CLAUDE_PLUGIN_ROOT}` are portable.

## Follow-up — enforcement (NOT in the landing PR)

The detector is not yet wired into `just check`. Enforcing it needs a policy decision
first, then mechanical work:

1. **Decide the illustrative-example policy.** Measured 2026-06-09: 39 numbered refs across
   15 files in `src/plugins/**`. ~30 are teaching examples, and some are **pedagogically
   essential as concrete values** — the full-paths lesson in the `understanding` skill
   deliberately shows `spx/21-spec-tree.enabler/15-build.adr.md` to teach "use the full
   path." Blanket placeholder migration would gut those lessons. Options: tolerate refs
   inside fenced `` ```text `` example blocks, adopt an agreed illustrative namespace, or
   accept the loss. This is the blocker to enforcement, not the wiring.
2. **Migrate the genuine dangling refs** (those that are real references to this product's
   own tree, e.g. `spx/21-spec-tree.enabler/54-decomposing.enabler/decomposing.md`) to
   placeholder form or remove them.
3. **Wire the `Step`** into `outcomeeng/validation/_steps.py` (scanning `src/plugins/**`),
   and consider extending the `spx/15-validation.enabler/65-gate.enabler` compliance
   assertion to lock it. No CI change (existing `uv run python -m outcomeeng.validation`
   entrypoint runs every Step).
4. **Fix `AGENTS.md` line 80** — "The semgrep rule enforces this" is false; no semgrep step
   exists. This is the separate in-code-comment rule, related but distinct from this
   portability check.

## Not this work

References inside `outcomeeng/` (the non-shipped toolchain) — a separate matter, out of scope.
