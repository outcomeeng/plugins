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
- Durable facts stay in GitHub, the repository, the spec tree, and command output. Re-read those sources on wake-up; conversation memory is not durable and is not a fact source.
- Heartbeat text points to authoritative state; it never copies the full state.
- The continuation prompt is a pointer, never a payload: it names the skills to reload and the pointers each skill must handle (the work-item identifiers, plus the repository when a cold reader needs it to resolve them), and nothing else.
- Never assume conversation memory survives to the next fire. Compaction, session resumption, and a fresh automation thread each discard it, and none can be anticipated when the prompt is written. The wake-up reconstructs the directive, the plan, the finding assessments, and the next action by reloading the named skills and re-reading the durable artifacts (PR body, commits, PLAN.md, ISSUES.md) and live state. If the next fire must know something, write it to a durable artifact — never to the prompt, never to hoped-for retained memory.
- On wake-up, reload the named workflow skills, `/tracking-tasks`, repository instructions, and authoritative state before acting. The reload is mandatory recovery: the protocol a skill carries cannot be assumed to have survived in context, so re-invoking restores it.
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
The continuation prompt carries exactly two things:

1. **The skills to reload** — the owning workflow skill and the references it depends on, always including `/tracking-tasks`. The reloaded skill bodies supply the protocol; the prompt does not.
2. **The pointers each skill must handle** — the work-item identifiers the skill resumes from (PR number, run id, branch, issue, or rollout id), plus the repository when a cold reader needs it to resolve them. The pointers say what each skill operates on; the skill resolves everything else from them.

It carries nothing else. The wake-up reconstructs the directive, the plan, the finding assessments, the next action, and the stop condition by reloading the named skills and re-reading the durable artifacts (PR body, commits, `PLAN.md`, `ISSUES.md`) and live state. The prompt is not a memory: it is re-sent unchanged on every fire, it would be stale by fire time, and conversation memory is never assumed to survive (compaction, resumption, or a fresh thread can discard it, none anticipable). So the directive, the finding assessments, and the rationale never appear in the prompt — if the next fire must know something, it is written to a durable artifact (`PLAN.md` / `ISSUES.md`), the source the wake-up already re-reads.

A re-entry into a context that still holds the prior conversation can be as terse as the re-entry command plus the work-item pointer; a cold reader (a fresh thread) needs the repository and the skills named explicitly so the pointers resolve. The two differ only in how much a reader needs to resolve the same pointers — neither carries state.
</heartbeat_payload>

<stale_context_boundary>
NEVER copy these into a heartbeat:

- full PR bodies, full plans, full review histories, or full CI logs
- long evidence summaries already posted to GitHub
- outdated prior-head feedback except as a pointer to a URL when needed
- expected future check conclusions that can be read from GitHub
- repository policy text available from AGENTS.md, local overlays, or skills
- detailed implementation rationale already captured in commits, specs, or comments
- the directive, the finding assessments, the rationale, or any reasoning the wake-up reconstructs from the reloaded skills and durable artifacts — the prompt names skills and pointers only

</stale_context_boundary>

<lifecycle>
Create tracking when active work is blocked only by time, pending checks, pending review, host load, external convergence, or a delayed repository-governed action.

Refresh tracking on a new commit, run id, PR number, blocker, approval boundary, failure classification, or next repository action. Refreshing re-schedules the next fire and updates the pointer when the work-item id itself changes; it never writes the blocker, approval boundary, or failure classification into the prompt — that state is reconstructed on wake-up, and anything a later fire needs is written to a durable artifact.

Keep tracking active when state is queued, in progress, pending, retry-after-classification, awaiting deterministic local repair, or waiting for external convergence.

Convert tracking to a repair path when a failure is deterministic and can be fixed locally. The next fire re-sends the same skills-and-pointers prompt unchanged; the failed layer, the log source, and the next repair checkpoint are written to `PLAN.md` / `ISSUES.md` so the next fire reconstructs them from there.

Delete tracking when the PR is merged and post-merge verification is green, the work item is closed, the task acceptance condition is met, or the only remaining step is operator approval and the owning workflow says to stop for approval.
</lifecycle>

<runtime_timer>
Use the runtime timer or heartbeat tool; never use shell waits, polling loops, watch commands, or background keep-alives. Select the tool by runtime:

- **Claude Code:** `ScheduleWakeup` for a single delayed re-check, or `/loop` for recurring re-inspection. The prompt names the owning skill and the pointers it handles per `<heartbeat_payload>`; the wake-up reloads the skill and reconstructs state from the durable artifacts and live state. `ScheduleWakeup`'s instruction to "pass the same input verbatim each turn" means re-send that same skills-and-pointers prompt every fire; it never means expand it into a self-contained directive. Default the PR and CI cadence to four minutes (240 s) — under the five-minute prompt-cache TTL, so the next wake reuses the warm cache.
- **Codex:** thread automation, which may open a fresh thread. The prompt names the repository, the skills to reload, and the pointers each handles, so a cold thread can resolve them; it does not carry the directive or the reasoning. Cadence is minute-based, typically every three minutes.

For any thread heartbeat or automation tool:

- create or update the existing work-item heartbeat
- attach it to the current thread when the work continues in the same conversation
- use the owning workflow cadence from the per-runtime default above
- include a sparse prompt following `<heartbeat_payload>`
- delete it as soon as `<lifecycle>` says no timer-backed repository action remains

</runtime_timer>

<prompt_template>
The prompt is the skills to reload plus the pointers each handles — nothing the wake-up can reconstruct.

Warm re-entry (a context that may still hold the prior conversation) — name the owning skill and its pointer:

```text
/<owning-workflow-command> <work-item-pointer>
```

Cold re-entry (a fresh thread) — name the repository, the skills to reload, and the pointers each handles, so they resolve without the prior conversation:

```text
Resume <owning skill> (+ /tracking-tasks) for <repo path> <work-item pointer>. Reload the skills, re-read the durable artifacts (PR body, commits, PLAN.md, ISSUES.md) and live state, and continue from there.
```

Neither form carries the directive, the finding assessments, or the rationale; those are reconstructed, and anything the next fire needs lives in a durable artifact.
</prompt_template>

<failure_handling>

- Queued, in-progress, and pending states: report material changes, refresh the heartbeat, and continue on the next wake-up.
- Failed, cancelled, or timed-out checks: fetch failed logs once, classify the failed layer, write the failed layer, log source, and next repair checkpoint to `PLAN.md` / `ISSUES.md` (never into the prompt), and keep the work active unless the next step requires operator approval, credentials, or judgment.
- Review feedback: fix safe local issues, run the governed local review and validation loop, push, then refresh tracking for current-head checks and review.
- High host load: record the load condition, schedule the next load-aware checkpoint, and avoid starting heavy validation.
- Missing approval: stop the work item at the approval boundary, delete heartbeat tracking, and ask with the identifiers, effect, and non-effect required by the owning workflow.

</failure_handling>

<success_criteria>
Tracking is correct when:

- every heartbeat-producing skill loads `/tracking-tasks` before mutating runtime tracking
- the continuation prompt carries only the skills to reload and the pointers each handles — never the directive, finding assessments, or rationale, which are reconstructed on wake-up; anything the next fire needs is written to a durable artifact
- wake-ups reload the named skills and re-read authoritative state before acting, never assuming conversation memory survived
- failed checks stay in the active workflow until classified and repaired or blocked by an explicit operator decision
- shell waits, polling loops, watch commands, and duplicate heartbeats are absent
- heartbeat deletion happens only at acceptance, closure, no remaining repository action, or approval-only boundary

</success_criteria>
