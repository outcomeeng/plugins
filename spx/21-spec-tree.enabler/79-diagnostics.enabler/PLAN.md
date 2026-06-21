# PLAN: Build the `diagnose` environment-doctor skill

This node governs the `diagnose` skill — a portable environment doctor for any spec-tree / spx environment. The spec declares the first slice; this note tracks the remaining authoring work and the deferred checks. Coordination only; the spec and its `[eval]`/`[audit]` evidence are the truth.

## Resolved decisions

- **Architecture — thin skill over existing `spx`/harness surfaces.** The skill orchestrates existing commands (`spx worktree status`, harness env vars, and later `spx session list` / marketplace listing) and classifies their output in its body. It ships in this repository now. Per `spx/12-shipped-scripting.adr.md`, a check that outgrows light orchestration extracts into the `spx` CLI then — not preemptively. No new `spx doctor` CLI subcommand in this slice.
- **First slice — seed + `spx` reachability/version.** The `SessionStart`-hook session-environment check (working / identity-only / silent no-op) plus the `spx`-on-PATH check that reports the installed version verbatim. Heavier checks were deferred to follow-up slices.
- **Version-floor source and shape.** `spx/21-spec-tree.enabler/79-diagnostics.enabler/15-version-floor.adr.md` governs: the floor is `REQUIRED_SPX_VERSION` (the product's single source-of-truth spx-version floor) rendered into the shipped skill by the build's template pass (the `{{! spx_floor !}}` token); the floor verdict folds into `spx-reachability` as a below-floor degraded verdict rather than a separate check.

## Status

- **Shipped:** the `diagnose` skill with five checks — session-environment, spx-reachability (now judging the installed `spx` version against the build-rendered floor per `15-version-floor.adr.md`), worktree-pool, session-store, and marketplace-install — the spec node, the `15-version-floor.adr.md` decision, the build-render of `REQUIRED_SPX_VERSION`, README/template/catalog registration, and the version bumps. Each behavior check carries an `[eval]` suite under `evals/`, and the floor render carries a `[test]` conformance suite (`tests/test_version_floor.conformance.l1.py`); the node is out of `spx/EXCLUDE`. spec-auditor and skill-auditor pass on every slice.
- **Remaining:** the graded eval run (see `ISSUES.md` — needs CI auth or local `ANTHROPIC_API_KEY`; not gated by `just check`); the `[audit]` assertions are agentic and verified at audit time.

The session-environment check reuses the env-var + `spx worktree status` round-trip proven by `spx/21-spec-tree.enabler/13-agent-environment.enabler`.

## Deferred checks (follow-up slices)

None — the planned checks ship. A future surface grows the report by extension per the node's `<extending>` model; a check that outgrows light orchestration extracts into the `spx` CLI per `spx/12-shipped-scripting.adr.md`.
