# Post-Compact Continuity

Post-compact continuity uses Claude Code's standard compact summary as the state record and the spec-tree `SessionStart` hook as the methodology-reload signal. When Claude reports `source=compact`, the hook tells the resuming agent that compaction reset the loaded foundation and requires `/understand` followed by `/contextualize` for every spec node still in scope. The project defines no `compactPrompt` override.

## Rationale

Claude Code already produces the compact summary that carries conversation state. A project-owned `compactPrompt` duplicates and constrains that summary, embeds runtime-specific wording, and grows stale as the runtime's base prompt evolves. The `SessionStart` payload provides a stable lifecycle signal instead: `source=compact` identifies the one start condition where the loaded methodology authority has expired, and the hook can direct the required reload without prescribing the resumed task.

## Product properties

1. Claude Code's standard compact summary remains the sole compact-summary prompt surface; the project defines no `compactPrompt` override.
2. A `SessionStart` event with `source=compact` identifies that the loaded spec-tree foundation and node contexts expired during compaction.
3. The post-compact hook directs methodology and node-context reload while leaving task reconstruction to the resuming agent and the standard summary.

## Verification

### Testing

- NEVER: `.claude/settings.json` defines a `compactPrompt` override ([conformance])

### Audit

- ALWAYS: the `SessionStart` hook reacts to `source=compact` by identifying the expired methodology authority and directing `/understand` followed by `/contextualize` for every spec node still in scope ([audit])
- ALWAYS: the post-compact hook leaves task reconstruction to the resuming agent and Claude Code's standard summary ([audit])
- NEVER: spec-tree replaces or augments Claude Code's compact-summary prompt through project configuration ([audit])
