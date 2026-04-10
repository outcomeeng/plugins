# Frontmatter Validation Strategy

## Purpose

This decision governs how SKILL.md frontmatter fields are validated. Consistent validation prevents drift between what skill authors commit and what the Claude Code CLI accepts.

## Context

**Business impact:** Skill authors whose frontmatter is rejected by Claude Code but passes local validation lose trust in the validation pipeline. Authors whose frontmatter is accepted by Claude Code but rejected locally are blocked from committing valid work. Both failure modes stem from drift between local validation and the authoritative field set.

**Technical constraints:** Anthropic publishes `quick_validate.py` in the `anthropics/skills` repository under Apache 2.0. That script is the source-of-truth validator for the Agent Skills open standard — it enforces the closed set of six standard fields (`name`, `description`, `license`, `allowed-tools`, `metadata`, `compatibility`) plus format rules for `name` (kebab-case, ≤64 chars), `description` (≤1024 chars, no angle brackets), and `compatibility` (≤500 chars). Claude Code accepts additional implementation-specific fields (`disable-model-invocation`, `argument-hint`, `hooks`, `model`, `when-to-use`, others) that the open standard script does not recognize. The marketplace already depends on Python as its validation runtime.

## Decision

The set of valid SKILL.md frontmatter fields is the union of:

1. The fields enforced by a vendored copy of Anthropic's `quick_validate.py` (Apache 2.0), which defines the Agent Skills open standard floor.
2. A hand-curated allowlist of Claude Code-specific fields maintained in this marketplace.

A skill is valid when either the vendored validator accepts it, or the only unexpected keys it reports are in the Claude Code allowlist and all other standard-field format rules pass.

## Rationale

Three alternatives fail:

- **Hardcoded field list** — drifts from reality the moment Anthropic tightens or extends the open standard. Requires a maintenance step that is always late.
- **Binary string scanning** — scanning an opaque CLI binary for field patterns is unreliable; a public, versioned validator script is the correct contract.
- **Only the vendored script** — rejects `disable-model-invocation`, `argument-hint`, `hooks`, and other fields that Claude Code accepts and this marketplace actively uses.

Vendoring the upstream validator plus a small allowlist gives the marketplace a single stable source of truth for the open standard (Anthropic's own script) with an explicit, reviewable extension for Claude Code-specific fields. The vendored script is a small, self-contained Python module with minimal dependencies. Updates arrive by re-pulling the upstream file; the allowlist lives next to the wrapper and is audited whenever a new Claude Code field appears in the marketplace's own skills.

## Trade-offs accepted

| Trade-off                                                               | Mitigation / reasoning                                                                                    |
| ----------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------- |
| Claude Code allowlist requires manual updates as the CLI evolves        | The allowlist is small (single-digit entries), visible in code review, and catches regressions in CI      |
| Vendored script must be resynced when Anthropic updates it              | The upstream file is stable and rarely changes; a periodic manual sync is lower cost than binary scanning |
| Format rules (name length, description length) are enforced universally | The open standard's rules are Anthropic's ceiling for portability — enforcing them locally is desirable   |

## Compliance

### Recognized by

A validation wrapper delegates open-standard field checking to a vendored upstream validator, then consults a curated Claude Code field allowlist for any fields the upstream validator flagged as unexpected. The vendored script and its license file are co-located under a vendor directory and are not modified in place.

### MUST

- Delegate open-standard frontmatter validation to the vendored upstream validator — Anthropic's published script is the source of truth for the Agent Skills standard ([review])
- Preserve the Apache 2.0 license file alongside the vendored script — attribution is a redistribution requirement ([review])
- Maintain the Claude Code-specific field allowlist in the wrapper, not in the vendored script — separation keeps upstream syncs mechanical ([review])
- Accept the vendored validator as a callable parameter — enables Level 1 testing of allowlist filtering without invoking the vendored script ([review])

### NEVER

- Modify the vendored script in place — upstream edits make future syncs ambiguous and break the attribution chain ([review])
- Scan the Claude Code CLI binary for frontmatter field patterns — the binary is an opaque, unstable artifact and the vendored script is the correct contract ([review])
- Hardcode the Agent Skills standard field list in marketplace source — the vendored script already enforces it and any duplicate will drift ([review])
- Use `unittest.mock.patch` for the vendored validator — use dependency injection instead ([review])
