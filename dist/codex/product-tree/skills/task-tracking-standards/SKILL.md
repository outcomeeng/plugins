---
name: task-tracking-standards
user-invocable: false
description: >-
  Runtime task-tracking standards for skills that schedule heartbeats or timers. Loaded by other skills, not invoked directly.
allowed-tools: Read
---

<objective>
One shared standard for routing heartbeat and timer creation that keeps active repository work alive across external waits.
</objective>

<reference_note>
This is a reference skill; `<when_to_load>` names the moments it applies. The heartbeat is the runtime tool; this skill owns the rules for using that tool.
</reference_note>

<when_to_load>
Load this skill before any workflow:

- creates or refreshes a heartbeat for a workflow whose governing skill has no foreground wait command
- schedules a delayed rollout or external-convergence re-check
- deletes a heartbeat because acceptance is reached, the work item closed, or the only remaining action is operator approval
- launches local work — a command or a subagent — and must choose between ending the turn for a completion notification and collecting the result within the active turn

</when_to_load>

<principles>
- Runtime tracking is a coordination handle for the next wake-up. Keep it sparse.
- Durable facts stay in GitHub, the repository, the Product Tree, and command output. Re-read those sources on wake-up; conversation memory is not durable and is not a fact source.
- The continuation prompt is a pointer, never a payload; `<heartbeat_payload>` defines its content.
- On wake-up, reload the named workflow skills, this skill, repository instructions, and authoritative state before acting. The reload is mandatory recovery: the protocol a skill carries cannot be assumed to have survived in context, so re-invoking restores it.
- A failed check keeps the work active. Fetch failed logs once, classify the layer, then continue the repair loop or ask for the exact missing approval, credential, or judgment.

</principles>

<authoritative_sources>
Use pointers to these sources instead of copying their contents into a heartbeat:

- GitHub run state outside the PR-check lifecycle, comment state, and review-thread state
- local branch, remote branch, base branch, and worktree status
- repository specs, ADRs, PDRs, PLAN.md, ISSUES.md, AGENTS.md, and local overlays
- workflow handoff artifacts and command outputs stored in the repository or GitHub
- current conversation approval, credential, and judgment decisions

</authoritative_sources>

<heartbeat_payload>
The continuation prompt carries exactly two things:

1. **The skills to reload** — the owning workflow skill and the references it depends on, always including this skill. The reloaded skill bodies supply the protocol; the prompt does not.
2. **The pointers each skill must handle** — the work-item identifiers the skill resumes from (PR number, run id, branch, issue, or rollout id), plus the repository when a cold reader needs it to resolve them. The pointers say what each skill operates on; the skill resolves everything else from them.

It carries nothing else. The wake-up reconstructs the directive, the plan, the finding assessments, the next action, and the stop condition by reloading the named skills and re-reading the durable artifacts (PR body, commits, `PLAN.md`, `ISSUES.md`) and live state. The prompt is re-sent unchanged on every fire and would be stale by fire time, so the directive, the finding assessments, and the rationale never appear in it. If the next fire must know something, write it to a durable artifact (`PLAN.md` / `ISSUES.md`), the source the wake-up already re-reads.
</heartbeat_payload>

<stale_context_boundary>
NEVER copy these into a heartbeat:

- full PR bodies, full plans, full review histories, or full CI logs
- long evidence summaries already posted to GitHub
- outdated prior-head feedback except as a pointer to a URL when needed
- expected future check conclusions that can be read from GitHub
- repository policy text available from AGENTS.md, local overlays, or skills
- detailed implementation rationale already captured in commits, specs, or comments

</stale_context_boundary>

<lifecycle>
Create tracking when active work is blocked only by time, external convergence, or a delayed repository-governed action whose governing skill has no foreground wait command.

Refresh tracking on a new commit, run id, work-item id, blocker, approval boundary, failure classification, or next repository action. Refreshing re-schedules the next fire and updates the pointer when the work-item id itself changes.

Keep tracking active when state is queued, in progress, pending, retry-after-classification, awaiting deterministic local repair, or waiting for external convergence, excluding GitHub PR check waits.

Convert tracking to a repair path when a failure is deterministic and can be fixed locally. Write the failed layer, the log source, and the next repair checkpoint to `PLAN.md` / `ISSUES.md`.

Delete tracking when the PR is merged and every declared deploy or release phase has completed or no-oped, the work item is closed, the task acceptance condition is met, or the only remaining step is operator approval and the owning workflow says to stop for approval.
</lifecycle>

<runtime_timer>
Use the runtime timer or heartbeat tool when available. Select the tool by runtime:

