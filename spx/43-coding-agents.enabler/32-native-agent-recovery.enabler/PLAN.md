# Plan — native agent recovery

Pending work induced by higher truth. Governing decision:
`spx/43-coding-agents.enabler/32-native-agent-recovery.enabler/15-exact-native-recovery.adr.md`.

## Route the three untagged lifecycle assertions through `/verify`

`spx/43-coding-agents.enabler/32-native-agent-recovery.enabler/native-agent-recovery.md` opens
`## Assertions` with three untagged declarations — driver identity, interrupted-run resumption, and
per-step repetition — and the ADR carries their three untagged `## Verification` rules. `/apply`
invokes `/verify` to select each one's verification type, and `/test` selects the assertion type
when verify selects test. Authoring selected neither.

## Collapse the narrow idempotence property into the general one

The existing Properties entry — "Repeating recovery after every prepared candidate has one exact
distinct post-restart correlation and every non-controller session is durably reassessed emits no
activation, native command, or reassessment instruction" — is the whole-lifecycle special case of
the new per-step repetition assertion, which holds however far an interrupted run advanced. Two
assertions making one claim through the same evidence mechanism is duplication. Resolving it moves
a `[test]` link, so it belongs to `/verify` routing the new assertion rather than to authoring.

## Implement the declared lifecycle in the shipped script

`src/plugins/coding-agents/skills/recover-prowl-agents/scripts/recover_agents.py` records no driving
session identity and reads no per-step resume state: `prepare` writes candidates and
`reassessedSessionIds`, and each later operation recomputes its plan from the manifest plus
caller-supplied public arrays. The declarations lead the implementation, which
`/understand` `<future_product_truth>` permits; the node stays failing against them until `/apply`
carries the evidence and the source.
