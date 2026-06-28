# Frontmatter Validation Strategy

The set of valid SKILL.md frontmatter fields is the union of the fields enforced by a vendored copy of Anthropic's `quick_validate.py` (Apache 2.0), which defines the Agent Skills open-standard floor; marketplace portable capability fields shared by Claude Code and Codex, including `argument-hint`; and a hand-curated allowlist of Claude Code-only fields maintained in this marketplace. A skill is valid when the vendored validator accepts it, or when the only unexpected keys it reports are in the marketplace extension allowlists and all other standard-field format rules pass. A validation wrapper delegates open-standard field checking to the vendored validator, then consults the curated portable and Claude-only allowlists for any fields the vendored validator flagged; the vendored script and its license file are co-located under a vendor directory and are not modified in place.

## Rationale

A hardcoded field list drifts from reality the moment Anthropic tightens or extends the open standard. Scanning an opaque CLI binary for field patterns is unreliable; a public, versioned validator script is the correct contract. Using only the vendored script rejects `argument-hint`, which both emitted runtime targets preserve as a portable skill capability field, and rejects `disable-model-invocation`, `hooks`, and other fields Claude Code accepts and this marketplace uses. Vendoring the upstream validator plus small wrapper allowlists gives a single stable source of truth for the open standard with explicit, reviewable extensions for portable capability fields and Claude Code-only fields; updates arrive by re-pulling the upstream file, and the wrapper allowlists are audited whenever a new marketplace extension field appears.

## Verification

### Audit

- ALWAYS: delegate open-standard frontmatter validation to the vendored upstream validator — Anthropic's published script is the source of truth for the Agent Skills standard ([audit])
- ALWAYS: preserve the Apache 2.0 license file alongside the vendored script — attribution is a redistribution requirement ([audit])
- ALWAYS: maintain marketplace extension field allowlists in the wrapper, not in the vendored script, separating portable capability fields from Claude Code-only fields — separation keeps upstream syncs mechanical and prevents Codex-supported fields from being modeled as Claude-only ([audit])
- ALWAYS: accept the vendored validator as a callable parameter — enables Level 1 testing of allowlist filtering without invoking the vendored script ([audit])
- NEVER: modify the vendored script in place — upstream edits make future syncs ambiguous and break the attribution chain ([audit])
- NEVER: scan the Claude Code CLI binary for frontmatter field patterns — the binary is an opaque, unstable artifact and the vendored script is the correct contract ([audit])
- NEVER: hardcode the Agent Skills standard field list in marketplace source — the vendored script already enforces it and any duplicate will drift ([audit])
- NEVER: use `unittest.mock.patch` for the vendored validator — use dependency injection instead ([audit])
