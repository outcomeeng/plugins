# Post-Compact Continuity

The portion of compact summaries authored by spec-tree records state in state-recording voice: factual records of the session state, with no imperative sections added by spec-tree. The resuming agent reads the state-schema sections, reconstructs context, and resumes from those facts. Spec-tree's post-compact continuity contribution is summary state for reader-led resumption.

## Rationale

The compact summary is the agent writing for the agent who reads it next, so a state-recording contribution lets the resuming agent read context and decide. The schema sections (active node, pre-compact markers, modified files, open questions, last user request, in-flight observations) give that reader the facts to re-derive intent and reload the methodology foundation and node context itself.

## Product properties

1. The portion of compact summaries authored by spec-tree records state in past-tense factual form and adds no imperatives.
2. The state-schema sections give the resuming agent the facts to re-derive intent and reload context without directing a fixed resumption path.
3. Post-compact continuity proceeds without human direction — the resuming agent reads the summary, reconstructs intent from it and the user's next message, and continues.

## Verification

### Audit

- ALWAYS: the post-compact summary includes sections conforming to the state schema (active node, pre-compact markers, modified files, open questions, last user request, in-flight observations) ([audit])
- ALWAYS: spec-tree's post-compact continuity contribution is the compact summary state the resuming agent reads and interprets ([audit])
- NEVER: spec-tree's compact-summary contribution adds imperative sections ("next step", "resume here", "now do X", "persistence proposal", "starting point") ([audit])
- NEVER: spec-tree's compact-summary contribution names specific skills the agent should invoke after resume — skill choice is the resuming agent's, not summary text it reads as self-direction ([audit])
