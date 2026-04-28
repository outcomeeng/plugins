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

- Spec Tree methodology (understanding, contextualizing, authoring, decomposing, refactoring, aligning)
- Shared Claude Code and Codex plugin surfaces from the same source tree
- Testing and audit skills (testing, auditing-tests) as supersets of standalone methodology
- TDD flow orchestration (coding) with language-specific delegation
- Commit workflow (committing-changes) with Conventional Commits
- Language-specific plugins (Python, TypeScript) for architecture, testing, coding, review
- Session management (handoff, pickup) for conversation continuity
- Pre-commit validation infrastructure for plugin and skill quality
- Local plugin installation and update support for developer machines

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
- NEVER: store status in committed files — prevents drift from reality

## Open decisions

| Decision topic | Key question | Options | Triggers ADR/PDR? |
| -------------- | ------------ | ------- | ----------------- |
| None           | N/A          | N/A     | No                |
