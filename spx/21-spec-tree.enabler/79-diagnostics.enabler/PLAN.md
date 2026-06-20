# PLAN: Build the `diagnose` environment-doctor skill

This node governs the `diagnose` skill — a portable environment doctor for any spec-tree / spx environment. The spec declares the first slice; this note tracks the remaining authoring work and the deferred checks. Coordination only; the spec and its `[eval]`/`[audit]` evidence are the truth.

## Resolved decisions

- **Architecture — thin skill over existing `spx`/harness surfaces.** The skill orchestrates existing commands (`spx worktree status`, harness env vars, and later `spx session list` / marketplace listing) and classifies their output in its body. It ships in this repository now. Per `spx/12-shipped-scripting.adr.md`, a check that outgrows light orchestration extracts into the `spx` CLI then — not preemptively. No new `spx doctor` CLI subcommand in this slice.
- **First slice — seed + `spx` reachability/version.** The `SessionStart`-hook session-environment check (working / identity-only / silent no-op) plus the `spx`-on-PATH check that reports the installed version verbatim. Heavier checks, including version-floor compliance, are deferred (below).

## Status

- **Shipped:** the `diagnose` skill with five checks — session-environment and spx-reachability (spec-tree 0.61.0), worktree-pool (0.61.2), session-store (0.61.3), and marketplace-install (this slice) — the spec node, README/template/catalog registration, and the version bumps. Each check carries a `[eval]` suite under `evals/` (test-evidence-auditor APPROVED); the node is out of `spx/EXCLUDE`. spec-auditor and skill-auditor pass on every slice.
- **Remaining:** the graded eval run (see `ISSUES.md` — needs CI auth or local `ANTHROPIC_API_KEY`; not gated by `just check`); the `[audit]` assertions are agentic and verified at audit time; the deferred checks below.

The session-environment check reuses the env-var + `spx worktree status` round-trip proven by `spx/21-spec-tree.enabler/13-agent-environment.enabler`.

## Deferred checks (follow-up slices)

Each grows the report by extension; the heavier ones are candidates `spx/12-shipped-scripting.adr.md` would push into the `spx` CLI once they prove themselves.

- **spx version-floor compliance** — judge the reported `spx` version against a required minimum. Needs a minimum-version declaration the installed plugin tree exposes (no such declaration ships today); the spx-reachability check reports the version verbatim rather than judging it against a floor. Deciding the declaration mechanism (e.g. a `minimumSpxVersion` manifest field and how the floor value is sourced) is a prerequisite and may warrant its own decision record.
