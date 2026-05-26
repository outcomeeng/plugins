# ISSUES — sessions

## handing-off skill teaches the stale YAML handoff-input format

`spx session handoff` requires the JSON-prefix wire format: a single JSON object of caller fields (`priority`, `goal`, `next_step`, `specs`, `files`) followed by the body bytes verbatim. It rejects input that opens with the `---` YAML-frontmatter delimiter (`SessionLegacyFrontmatterInputError`).

The handing-off skill still teaches the old YAML-frontmatter input:

- `src/plugins/spec-tree/skills/handing-off/references/session-format.md` — the whole template opens with `---` frontmatter.
- `src/plugins/spec-tree/skills/handing-off/workflows/04-execute.md` — the Path C example pipes a `cat << 'EOF'` heredoc whose content opens with `---`.

An agent following the skill verbatim hits the rejection before adapting. Update both to the JSON-prefix contract (the CLI error documents it: `printf '%s\n' '{"priority":"high","goal":"...","next_step":"..."}' '# Body' | spx session handoff`). The body sections (`<metadata>`, `<nodes>`, `<skills>`, `<persisted>`, `<coordination>`, `<incorporated_sessions>`) are unchanged; only the frontmatter-delimiter input contract is wrong. Surfaced 2026-05-26 while running `/handoff`.
