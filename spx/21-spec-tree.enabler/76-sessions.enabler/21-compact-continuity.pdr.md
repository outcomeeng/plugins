# Post-Compact Continuity

The portion of compact summaries authored by spec-tree — appended to Claude Code's base summarization prompt via `compactPrompt` — records state in state-recording voice: past-tense factual records of what was true at compact time, with no imperative sections added by spec-tree. Compaction expires the agent's loaded spec-tree skills, so re-anchoring depends on recovering the active node. The PreCompact hook delegates that capture to the `spx` CLI (`spx compact store`), which reads the transcript — where the `<SPEC_TREE_FOUNDATION>` and `<SPEC_TREE_CONTEXT>` markers are recorded verbatim — and stashes the node under `.spx/sessions/{session_id}/`. The PostCompact hook re-anchors via `spx compact retrieve`: it prefixes a `<SPEC-TREE_RESUMED active-node="..."/>` marker and addresses the resuming agent as a competent engineer, stating that the loaded skills are gone and directing re-invocation of `/spec-tree:understanding` and `/spec-tree:contextualizing` on the captured node, supplied as the contextualizing argument. When the CLI returns no stash, the hook falls back to parsing the compact summary. The `compactPrompt` configuration, the hooks, and the `spx` CLI are the writable surfaces that shape post-compact agent behavior; the base summarization prompt is read-only.

## Rationale

Three structural facts determine the design. The agent talks to itself: the compact summary is the agent writing for the agent who reads it next, so a state-recording contribution lets the resuming agent read context and decide, while an imperative contribution would compound the base prompt's residual force. Re-anchoring is the agent's action, not the hook's: compaction expires the loaded skills, and only re-invoking them reloads the methodology foundation and the node context — the hook cannot reload a skill on the agent's behalf, so it instructs the agent to do it and names the active node so `/spec-tree:contextualizing` runs with the argument a bare invocation lacks. The carrier of that node is the transcript, not the summary: the markers are recorded verbatim in the transcript, so capturing the node there is deterministic, whereas the summary is written by a model and may omit it, reformat it, or be overridden by another PreCompact tool. The `spx` CLI owns that capture and storage because it resolves `.spx/` correctly across a single checkout and a bare-repository worktree pool and tests that resolution against a multi-worktree harness the hooks cannot; the hooks are thin — invoking the CLI and formatting the instruction — and fall back to the summary so re-anchoring degrades rather than fails when the CLI is unavailable.

## Product properties

1. The portion of compact summaries authored by spec-tree records state in past-tense factual form — base-prompt-forced sections may carry residual imperatives, but spec-tree adds none.
2. The PreCompact hook delegates capture of the active node to the `spx` CLI, which reads the transcript and stashes the node under `.spx/sessions/{session_id}/`, and no-ops when the CLI is unavailable.
3. The PostCompact hook re-anchors from `spx compact retrieve` — instructing the resuming agent that its loaded skills are gone and to re-invoke `/spec-tree:understanding` and `/spec-tree:contextualizing` on the captured node, supplied as the contextualizing argument — and parses the compact summary only as a fallback when the CLI returns no stash.
4. Post-compact continuity proceeds without human direction — the agent reloads the foundation and the node context by acting on the hook's instruction, reconstructs intent from the summary and the user's next message, and continues; the instruction names the skills and the node, so a capable agent acts on it.

## Verification

### Testing

- ALWAYS: the `compactPrompt` configuration appends sections conforming to the state schema (active node, pre-compact markers, modified files, open questions, last user request, in-flight observations) — base-prompt-forced sections are accepted as residual; the schema sections are spec-tree's contribution ([conformance])

### Audit

- ALWAYS: capture and storage of the active node are delegated to the `spx` CLI, which resolves `.spx/` and places the stash, and the hooks degrade silently when the CLI is unavailable ([audit])
- ALWAYS: when a foundation was active pre-compact, the PostCompact hook's output addresses the resuming agent in plain terms — that compaction removed its loaded skills and that it must re-invoke `/spec-tree:understanding` and `/spec-tree:contextualizing` on the captured node — rather than emitting a bare skill token a summary buries ([audit])
- ALWAYS: the re-anchoring names the captured node as the `/spec-tree:contextualizing` argument, and a post-compact `/spec-tree:contextualizing` directed without a node is a defect because it loads no context ([audit])
- NEVER: the hooks own `.spx/` mechanics or the stash location — the `spx` CLI is the single owner of `.spx/` resolution and stash placement, so the resume stash never diverges from the CLI's `.spx/` model ([audit])
- NEVER: the `compactPrompt` configuration adds imperative sections ("next step", "resume here", "now do X", "persistence proposal", "starting point") — those compound residual imperatives the marketplace cannot remove ([audit])
- NEVER: the `compactPrompt` configuration names specific skills the agent should invoke after resume — skill choice belongs to the PostCompact hook instruction, not to summary text the agent reads as self-direction ([audit])
