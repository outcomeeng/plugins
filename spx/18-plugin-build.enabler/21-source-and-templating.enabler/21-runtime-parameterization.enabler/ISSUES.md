# Known issues — runtime parameterization

## FOLLOW-UP [consistency]: guard enforcement is develop-scoped while the marketplace still carries raw tokens

`RUNTIME_TOKEN_GUARDED_PLUGINS` is `frozenset({"develop"})` for the pilot, so the source-layer
guard fails the build only on raw runtime-divergent tokens under `src/plugins/develop/`. Authored
source in other plugins still carries raw `AskUserQuestion` (for example
`src/plugins/spec-tree/skills/merge/SKILL.md`,
`src/plugins/spec-tree/skills/standardizing-merging/SKILL.md`, and ~20 others) — those tokens
ship into `dist/codex/` untranslated until each plugin is converted to `tool(...)` tokens and
added to the guarded set.

The ADR NEVER assertion and the mechanism node's NEVER assertion are both scoped to "a guarded
plugin's authored `src/plugins/` content" so the declaration matches what the guard enforces
today. The marketplace-wide rollout — convert each remaining plugin's divergent tokens, then
extend `RUNTIME_TOKEN_GUARDED_PLUGINS` until it spans every plugin — is the Phase 2 work recorded
in this node's `PLAN.md`. This entry tracks the gap explicitly so the develop-scoped guard is a
recorded, intentional pilot boundary rather than an undocumented enforcement hole.

Resolution shape: per the PLAN.md Phase 2 rollout, convert each plugin's `AskUserQuestion` and
other registered runtime tokens to `tool(...)` tokens (or per-runtime conditionals), add the plugin
to `RUNTIME_TOKEN_GUARDED_PLUGINS`, and rebuild. When the guarded set spans the marketplace, the
"guarded plugin's" qualifier on the ADR and node assertions can widen back to all authored
`src/plugins/` content.
