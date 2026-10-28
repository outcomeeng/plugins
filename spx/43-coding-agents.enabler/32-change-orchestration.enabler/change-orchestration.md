---
id: 01a0f110-cfe6-70b6-8a53-a0deaf6c0c97
malleability: spec
---

# Change Orchestration

PROVIDES the Orchestrator position's duties for one Change — claiming it for an Applier, starting that Applier's agent session, checking its progress, and passing questions up the chain of positions
SO THAT an operator
CAN have each Executable Change applied by its own Applier session without opening that session's pane

The Orchestrator is a position, never one of the five Roles: it holds no Role for the Change it orchestrates and produces no artifact of it. The Applier it starts holds the Change and applies it through `spx/31-outcomeeng.enabler/32-changes.enabler/65-change-execution.enabler`.

## Assertions

### Compliance

- ALWAYS: `/orchestrate-change` claims one Change for its Applier, naming the Applier's worktree root, and starts one Applier session for it in the root pane `spx/43-coding-agents.enabler/18-herdr-environment.enabler` returns when it creates the Applier's worktree, for a root absent from the pool, or opens the existing one, either grouped with the herdr workspace the invocation names; on Claude Code the session starts with the product-tree definition `change-applier` selected ([audit:applier-start])
- ALWAYS: on Codex, `/orchestrate-change` Start returns an explicit `unavailable` result naming the Change and writes no store state, while Check runs unchanged; on Claude Code, Start returns no such result ([audit:codex-start-unavailable])
- ALWAYS: the Applier session's start and every resume withhold the harness's structured-question tool through the harness setting alone; no skill detects whether its session is an Applier ([audit:structured-question-withheld])
- ALWAYS: `/orchestrate-change` names `change-applier` as the one configured definition it starts, and starts no session through any other definition ([audit:single-applier-definition])
- ALWAYS: a start the harness's classifier refuses is retried once, only after retracing the refused request, the classifier's reason, and each step that shaped the request, and changed only by the correction that retrace finds, so a retrace that finds no defect resubmits the request unchanged; a second refusal stops the start and reports the refused request, the reason, and the Claim still held to the Orchestrator's principal ([audit:refused-start-retry])
- ALWAYS: the Orchestrator checks each Applier at regular intervals and, finding one stalled or near its context limit, prompts, compacts or restarts it; a restarted Applier relaunches into the pane its stop kept, after the Change is claimed again for that worktree, and continues from the Change and its latest Handoff ([audit:stalled-applier-checks])
- ALWAYS: across the Changes one Orchestrator orchestrates, it settles blockers and questions in the order the coordination overlay declares for the Change store's priority field, and orders Changes of equal priority, and every Change when the overlay declares no priority field, by ascending issue number ([audit:change-priority-order])
- ALWAYS: the Orchestrator answers no question the Applier raises; it passes each one verbatim, once per Handoff, to its principal as a message record of `spx/43-coding-agents.enabler/21-agent-communication.enabler` ([audit:question-passing])
- NEVER: the Orchestrator acts as a Verifier ([audit:orchestrator-not-verifier])
- ALWAYS: `/orchestrate-change` reads the Change's Lifecycle from the store at each check, and ends its checks of that Applier when the Lifecycle is `Applied` or `Abandoned` ([audit:lifecycle-check])
- NEVER: the Orchestrator sends a prompt or keystroke into a pane whose Applier session waits at a question or approval screen; it reports the screen verbatim to the principal as a message record, once per screen under one correlation per Change, and ends that check ([audit:no-prompt-at-question-screen])
- ALWAYS: `/orchestrate-change` finds an earlier screen report among its principal's records through the agent-mail capability's list operation with the all-records option, and reads or acknowledges none of them ([audit:screen-report-lookup])
- ALWAYS: the Orchestrator stops the session of an Applier that released its Change, other than a release its Hazards attribute to the session itself ending, stalling or running out of context, once the worktree status shows no running Applier work and the pane does not wait at a question or approval screen, which it reports instead and neither stops nor prompts; the stop leaves the pane at its shell and retains the worktree and its ignored drafts ([audit:released-applier-stop])
- ALWAYS: before each Applier start or relaunch, `/orchestrate-change` obtains from SPX's `spx verification run paths` the canonical write paths of the verification runs the Applier session records, supplies each path through the harness's supported parent-session permission configuration, on Claude Code an additional-directory option among the start's agent arguments, and preserves the operator's approval policy ([audit:launch-write-paths])
- ALWAYS: after each Applier start or relaunch and before sending the Change's issue reference, `/orchestrate-change` runs a permission preflight that checks the Applier session's effective native child policy for write access to each supplied path, and stops with a configuration error naming each path the policy denies ([audit:permission-preflight])
- ALWAYS: `/orchestrate-change` plans permissions anew for each start, each relaunch, and each changed verification scope ([audit:renewed-planning])
