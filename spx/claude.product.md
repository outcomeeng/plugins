# Claude Plugin Marketplace

## Why this product exists

The Claude Plugin Marketplace provides the Spec Tree methodology for Outcome Engineering, establishing human-written specifications as the authoritative source of truth for product development.

## Product hypothesis

WE BELIEVE THAT a plugin marketplace delivering Spec Tree methodology through skills for context loading, spec authoring, testing, and TDD implementation
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
- Testing and audit skills (testing, auditing-tests) as supersets of standalone methodology
- TDD flow orchestration (coding) with language-specific delegation
- Commit workflow (committing-changes) with Conventional Commits
- Language-specific plugins (Python, TypeScript) for architecture, testing, coding, review
- Session management (handoff, pickup) for conversation continuity
- Pre-commit validation infrastructure for plugin and skill quality

### What's excluded

| Excluded                | Rationale                                     |
| ----------------------- | --------------------------------------------- |
| Lock file tooling       | Planned but not yet designed                  |
| Cloud collaboration     | Individual developer tool, not team platform  |
| IDE-specific extensions | Claude Code is the interface, not IDE plugins |

## Product-level assertions

### Compliance

- ALWAYS: derive node status from test results, never from stored labels — status reflects reality
- ALWAYS: use atemporal voice in all specs — specs are permanent truth, not work items
- NEVER: store status in committed files — prevents drift from reality
