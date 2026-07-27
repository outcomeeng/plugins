# Outcome Engineering Plugin Marketplace

## Why this product exists

This product is a Claude Code and Codex plugin marketplace delivering the Spec Tree methodology — human-written specifications as the authoritative source of truth — together with the affordances that facilitate agent–user interaction while authoring, refactoring, and maintaining a product's spec tree: the SPX CLI and a local browser surface. It ships into every consumer team's own repository, in languages and domains unknown at design time; this repository is only the dogfood instance, the least important of those consumers.

## Consumers and jobs

| Consumer / persona      | Job to be done                                                                                                                 |
| ----------------------- | ------------------------------------------------------------------------------------------------------------------------------ |
| Product engineers       | Apply the Spec Tree methodology through their coding agent while preserving their repository's language and domain conventions |
| Plugin authors          | Create portable methodology, language, and craft plugins from one authored source                                              |
| Marketplace maintainers | Build, inspect, install, and publish agent-harness-native plugin artifacts from the shared marketplace                         |

## Surfaces

- Claude Code plugins — product engineers invoke skills and configured agents through Claude Code-native plugin artifacts.
- Codex plugins — product engineers invoke skills and configured agents through Codex-native plugin artifacts.
- SPX CLI — product engineers and automation inspect and operate on spec-tree structure and verification state.
- Local browser — product engineers inspect and restructure the SPX CLI's spec-tree projection interactively.

## Actors and sidedness

The marketplace serves plugin producers and plugin consumers.

- Plugin authors provide authored methodology, language, and craft behavior.
- Marketplace maintainers render and publish agent-harness-native plugin artifacts.
- Product engineers consume those artifacts inside their own repositories.

## Product hypothesis

WE BELIEVE THAT a plugin marketplace delivering Spec Tree methodology through Codex and Claude Code plugins for context loading, spec authoring, verification, and spec-driven implementation
WILL reduce implementation rework by enforcing complete context and evidence-driven flows before any code is written
CONTRIBUTING TO faster iteration cycles and higher confidence in AI-assisted development

### Evidence of success

| Metric                   | Current | Target | Measurement approach                              |
| ------------------------ | ------- | ------ | ------------------------------------------------- |
| Context loading coverage | 100%    | 100%   | All implementation skills enforce context loading |
| Spec-test coupling       | Partial | 100%   | Every assertion links to at least one test file   |
| Plugin adoption          | N/A     | 50+    | GitHub stars + marketplace installs               |

## Scope

### What's included

- Spec Tree methodology (`/understand`, `/contextualize`, `/author`, `/decompose`, `/refactor`, `/align`)
- Shared Claude Code and Codex plugin surfaces from the same source tree
- Verification and evidence skills (`/verify`, `/test`, `/audit-tests`) as supersets of standalone methodology
- TDD flow orchestration (`/apply`) with language-specific delegation
- Commit workflow (`/commit-changes`) with Conventional Commits
- Language-specific plugins (Python, TypeScript, Rust) for architecture, tests, code, and review
- Session management (handoff, pickup) for conversation continuity
- Pre-commit validation infrastructure for plugin and skill quality
- Persistent marketplace installation and isolated end-to-end install verification, governed by `spx/12-marketplace-state.adr.md`
- Interface surfaces (browser) that render the spec tree from the SPX CLI projection and support interactive review and restructuring

### What's excluded

| Excluded                | Rationale                                    |
| ----------------------- | -------------------------------------------- |
| Lock file tooling       | Outside plugin marketplace scope             |
| Cloud collaboration     | Individual developer tool, not team platform |
| IDE-specific extensions | Codex and Claude Code are runtime surfaces   |

## Product-level assertions

### Compliance

- ALWAYS: derive node status from test results, never from stored labels — status reflects reality
- ALWAYS: use atemporal voice in all specs — specs are permanent truth, not work items
- ALWAYS: state-changing operations against external systems (credential changes, workflow runs, repository writes) occur only with an explicit user instruction in the same turn — reading, status checks, and observability calls use non-mutating APIs
- ALWAYS: data values surfaced to the agent — identity (session id, host account, owner/repo, run id, commit SHA) and status/conclusion fields (workflow conclusion, run status, exit codes) — appear verbatim from their source — downstream skills index on the literal and users compare against the source
- NEVER: store status in committed files — prevents drift from reality
- NEVER: paraphrase or summarize agent-surfaced data values — identity or status/conclusion — paraphrase breaks downstream literal indexing and obscures user comparison against the source

## Open decisions

| Decision topic | Key question | Options | Triggers ADR/PDR? |
| -------------- | ------------ | ------- | ----------------- |
| None           | N/A          | N/A     | No                |
