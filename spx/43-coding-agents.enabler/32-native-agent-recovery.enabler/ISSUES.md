# ISSUES — native agent recovery

Coordination note; not spec truth.

## DEBT [evidence]: no deterministic guard rejects an oversized destroyed fact

`reassessment_prompt` concatenates `NON_CONTROLLER_BOUNDARY` (~190 characters) with the
operator-supplied `restored[].text` and `_restored_facts` accepts that text unchecked, so the
one-short-line rule the skill's `<constraints>` and `<failure_modes>` declare is enforced only by
prose instructing the invoking agent. An oversized destroyed fact still reaches `send`, collapses
into a `[Pasted text #1]` attachment no `Enter` submits, and strands silently in the recipient's
editor — the exact incident the failure mode records.

**Resolution shape**: reject the delivery in `_restored_facts` with an `AdapterError` when the
combined boundary and destroyed fact exceed the recipient TUI's paste-collapse threshold, and cover
the rejection with compliance evidence.

**Deferral reason**: the guard needs a threshold this product has not established. The recorded
incident proves 1,300 characters collapses; it does not locate the boundary, which belongs to the
recipient TUI rather than to this script and differs between the Claude and Codex surfaces this
skill drives. Writing a guessed constant into a deterministic guard would reject valid deliveries on
an invented number, so the bounded code change waits on measuring the real threshold per surface —
an empirical task against two external TUIs, not an edit to this file.

## DEBT [correctness]: the attested exemption binds a pane id rather than its candidate

`src/plugins/coding-agents/skills/recover-prowl-agents/scripts/recover_agents.py` computes
`is_attested = attested is not None and binding.pane_id == attested.pane_id` in `recover`, granting
the sessionless-occupant exemption to whichever binding carries that pane id without confirming that
binding's candidate is the attested candidate. `15-exact-native-recovery.adr.md` states the
attestation binds "to the single current-session candidate", so a co-located authorized secondary
sharing the controller's worktree inherits an exemption the invariant reserves for one candidate.

**Resolution shape**: require `candidate.original_pane_id == attested.candidate.original_pane_id`
(or `candidate.evidence is EvidenceSource.CURRENT_SESSION`) alongside the pane-id match, and add
mapping evidence for a co-located authorized secondary while the controller pane is attested.

**Reachability**: the skill's own workflow always derives bindings from `plan_activation`, which
pairs each pane with one candidate, so no supported invocation reaches the divergence today. The
defect is a latent contradiction with the ADR, not a live failure.

## DEBT [conformance]: the Codex plugin manifest omits the Write capability

`src/plugins/coding-agents/.codex-plugin/plugin.json` declares `interface.capabilities` as
`["Read"]` while `src/plugins/coding-agents/skills/recover-prowl-agents/SKILL.md` declares `Write`
in its `allowed-tools`. Every other plugin in this marketplace that ships a Write-using skill
declares `["Read", "Write"]`, so this manifest understates what the plugin's skills do.

**Resolution shape**: add `"Write"` to `interface.capabilities`, then `just bump`,
`just build-skills`, and the gate cycle the plugin-distribution surface requires.

## DEBT [instruction]: prepare never tells the operator to resume the controller

`src/plugins/coding-agents/skills/recover-prowl-agents/SKILL.md` `<prepare_workflow>` step 8 reports
the manifest path and candidate count and states that Prowl may restart. It never states that the
session driving recovery must be the manifest's own current-session candidate, so a post-restart
operator naturally starts a fresh session, whose attestation cannot identify a current-session
candidate and whose own agent is absent from the manifest. `<recover_workflow>` step 2 assumes an
already-resumed controller without saying who resumes it.

**Resolution shape**: extend `<prepare_workflow>` step 8 to name the exact resumption the operator
performs before recovery — resume the recorded driving session in its own worktree, then drive
`recover` from it — and state the same precondition in `<recover_workflow>` step 1. The node spec
now declares the driver-identity rule; the skill body still carries no instruction for it.
