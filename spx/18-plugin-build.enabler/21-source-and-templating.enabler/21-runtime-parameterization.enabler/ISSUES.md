# Known issues — runtime parameterization

## FOLLOW-UP [consistency]: the runtime-token lint ignore-list still names unconverted plugins

Enforcement that a raw runtime-divergent name never appears in authored source is the
runtime-token validation lint (`outcomeeng/validation/runtime_tokens.py`,
governed by `spx/15-validation.enabler/32-runtime-token.enabler/runtime-token.md`). The lint
is default-on across `src/plugins/`, exempting only the files named in its
`RUNTIME_TOKEN_IGNORE` set — the not-yet-converted files that still carry raw
`AskUserQuestion` and the like (the spec-tree skills and `work/sanitize-powerpoint`).

Those exempt files ship raw runtime names into `dist/codex/` untranslated until each is
converted to `tool(...)` tokens (or per-runtime conditionals) and removed from the ignore-list.
A newly added plugin is enforced by default — the ignore-list is the only exemption — so the
hole is bounded and explicitly tracked, not silent.

Resolution shape: convert each ignore-listed file's runtime-divergent names to `tool(...)`
tokens, drop its entry from `RUNTIME_TOKEN_IGNORE`, rebuild, and confirm the lint stays green.
When the ignore-list reaches empty, the marketplace is fully enforced and the set can be removed.
