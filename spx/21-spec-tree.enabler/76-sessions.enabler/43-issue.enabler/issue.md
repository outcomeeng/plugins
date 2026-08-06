# Issue

PROVIDES the `/issue` skill — capturing an agent's observation about a spec-tree dependency and filing it as a handoff session in that dependency repository's own session queue through `spx -C <target-dir> session handoff`
SO THAT an agent working in a consumer or product repository that depends on a spec-tree component — the marketplace plugins, the `spx` CLI, or another spec-tree dependency
CAN record a needed follow-up where the dependency's own agents pick it up, instead of editing the dependency's shared installed source directly

## Assertions

### Mappings

- Marketplace registration JSON maps to either the target dependency checkout path or a non-zero diagnostic when the named local marketplace cannot be resolved ([test](tests/test_resolve_marketplace.mapping.l1.py))

### Compliance

- ALWAYS: `/issue` files the follow-up into the target dependency repository's session queue by running `spx -C <target-dir> session handoff`, so the dependency's own session workflow owns the recorded follow-up ([audit])
- ALWAYS: `/issue` resolves the target from the dependency the observation concerns — the marketplace Directory source for the spec-tree plugin, the `spx` CLI checkout for the `spx` dependency — and passes that checkout directory to `spx -C <target-dir> session handoff`, never a single hard-coded target ([audit])
- ALWAYS: `/issue` obtains operator confirmation before its first mutating command against any target the invocation arguments did not name directly as a checkout path, presenting the absolute target root, that repository's normalized origin identity, the resolved git ref, and the follow-up's goal, and stopping on anything but explicit approval with both repositories unchanged ([audit])
- NEVER: `/issue` treats resolving a target as authorization to write to it — a target reached through marketplace resolution or the invoking repository's configuration is confirmed however reliably it resolved ([audit])
- ALWAYS: `/issue` captures only the invoking agent's observation, uncertainty, verified facts, affected paths, and next-workflow context, and shapes them into the handoff body ([audit])
- ALWAYS: `/issue` uses a dependency-followup body whose required sections are observation, uncertainty, checked facts, affected paths, and next-workflow context; it does not use `/handoff`'s node-oriented session body because the invoking agent assigns none of the dependency's internal taxonomy ([audit])
- ALWAYS: `/issue` supplies an output-shaped `goal` and an imperative `next_step` in the handoff header so the target repository's `spx session list` and `spx session todo` surface what the follow-up produces and the first action that resumes it ([audit])
- ALWAYS: `/issue` resolves the invoking runtime identity before filing and verifies that the stored handoff carries the same non-empty `agent_session_id` and a non-empty `created_at` ([audit])
- NEVER: `/issue` records the target dependency's internal taxonomy — a node address, a decision index, an assertion type, or any classification the dependency's own agents assign — the invoking agent supplies observations, not the dependency's spec-tree structure ([audit])
- NEVER: `/issue` edits, commits to, or pushes the target dependency repository's tracked source — its only effect on the target is the handoff session document `spx -C <target-dir> session handoff` writes into that repository's session queue ([audit])
- NEVER: `/issue` alters the invoking repository's own git state or session queue — targeting the dependency through `spx -C <target-dir> session handoff` leaves the invoking checkout untouched ([audit])
- NEVER: `/issue` targets the invoking repository itself — an observation about the current product stays in that product's normal spec-tree workflow rather than entering the dependency-followup path ([audit])