- **Claude Code:** `ScheduleWakeup` for a single delayed re-check, or `/loop` for recurring re-inspection. `ScheduleWakeup`'s instruction to "pass the same input verbatim each turn" means re-send that same skills-and-pointers prompt every fire; it never means expand it into a self-contained directive.
- **Codex:** use a timer or automation capability only when the active harness exposes and documents one. When none is exposed, report the exact external condition and durable work-item pointer, keep the work active, end the turn, and resume only from operator re-entry or an external completion notification. Never manufacture a shell timer.

A scheduled heartbeat is the turn's continuation, not its close. When a scheduled wake-up is the next action, do not append a structured question to close the turn — the wake-up is the continuation. End such a turn by reporting status and the scheduled re-check, with no question and no trailing prose offer.

For any documented and exposed runtime heartbeat or automation tool, create or update the one work-item heartbeat — attached to the current thread when the work continues in the same conversation — at the cadence supplied by the owning workflow or tool contract, following `<heartbeat_payload>` for prompt shape and `<lifecycle>` for the create, refresh, and delete triggers. This reference defines no runtime-specific default cadence.

Never use shell `sleep`, `gh run watch`, `until`/`while` polling, a backgrounded watcher, or a background keep-alive as a timer substitute.

</runtime_timer>

<local_background_work>
A runtime timer or heartbeat is for a wait the harness cannot observe — external state such as a rollout or service convergence. Local work the session itself launches needs neither a timer nor a poll.

This harness documents no wake of the session when a background process exits, so the session owns every local wait and collects its result itself. Run a local command in the foreground with a timeout large enough to cover it — one bounded invocation — and collect its result within the active turn. When the command cannot finish within the turn, move the work to the next step boundary. Collect a subagent launch within the active turn through the native wait capability. Never start a local command in the background, never expect a completion notification to resume the session, and never create a heartbeat to re-check it.

Never poll a local command in-shell with a wait loop, a `sleep`, or a watch command. The poll loop spawns a process tree per iteration that the harness does not reap, and across turns and concurrent agents it exhausts the host's process limit.

</local_background_work>

<prompt_template>
The prompt is the skills to reload plus the pointers each handles — nothing the wake-up can reconstruct.

Warm re-entry (a context that may still hold the prior conversation) — name the owning skill and its pointer:

```text
Resume /<owning-workflow-command> (+ /task-tracking-standards) for <work-item-pointer>.
```

Cold re-entry (a fresh thread) — name the repository, the skills to reload, and the pointers each handles, so they resolve without the prior conversation:

```text
Resume <owning skill> (+ /task-tracking-standards) for <repo path> <work-item pointer>. Reload the skills, re-read the durable artifacts (PR body, commits, PLAN.md, ISSUES.md) and live state, and continue from there.
```

</prompt_template>

<failure_modes>

**Background launch awaiting a wake that never comes**

- **What happened:** Claude started a local command in the background and ended the turn to wait for a completion notification.
- **Why it failed:** This harness documents no wake when a background process exits, so nothing resumed the session and the result went uncollected.
- **How to avoid:** Run the command in the foreground with a timeout that covers it and collect the result within the active turn, or move the work to the next step boundary.

**Stale heartbeat payload**

- **What happened:** Claude copied the current directive, plan, and finding assessments into a heartbeat prompt.
- **Why it failed:** The branch advanced before the wake-up, so the prompt resumed stale conclusions against a new head.
- **How to avoid:** Build the prompt as `<heartbeat_payload>` defines it.

**Local command polling**

- **What happened:** Claude polled a local command with repeated shell sleeps.
- **Why it failed:** Every iteration added another monitored process tree until process and file-descriptor pressure disrupted unrelated work.
- **How to avoid:** Run one foreground command with an adequate timeout and collect it within the active turn, or move the work to the next step boundary.

</failure_modes>

<failure_handling>

- Queued, in-progress, and pending states outside the PR-check lifecycle: report material changes, refresh the heartbeat, and continue on the next wake-up.
- Failed, cancelled, or timed-out external work: fetch failed logs once, classify the failed layer, write the failed layer, log source, and next repair checkpoint to `PLAN.md` / `ISSUES.md`, and keep the work active unless the next step requires operator approval, credentials, or judgment.
- Missing approval: stop the work item at the approval boundary, delete heartbeat tracking, and ask with the identifiers, effect, and non-effect required by the owning workflow.

</failure_handling>

<success_criteria>
Tracking is correct when:

- the continuation prompt matches `<heartbeat_payload>`
- wake-ups reload the named skills and re-read authoritative state before acting, never assuming conversation memory survived
- failed checks stay in the active workflow until classified and repaired or blocked by an explicit operator decision
- shell `sleep`, polling loops, `gh run watch`, background keep-alives, backgrounded watchers, and duplicate heartbeats are absent
- local work runs in the foreground with an adequate timeout and is collected within the active turn, or moves to the next step boundary — never a background launch, a poll loop, or a heartbeat that waits for a notification
- heartbeat deletion happens only at acceptance, closure, no remaining repository action, or approval-only boundary

</success_criteria>
