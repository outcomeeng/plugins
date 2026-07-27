# PLAN — native agent recovery

Coordination note; not spec truth.

## Declare and verify the controller-pane attestation contract

The recovery script carries a controller-pane attestation mechanism that no assertion declares
and no test exercises: the `AttestedController` dataclass, `_attested_controller`, its binding
branch in `plan_activation`, its occupancy bypass in `recover`, and the `controllerPaneId` field
threaded through the `activate` and `recover` CLI dispatch and through `<recover_workflow>`
steps 3 and 7. `attested` appears nowhere in this node's spec, its ADR, or the harness.

The mechanism exists because a controller whose native transcript resolves under a different
project root than its worktree is read as a mismatched occupant of its own pane, which stops
activation. That is real behavior with no declaration above it, so the truth hierarchy has no
spec for the code to comply with.

**Resolution shape**: add one `[test]`-tagged Mappings assertion to
`native-agent-recovery.md` declaring that an attested controller pane maps to a binding for its
own current-session candidate, while an attestation whose pane, worktree, agent type, or session
does not identify that candidate maps to a named non-mutating failure. Add the matching Testing
rule to `15-exact-native-recovery.adr.md`. Cover it in the mapping lane through `plan_activation`
and `recover`, exercising the successful attested binding, the `session_id`-is-None occupancy
bypass, and each of the five `AdapterError` branches in `_attested_controller`: no
current-session candidate, the attested pane absent from the post-restart panes, a worktree that
is not the controller candidate's, more than one agent on the pane, and an agent type or session
that is another's.

Write the new predicates in the linked test file rather than the harness, following
`observe_wholly_intact_settlement` and `test_wholly_intact_candidate_set_maps_to_recorded_identities`
— the harness exposes the observations, the test owns every comparison. That keeps this coverage
clear of the seam DEBT recorded in this node's `ISSUES.md` instead of extending it.

**Evidence**: raised as a blocking `[evidence]` finding by the changeset review of
`origin/main...f0cd8ff4c` (run `2026-07-27_21-47-02-646-3a6306728e7b`), and confirmed against
`origin/main`, where `attested` has no occurrences.
