# Post-Compact Continuity

The portion of compact summaries authored by spec-tree — appended to Claude Code's base summarization prompt via the `compactPrompt` configuration in `.claude/settings.json` — records state in state-recording voice: past-tense factual records of what was true at compact time, with no imperative sections added by spec-tree. Compaction expires the agent's loaded spec-tree skills, so the resuming agent reads the state-schema sections, reconstructs context, and decides what to reload. The `compactPrompt` configuration is the only surface spec-tree shapes for post-compact behavior; the base summarization prompt is read-only, and no runtime hook participates in compaction.

## Rationale

The compact summary is the agent writing for the agent who reads it next, so a state-recording contribution lets the resuming agent read context and decide, while an imperative contribution would compound the base prompt's residual force. The schema sections (active node, pre-compact markers, modified files, open questions, last user request, in-flight observations) give that reader the facts to re-derive intent and reload the methodology foundation and node context itself. Spec-tree adds no compaction hook: a runtime hook cannot reload a skill on the agent's behalf, and any `.spx/` work belongs in the `spx` CLI invoked by a skill, not in a hook, per `spx/21-spec-tree.enabler/15-hook-state-delegation.adr.md`.

## Product properties

1. The portion of compact summaries authored by spec-tree records state in past-tense factual form — base-prompt-forced sections may carry residual imperatives, but spec-tree adds none.
2. The state-schema sections give the resuming agent the facts to re-derive intent and reload context, without a hook directing it.
3. Post-compact continuity proceeds without human direction — the resuming agent reads the summary, reconstructs intent from it and the user's next message, and continues.

## Verification

### Testing

- ALWAYS: the `compactPrompt` configuration appends sections conforming to the state schema (active node, pre-compact markers, modified files, open questions, last user request, in-flight observations) — base-prompt-forced sections are accepted as residual; the schema sections are spec-tree's contribution ([conformance])

### Audit

- ALWAYS: spec-tree's only post-compact surface is the `compactPrompt` summary text; no runtime hook participates in compaction, per `spx/21-spec-tree.enabler/15-hook-state-delegation.adr.md` ([audit])
- NEVER: the `compactPrompt` configuration adds imperative sections ("next step", "resume here", "now do X", "persistence proposal", "starting point") — those compound residual imperatives the marketplace cannot remove ([audit])
- NEVER: the `compactPrompt` configuration names specific skills the agent should invoke after resume — skill choice is the resuming agent's, not summary text it reads as self-direction ([audit])
