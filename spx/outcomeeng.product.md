# Outcome Engineering Plugin Marketplace

## Why this product exists

The Outcome Engineering Plugin Marketplace provides Spec Tree methodology for Codex and Claude Code, establishing human-written specifications as the authoritative source of truth for product development.

## Product hypothesis

WE BELIEVE THAT a plugin marketplace delivering Spec Tree methodology through Codex and Claude Code plugins for context loading, spec authoring, testing, and TDD implementation
WILL reduce implementation rework by enforcing complete context and test-driven flows before any code is written
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
- Testing and audit skills (`/test`, `/audit-tests`) as supersets of standalone methodology
- TDD flow orchestration (`/apply`) with language-specific delegation
- Commit workflow (`/commit-changes`) with Conventional Commits
- Language-specific plugins (Python, TypeScript, Rust) for architecture, tests, code, and review
- Session management (handoff, pickup) for conversation continuity
- Pre-commit validation infrastructure for plugin and skill quality
- Local plugin installation and update support for developer machines
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
