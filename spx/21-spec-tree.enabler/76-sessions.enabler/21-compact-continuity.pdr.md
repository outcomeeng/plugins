# Post-Compact Continuity

The portion of compact summaries authored by spec-tree — appended to Claude Code's base summarization prompt via `compactPrompt` — records state in state-recording voice: past-tense factual records of what was true at compact time, with no imperative sections added by spec-tree. The SessionStart-on-compact hook re-emits foundation context on resume and is the durable correction for any residual imperatives in the base prompt's forced sections. The `compactPrompt` configuration and the SessionStart hook are the only writable surfaces that shape post-compact agent behavior; the base summarization prompt is read-only.

## Rationale

Three structural facts determine the design. The agent talks to itself: the compact summary is the agent writing for the agent who reads it next, so a state-recording contribution lets the resuming agent read context and decide, while an imperative contribution would compound the base prompt's residual force. Influence is bounded by the writable surfaces: any rule about post-compact behavior that does not flow from `compactPrompt` or the SessionStart hook has nowhere to land in the conversation and cannot be enforced. Re-anchoring is mechanical: foundation markers expire during compaction, and re-emitting them is a deterministic action the hook performs without consulting the agent. A queue-and-claim transfer ceremony adds ceremony without changing who does the work, because the same agent continues autonomously with no human present to authorize a transfer.

## Product properties

1. The portion of compact summaries authored by spec-tree records state in past-tense factual form — base-prompt-forced sections may carry residual imperatives, but spec-tree adds none.
2. Foundation context (`<SPEC_TREE_FOUNDATION>`, `<SPEC_TREE_CONTEXT>`) active before compaction is re-emitted by the SessionStart hook on resume.
3. Post-compact continuity proceeds without human direction — the agent reconstructs intent from the summary, the re-anchored context, and the user's next message, and the hook directive outweighs any residual imperatives in base-prompt-forced sections by being mechanical and specific.

## Verification

### Audit

- ALWAYS: the `compactPrompt` configuration appends sections conforming to the state schema (active node, pre-compact markers, modified files, open questions, last user request, in-flight observations) — base-prompt-forced sections are accepted as residual; the schema sections are spec-tree's contribution ([audit])
- ALWAYS: the SessionStart-on-compact hook re-emits foundation context — invocations of `/spec-tree:understanding` and `/spec-tree:contextualizing` on the recorded active node — when the persisted summary records that a foundation marker was active pre-compact ([audit])
- ALWAYS: the SessionStart-on-compact hook appends a `<COMPACT_RESUMED at="..."/>` marker after the re-anchoring directive — downstream skills detect the marker to recognize a post-compact resume ([audit])
- NEVER: the `compactPrompt` configuration adds imperative sections ("next step", "resume here", "now do X", "persistence proposal", "starting point") — those compound residual imperatives the marketplace cannot remove ([audit])
- NEVER: the `compactPrompt` configuration names specific skills the agent should invoke after resume — skill choice belongs to the SessionStart hook directive, not to summary text the agent reads as self-direction ([audit])
