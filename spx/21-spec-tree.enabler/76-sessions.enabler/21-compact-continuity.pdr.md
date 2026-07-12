# Post-Compact Continuity

Post-compact continuity uses Claude Code's standard compact summary as the state record and the managed root instruction block as the methodology-reload signal. The root instruction block requires `/understand` followed by `/contextualize` for every spec node still in scope after compaction. The project defines no `compactPrompt` override, and the `SessionStart` hook remains limited to delegated session-environment and worktree-occupancy behavior.

## Rationale

Claude Code produces the compact summary that carries conversation state. A project-owned `compactPrompt` duplicates and constrains that summary, embeds runtime-specific wording, and grows stale as the runtime's base prompt evolves. The managed root instruction block survives as the product's routing authority and directs the required methodology reload without replacing the runtime's task summary or expanding the session hook beyond its delegated environment responsibilities.

## Product properties

1. Claude Code's standard compact summary is the sole compact-summary prompt surface; the project defines no `compactPrompt` override.
2. The managed root instruction block directs `/understand` followed by `/contextualize` for every spec node still in scope before post-compaction spec-tree work.
3. The `SessionStart` hook delegates session-environment and worktree-occupancy behavior to `spx hook run session-start` and carries no compact-summary or methodology-reload behavior.

## Verification

### Audit

- ALWAYS: the managed root instruction block directs `/understand` followed by `/contextualize` for every spec node still in scope after compaction, while task reconstruction remains with the resuming agent and Claude Code's standard summary ([audit])
- NEVER: the `SessionStart` hook carries compact-summary or methodology-reload behavior — it remains the delegated session-environment and worktree-occupancy hook defined by `spx/21-spec-tree.enabler/15-hook-state-delegation.adr.md` ([audit])
- NEVER: `.claude/settings.json` defines a `compactPrompt` override ([audit])
- NEVER: spec-tree replaces or augments Claude Code's compact-summary prompt through project configuration ([audit])
