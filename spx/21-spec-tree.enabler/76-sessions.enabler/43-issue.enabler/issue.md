# Issue

PROVIDES the `/issue` skill — capturing an agent's observation about a spec-tree component and filing one minimal follow-up in the owning repository's active session queue, including when that repository is the invoking repository
SO THAT an agent working in a consumer, dependency, or product repository
CAN record a needed follow-up where that repository's own agents pick it up, without editing installed source directly or running the current work through the full closure workflow

## Assertions

### Mappings

- Marketplace registration JSON maps to either the target dependency checkout path or a non-zero diagnostic when the named local marketplace cannot be resolved ([test](tests/test_resolve_marketplace.mapping.l1.py))

### Compliance

- ALWAYS: `/issue` files the follow-up into the target repository's session queue through `spx session handoff`; for a different repository it targets that dependency checkout, and for the invoking repository it uses a queue-safe checkout without switching, detaching, committing, routing into full `/handoff` closure, or otherwise disturbing the active worktree ([audit])
- ALWAYS: `/issue` resolves the owning checkout from the component the observation concerns — the invoking repository itself when its root carries a `.claude-plugin/marketplace.json` whose marketplace is `outcomeeng` and whose plugin list names `spec-tree`, otherwise the marketplace Directory source for the spec-tree plugin, the `spx` CLI checkout for the `spx` dependency, or the invoking repository for its own product — and runs `spx session handoff` against that repository's queue-safe checkout, never a single hard-coded target and never an operator-supplied path when the invoking checkout already identifies itself as the target ([audit])
- ALWAYS: `/issue` recognizes a target as the invoking repository only when their resolved absolute git common directories match; linked worktrees in the same pool enter the same-repository path, while every separate clone — including one with the same normalized origin identity — remains an external repository target that requires operator confirmation before mutation ([audit])
- ALWAYS: each authorized `/issue` invocation creates exactly one fresh `todo` follow-up; before a same-repository write it reads only the header fields `spx session list --json` returns for `todo` and `doing` sessions, reports as possible overlaps the full ids whose `goal` or `next_step` names an affected path or skill of the observation, and never reads a session body, reuses a session, probes origin for a stored branch, or withholds the write on that basis — queue consumers reconcile overlap at pickup ([audit])
- ALWAYS: `/issue` obtains operator confirmation before its first mutating command against every repository whose resolved git common directory differs from the invoking repository's, presenting the absolute target root, that repository's normalized origin identity, the resolved git ref, and the follow-up's goal, and stopping on anything but explicit approval with both repositories unchanged; the explicit `/issue` invocation itself authorizes one fresh write only to the invoking repository's own shared queue ([audit])
- NEVER: `/issue` treats resolving a different repository as authorization to write to it — a different target reached through marketplace resolution or the invoking repository's configuration is confirmed however reliably it resolved ([audit])
- ALWAYS: `/issue` captures only the invoking agent's observation, uncertainty, verified facts, affected paths, and next-workflow context, and shapes them into the handoff body ([audit])
- ALWAYS: `/issue` uses a dependency-followup body whose required sections are observation, uncertainty, checked facts, affected paths, and next-workflow context; it does not use `/handoff`'s node-oriented session body because the invoking agent assigns none of the dependency's internal taxonomy ([audit])
- ALWAYS: `/issue` supplies an output-shaped `goal` and an imperative `next_step` in the handoff header so the target repository's `spx session list` and `spx session todo` surface what the follow-up produces and the first action that resumes it ([audit])
- ALWAYS: `/issue` resolves the invoking runtime identity before filing and verifies that the stored handoff carries the same non-empty `agent_session_id` and a non-empty `created_at` ([audit])
- NEVER: `/issue` records the target dependency's internal taxonomy — a node address, a decision index, an assertion type, or any classification the dependency's own agents assign — the invoking agent supplies observations, not the dependency's spec-tree structure ([audit])
- NEVER: `/issue` edits, commits to, or pushes the owning repository's tracked source — its only possible effect there is one new handoff session document in that repository's queue ([audit])
- NEVER: `/issue` alters the invoking repository's tracked git state or current branch, or reads the body of, archives, releases, deletes, replaces, or otherwise changes an existing active session; after filing, it reads only the returned record to verify the new minimal `todo` follow-up ([audit])
