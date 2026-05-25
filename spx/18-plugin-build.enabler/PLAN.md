# Plan

Current implementation pass for the 18-plugin-build subtree.

## Implemented Shape

- Authored plugin content lives under `src/plugins/`.
- `outcomeeng.distribution.build` renders committed runtime trees under `dist/claude/` and `dist/codex/`.
- Marketplace catalogs point at the generated `dist/` plugin roots.
- Claude agent Markdown renders into Codex custom-agent TOML through `outcomeeng.distribution.agents`.
- `just sync-marketplace` installs generated Codex agents after Codex cache preservation and before install validation.

## Remaining Acceptance Steps

1. Regenerate runtime/catalog output and verify `dist/` is fresh.
2. Run markdown/spec status validation, then the full local check.
3. Run `just sync-marketplace <previous-main-ref>` and confirm generated TOML agents exist under `~/.codex/agents`.
