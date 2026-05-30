---
name: tracking-tasks
user-invocable: false
description: >-
  Runtime task-tracking standards for skills that schedule heartbeats or timers. Loaded by other skills, not invoked directly.
---

<objective>
Keep active repository work alive across external waits by routing heartbeat and timer creation through one shared tracking standard. Use this reference whenever a skill creates, refreshes, or deletes a delayed re-check for PR, CI, review, release, rollout, or verification work.
</objective>

<reference_note>
This is a reference skill. Load it from the owning workflow skill before creating, updating, or deleting a heartbeat, timer, wakeup, recurring re-check, or automation. The heartbeat is the runtime tool; this skill owns the rules for using that tool.
</reference_note>

<when_to_load>
Load `/tracking-tasks` before any workflow:

- creates the first heartbeat for an opened PR
- refreshes a heartbeat after a new commit, new run, new blocker, failed check, or pending review state
- schedules a delayed CI, PR, rollout, host-load, or external-convergence re-check
- deletes a heartbeat because acceptance is reached, the work item closed, or the only remaining action is operator approval

</when_to_load>

<principles>
- Runtime tracking is a coordination handle for the next wake-up. Keep it sparse.
- Durable facts stay in GitHub, the repository, the spec tree, command output, and conversation history. Re-read those sources on wake-up.
- Heartbeat text points to authoritative state; it never copies the full state.
- On wake-up, reload the owning workflow skill, `/tracking-tasks`, repository instructions, and authoritative state before acting.
- A failed check keeps the work active. Fetch failed logs once, classify the layer, then continue the repair loop or ask for the exact missing approval, credential, or judgment.
- "Stop before retrying" means classify before rerunning the same external job. It never means abandon active work.
- Pending checks, pending review, high host load, or delayed external convergence require an updated heartbeat before ending the turn.
- Use one active heartbeat per work item. Refresh it instead of creating duplicates.
- Delete a heartbeat only when no timer-backed repository action remains.

</principles>

<authoritative_sources>
Use pointers to these sources instead of copying their contents into a heartbeat:

- GitHub PR, run, check, review, comment, and review-thread state
- local branch, remote branch, base branch, and worktree status
- repository specs, ADRs, PDRs, PLAN.md, ISSUES.md, AGENTS.md, and local overlays
- workflow handoff artifacts and command outputs stored in the repository or GitHub
- current conversation approval, credential, and judgment decisions

</authoritative_sources>

<heartbeat_payload>
Every heartbeat prompt MUST contain only the minimum continuation state:

- work item: repository path plus PR number, run id, branch, issue, or rollout identifier
- owning workflow skills to reload, including `/tracking-tasks`
- authoritative sources to inspect once on wake-up
- current blocker condition
- exact next inspection command or tool action
- action to take when the blocker clears
- failure branch for failed, cancelled, or timed-out checks
- approval boundary and forbidden actions
- stop/delete condition

Keep the payload short enough that stale context cannot crowd out live state.
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
Create tracking when active work is blocked only by time, pending checks, pending review, host load, external convergence, or a delayed repository-governed action.

Refresh tracking when the work item gains a new commit, run id, PR number, blocker, approval boundary, failure classification, or next repository action.

Keep tracking active when state is queued, in progress, pending, retry-after-classification, awaiting deterministic local repair, or waiting for external convergence.

Convert tracking to a repair path when a failure is deterministic and can be fixed locally. The next heartbeat names the failed layer, the exact source of logs or feedback, and the next repair checkpoint.

Delete tracking when the PR is merged and post-merge verification is green, the work item is closed, the task acceptance condition is met, or the only remaining step is operator approval and the owning workflow says to stop for approval.
</lifecycle>

<runtime_timer>
Use the runtime timer or heartbeat tool; never use shell waits, polling loops, watch commands, or background keep-alives. Select the tool by runtime:

- **Claude Code:** `ScheduleWakeup` for a single delayed re-check, or `/loop` for recurring re-inspection. Pass a continuation prompt that re-enters the owning workflow. Default the PR and CI cadence to four minutes (240 s) — under the five-minute prompt-cache TTL, so the next wake reuses the warm cache.
- **Codex:** thread automation. The runtime may start a new thread, so the prompt names the repository, work item, branch, and the next repository-governed action. Cadence is minute-based, typically every three minutes.

For any thread heartbeat or automation tool:

- create or update the existing work-item heartbeat
- attach it to the current thread when the work continues in the same conversation
- use the owning workflow cadence from the per-runtime default above
- include a sparse prompt following `<heartbeat_payload>`
- delete it as soon as `<lifecycle>` says no timer-backed repository action remains

</runtime_timer>

<prompt_template>
Use this shape and replace placeholders with concise values:

```text
Continue <owning workflow> for <repo path> <work item>. Load <owning skills> and /tracking-tasks. Inspect <authoritative source> once. Current blocker: <condition>. When clear, run <next repository-governed action>. On failed/cancelled/timed_out checks, fetch failed logs once, classify the layer, and keep the work active through repair or the approval gate. Forbidden: <runtime/project bans>. Stop/delete when <acceptance condition or approval-only boundary>.
```

</prompt_template>

<failure_handling>

- Queued, in-progress, and pending states: report material changes, refresh the heartbeat, and continue on the next wake-up.
- Failed, cancelled, or timed-out checks: fetch failed logs once, classify the failed layer, and keep the work active unless the next step requires operator approval, credentials, or judgment.
- Review feedback: fix safe local issues, run the governed local review and validation loop, push, then refresh tracking for current-head checks and review.
- High host load: record the load condition, schedule the next load-aware checkpoint, and avoid starting heavy validation.
- Missing approval: stop the work item at the approval boundary, delete heartbeat tracking, and ask with the identifiers, effect, and non-effect required by the owning workflow.

</failure_handling>

<success_criteria>
Tracking is correct when:

- every heartbeat-producing skill loads `/tracking-tasks` before mutating runtime tracking
- heartbeat prompts contain pointers, blocker, next action, failure branch, approval boundary, and stop rule only
- wake-ups reload owning skills and authoritative state before acting
- failed checks stay in the active workflow until classified and repaired or blocked by an explicit operator decision
- shell waits, polling loops, watch commands, and duplicate heartbeats are absent
- heartbeat deletion happens only at acceptance, closure, no remaining repository action, or approval-only boundary

</success_criteria>
