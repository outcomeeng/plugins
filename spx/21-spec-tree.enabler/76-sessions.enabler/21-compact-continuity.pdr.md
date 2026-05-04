# Post-Compact Continuity

## Purpose

Governs post-compact continuity — how a Claude Code agent resumes its own work after context compression. Establishes the voice in which spec-tree records state for the agent to read on resume, identifies the writable surfaces through which post-compact agent behavior can be shaped, and acknowledges the bounded portion of those surfaces that the marketplace actually controls.

## Context

**Business impact:** Post-compact continuity is autonomous and unattended. After context compression, the agent resumes work without a human present to direct it. The agent's only sources of orientation are the compact summary it wrote for itself before compaction and the SessionStart hook output injected into the new session. Whatever those two documents say is what the agent enacts on resume. No human is available to correct a misdirected resume in real time, and no second agent claims the work — the original agent simply continues, with whatever orientation its own past writing has provided.

**Technical constraints:** The compact summary is authored by the same agent whose attention it competes for on resume. The summary appears in the conversation alongside the SessionStart hook output, in the agent's own register, and at significant length. The hook output appears inside `<system-reminder>` blocks. Foundation markers (`<SPEC_TREE_FOUNDATION>`, `<SPEC_TREE_CONTEXT>`) do not survive compaction and need re-emission on resume.

