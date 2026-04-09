# Spec Coverage Scope

## Purpose

This decision governs which plugins receive full spec-tree coverage (specs + automated tests) versus lightweight coverage (enabler with review-only compliance assertions). It prevents over-speccing pure-prompt plugins while ensuring implementation-heavy plugins have genuine test evidence.

## Context

**Business impact:** The marketplace spans two categories of plugins: plugins with Python/TypeScript implementation code and plugins that are pure skill definitions (markdown prompts). Requiring full spec+test coverage for prompt-only plugins produces specs whose assertions can only be verified by `[review]` — adding tree structure without adding verifiable evidence.

**Technical constraints:** Pure-skill plugins contain no executable code. Their quality is governed by auditing skills (`/auditing-skills`, `/auditing-commands`), not by automated tests. Implementation plugins contain Python scripts, test harnesses, or complex workflows with testable behavior.

## Decision

All plugins get at least one enabler node in the spec tree. Plugins with implementation code get full spec+test coverage. Plugins that are pure skill definitions get enabler nodes with `[review]` compliance assertions only.

## Rationale

The spec tree's value derives from the truth hierarchy: specs declare, tests verify, code complies. For pure-skill plugins, the "code" layer is markdown — there is no executable to test. Forcing automated tests produces one of two bad outcomes: tautological tests that parse markdown structure (testing formatting, not behavior) or tests that invoke Claude and assert on LLM output (non-deterministic, unfalsifiable).

Review-based compliance assertions acknowledge that skill quality is a human judgment: "does this skill produce good results?" is answered by `/auditing-skills`, not by pytest.

The alternative — excluding pure-skill plugins from the tree entirely — was rejected because enabler nodes still provide value: they document what the plugin provides, establish dependency relationships, and create a place to hang compliance rules that auditing skills enforce.

Legacy plugins (`specs`, `spx-legacy`) are excluded from the tree entirely. They have no testable behavior that the spec tree would govern.

## Trade-offs accepted

| Trade-off                                                                         | Mitigation / reasoning                                                                 |
| --------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------- |
| Pure-skill plugins lack automated test evidence                                   | Auditing skills provide structured review; skill quality is inherently a judgment call |
| Legacy plugins have no spec tree representation                                   | No testable behavior exists; spec nodes would have only vacuous assertions             |
| Adding implementation code to a pure-skill plugin requires upgrading its coverage | This is the intended forcing function — new code brings new evidence requirements      |

## Compliance

### Recognized by

Implementation plugins have enabler nodes with child outcomes containing `[test]` assertions. Pure-skill plugins have enabler nodes with only `[review]` compliance assertions and no child outcome nodes.

### MUST

- Create at least one enabler node for every non-legacy plugin — the tree is the complete product map ([review])
- Use `[test]` evidence for assertions about executable code — review is not a substitute for automated verification ([review])
- Use `[review]` evidence for assertions about skill/prompt quality — automated tests cannot verify prompt effectiveness ([review])

### NEVER

- Create automated tests for pure-skill plugins that test markdown structure — this produces tautological evidence ([review])
- Create spec nodes for legacy plugins (`specs`, `spx-legacy`) — no testable behavior exists ([review])
