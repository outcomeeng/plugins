# Issue

PROVIDES the `/issue` skill — capturing an agent's observation about a spec-tree component and filing or reusing one minimal follow-up in the owning repository's active session queue, including when that repository is the invoking repository
SO THAT an agent working in a consumer, dependency, or product repository
CAN record a needed follow-up where that repository's own agents pick it up, without editing installed source directly or running the current work through the full closure workflow

## Assertions

### Mappings

- Marketplace registration JSON maps to either the target dependency checkout path or a non-zero diagnostic when the named local marketplace cannot be resolved ([test](tests/test_resolve_marketplace.mapping.l1.py))

### Compliance

- ALWAYS: `/issue` files the follow-up into the target repository's session queue through `spx session handoff`; for a different repository it targets that dependency checkout, and for the invoking repository it uses a queue-safe checkout without switching, detaching, committing, handing off, or otherwise disturbing the active worktree ([audit])
- ALWAYS: `/issue` resolves the target from the dependency the observation concerns — the marketplace Directory source for the spec-tree plugin, the `spx` CLI checkout for the `spx` dependency — and passes that checkout directory to `spx -C <target-dir> session handoff`, never a single hard-coded target ([audit])
- ALWAYS: `/issue` recognizes a target as the invoking repository when their absolute git common directories or normalized origin identities match; a linked worktree in the same pool and a separate clone of the same origin enter the same-repository path rather than stopping as an invalid dependency target ([audit])
- ALWAYS: before a same-repository write, `/issue` searches both `todo` and `doing` sessions for a dependency-followup body describing the same observation and affected surfaces; it reuses one matching active session and writes nothing, or creates exactly one follow-up when no match exists, never creating a duplicate because wording or title differs ([audit])
- ALWAYS: `/issue` obtains operator confirmation before its first mutating command against a different repository when the invocation arguments did not name that checkout path directly, presenting the absolute target root, that repository's normalized origin identity, the resolved git ref, and the follow-up's goal, and stopping on anything but explicit approval with both repositories unchanged; the explicit `/issue` invocation itself authorizes one deduplicated write to the invoking repository's own queue ([audit])
- NEVER: `/issue` treats resolving a different repository as authorization to write to it — a different target reached through marketplace resolution or the invoking repository's configuration is confirmed however reliably it resolved ([audit])
- ALWAYS: `/issue` captures only the invoking agent's observation, uncertainty, verified facts, affected paths, and next-workflow context, and shapes them into the handoff body ([audit])
- ALWAYS: `/issue` uses a dependency-followup body whose required sections are observation, uncertainty, checked facts, affected paths, and next-workflow context; it does not use `/handoff`'s node-oriented session body because the invoking agent assigns none of the dependency's internal taxonomy ([audit])
- ALWAYS: `/issue` supplies an output-shaped `goal` and an imperative `next_step` in the handoff header so the target repository's `spx session list` and `spx session todo` surface what the follow-up produces and the first action that resumes it ([audit])
- ALWAYS: `/issue` resolves the invoking runtime identity before filing and verifies that the stored handoff carries the same non-empty `agent_session_id` and a non-empty `created_at` ([audit])
- NEVER: `/issue` records the target dependency's internal taxonomy — a node address, a decision index, an assertion type, or any classification the dependency's own agents assign — the invoking agent supplies observations, not the dependency's spec-tree structure ([audit])
- NEVER: `/issue` edits, commits to, or pushes the target dependency repository's tracked source — its only effect on the target is the handoff session document `spx -C <target-dir> session handoff` writes into that repository's session queue ([audit])
- NEVER: `/issue` alters the invoking repository's tracked git state or current branch, or archives, releases, deletes, replaces, or otherwise changes an existing active session; a same-repository filing adds at most one minimal `todo` follow-up and preserves every unrelated queue entry ([audit])