The writable surfaces for post-compact behavior are the `compactPrompt` configuration in `settings.json` (extends Claude Code's base summarization prompt) and the SessionStart-on-compact hook script (governs what is injected when the new session starts). Claude Code's base summarization prompt is read-only from the marketplace's position and forces sections that include imperative framing — sections 7 (Pending Tasks), 8 (Current Work), and 9 (Optional Next Step) of the base prompt's nine-section structure. `compactPrompt` extends the base prompt but cannot remove or rewrite its forced sections. Constraints stated outside `compactPrompt` and the hook script have nowhere to land in the conversation and remain unenforceable on resume.

## Decision

The portion of compact summaries authored by spec-tree (via `compactPrompt` extensions appended to the base prompt) is written in state-recording voice — past-tense factual records of what was true at compact time, with no imperative sections added by spec-tree. Sections forced by Claude Code's base summarization prompt may contain residual imperatives that `compactPrompt` cannot remove; the SessionStart-on-compact hook directive — fully under marketplace control — is the durable correction mechanism, deliberately constructed to be more specific and mechanical than the base prompt's softer "optional" framing. The `compactPrompt` configuration and the SessionStart hook script are the only writable surfaces shaping post-compact agent behavior; the base summarization prompt is read-only, and constraints outside these surfaces are unenforceable on resume.

A queue-and-claim transfer ceremony is inadequate for this concern. The same agent continues autonomously after compaction with no human present to authorize a transfer, and persistence happens through the agent's own state record because no other party is available to direct it. Transfer semantics overlaid on this scenario add ceremony without changing who is doing the work.

## Rationale

Three structural facts determine the design:

- **The agent talks to itself.** The compact summary is the agent writing for the agent who will read it next. If spec-tree's contribution to the summary records state, the agent on resume reads context and decides what to do. If spec-tree's contribution records imperatives, the agent on resume enacts them. The base prompt's residual imperatives in sections 7–9 are softer ("optional next step", "pending tasks") than what spec-tree could add ("must invoke X first") — keeping the spec-tree contribution state-only avoids compounding the base prompt's residual force.

- **Influence is bounded by the writable surfaces.** The `compactPrompt` extension determines what spec-tree adds to the summary. The SessionStart hook determines what additional context is injected. The base prompt's content is not writable. Any rule about post-compact behavior that does not flow from `compactPrompt` or the SessionStart hook has nowhere to land in the conversation and cannot be enforced.

- **Re-anchoring is mechanical.** Foundation markers expire during compaction. Re-emitting them is a deterministic action, not an agent judgment. The hook performs this without consulting the agent because no decision is involved: any marker recorded as active pre-compact gets re-emitted on resume. The hook's directive is mechanical and specific; the base prompt's residual imperatives are softer ("optional"); the hook outweighs the base by being clearer.

## Trade-offs accepted

| Trade-off                                                                                  | Mitigation / reasoning                                                                                                                                                                                                                                                                                                 |
| ------------------------------------------------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Compact summary cannot record an explicit "next step" via spec-tree's `compactPrompt`      | Past-tense factual records ("was drafting test X based on assertion N") preserve the cognitive thread; the user's next message and the re-anchored context drive action                                                                                                                                                |
| Hook re-anchoring runs even on resume turns that don't need spec-tree                      | Re-anchoring is deterministic and inexpensive (two skill invocations); conditional logic adds complexity and risks false negatives that leave the agent miscontexted                                                                                                                                                   |
| Constraints outside `compactPrompt` and the hook are unenforceable on resume               | Honest acknowledgment of where influence ends; alternative framings create false confidence in rules the runtime cannot enforce                                                                                                                                                                                        |
| `compactPrompt` is a partial writable surface — the base summarization prompt is read-only | The base prompt forces sections (Pending Tasks, Current Work, Optional Next Step) that may contain residual imperatives that `compactPrompt` cannot remove. The SessionStart-on-compact hook directive — fully under marketplace control — outweighs the base prompt's softer framing by being mechanical and specific |

## Product invariants

- The portion of compact summaries authored by spec-tree (via `compactPrompt`) records state in past-tense factual form — base-prompt-forced sections may contain residual imperatives, but spec-tree adds none.
- Foundation context (`<SPEC_TREE_FOUNDATION>`, `<SPEC_TREE_CONTEXT>`) that was active before compaction is re-emitted by the SessionStart hook on resume.
- Post-compact continuity proceeds without human direction — the agent reconstructs intent from the summary, the re-anchored context, and the user's next message; the SessionStart hook directive outweighs any residual imperatives in base-prompt-forced sections by being mechanical and specific.

## Compliance

### Recognized by

The `compactPrompt` configuration in `settings.json` extends Claude Code's base summarization prompt with sections containing only the state schema (active node, pre-compact markers, modified files, open questions, last user request, in-flight observations) and no imperative framing added by spec-tree. The SessionStart-on-compact hook reads the persisted summary, injects it as context, emits a directive that invokes `/spec-tree:understanding` (when the foundation marker was active pre-compact) and `/spec-tree:contextualizing` on the recorded active node, and appends a `<COMPACT_RESUMED at="..."/>` marker. Compact summaries persisted to `.spx/sessions/tmp/compact-<session_id>.md` contain the base prompt's nine sections followed by spec-tree's appended state-only sections.

### MUST

- The `compactPrompt` configuration appends sections to the base summarization prompt that conform to the state schema (active node, pre-compact markers, modified files, open questions, last user request, in-flight observations) — base-prompt-forced sections are accepted as residual; the schema sections are what spec-tree contributes to the summary ([review])
- The SessionStart-on-compact hook re-emits foundation context — invocations of `/spec-tree:understanding` and `/spec-tree:contextualizing` on the recorded active node — when the persisted summary records that a foundation marker was active pre-compact ([review])
- The SessionStart-on-compact hook appends a `<COMPACT_RESUMED at="..."/>` marker after the re-anchoring directive — downstream skills detect the marker to recognize a post-compact resume ([review])

### NEVER

- The `compactPrompt` configuration adds imperative sections — "next step", "resume here", "now do X", "persistence proposal", "starting point" — those compound residual imperatives in base-prompt-forced sections that the marketplace cannot remove ([review])
- The `compactPrompt` configuration names specific skills the agent should invoke after resume — skill choice belongs to the SessionStart hook directive, not to summary text the agent will read as self-direction ([review])
