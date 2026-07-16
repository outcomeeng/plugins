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
This is a reference skill. Skills that create, update, or delete a heartbeat or timer load it via the Skill tool; `<when_to_load>` names the moments. The heartbeat is the runtime tool; this skill owns the rules for using that tool. Do not load this skill for GitHub PR check/review waits governed by /merging-standards; those use `gh pr checks <pr-number> --watch --fail-fast --interval 30` directly.
</reference_note>

<when_to_load>
Load `/task-tracking-standards` before any workflow:

- creates or refreshes a heartbeat for a workflow whose governing skill has no foreground wait command
- schedules a delayed rollout, host-load, or external-convergence re-check
- deletes a heartbeat because acceptance is reached, the work item closed, or the only remaining action is operator approval
- launches local background work the harness tracks — a backgrounded command or a subagent — and must choose between ending the turn for the completion notification and running it in the foreground with an adequate timeout

</when_to_load>

<principles>
- Runtime tracking is a coordination handle for the next wake-up. Keep it sparse.
- Durable facts stay in GitHub, the repository, the spec tree, and command output. Re-read those sources on wake-up; conversation memory is not durable and is not a fact source.
- Heartbeat text points to authoritative state; it never copies the full state.
- The continuation prompt is a pointer, never a payload: it names the skills to reload and the pointers each skill must handle (the work-item identifiers, plus the repository when a cold reader needs it to resolve them), and nothing else.
- Never assume conversation memory survives to the next fire. Compaction, session resumption, and a fresh automation thread each discard it, and none can be anticipated when the prompt is written. The wake-up reconstructs the directive, the plan, the finding assessments, and the next action by reloading the named skills and re-reading the durable artifacts (PR body, commits, PLAN.md, ISSUES.md) and live state. If the next fire must know something, write it to a durable artifact — never to the prompt, never to hoped-for retained memory.
- On wake-up, reload the named workflow skills, `/task-tracking-standards`, repository instructions, and authoritative state before acting. The reload is mandatory recovery: the protocol a skill carries cannot be assumed to have survived in context, so re-invoking restores it.
- A failed check keeps the work active. Fetch failed logs once, classify the layer, then continue the repair loop or ask for the exact missing approval, credential, or judgment.
- "Stop before retrying" means classify before rerunning the same external job. It never means abandon active work.
- High host load or delayed external convergence requires an updated heartbeat before ending the turn when the governing workflow has no foreground wait command.
- Use one active heartbeat per work item. Refresh it instead of creating duplicates.
- Delete a heartbeat only when no timer-backed repository action remains.

</principles>

<authoritative_sources>
Use pointers to these sources instead of copying their contents into a heartbeat:

- GitHub run state outside the PR-check lifecycle, comment state, and review-thread state
- local branch, remote branch, base branch, and worktree status
- repository specs, ADRs, PDRs, PLAN.md, ISSUES.md, CLAUDE.md, and local overlays
- workflow handoff artifacts and command outputs stored in the repository or GitHub
- current conversation approval, credential, and judgment decisions

</authoritative_sources>

<heartbeat_payload>
The continuation prompt carries exactly two things:

1. **The skills to reload** — the owning workflow skill and the references it depends on, always including `/task-tracking-standards`. The reloaded skill bodies supply the protocol; the prompt does not.
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
- repository policy text available from CLAUDE.md, local overlays, or skills
- detailed implementation rationale already captured in commits, specs, or comments
- the directive, the finding assessments, the rationale, or any reasoning the wake-up reconstructs from the reloaded skills and durable artifacts — the prompt names skills and pointers only

</stale_context_boundary>

<lifecycle>
Create tracking when active work is blocked only by time, host load, external convergence, or a delayed repository-governed action whose governing skill has no foreground wait command.

Refresh tracking on a new commit, run id, work-item id, blocker, approval boundary, failure classification, or next repository action. Refreshing re-schedules the next fire and updates the pointer when the work-item id itself changes; it never writes the blocker, approval boundary, or failure classification into the prompt — that state is reconstructed on wake-up, and anything a later fire needs is written to a durable artifact.

Keep tracking active when state is queued, in progress, pending, retry-after-classification, awaiting deterministic local repair, or waiting for external convergence, excluding GitHub PR check waits governed by /merging-standards.

Convert tracking to a repair path when a failure is deterministic and can be fixed locally. The next fire re-sends the same skills-and-pointers prompt unchanged; the failed layer, the log source, and the next repair checkpoint are written to `PLAN.md` / `ISSUES.md` so the next fire reconstructs them from there.

Delete tracking when the PR is merged and every declared deploy or release phase has completed or no-oped, the work item is closed, the task acceptance condition is met, or the only remaining step is operator approval and the owning workflow says to stop for approval.
</lifecycle>

<runtime_timer>
Use the runtime timer or heartbeat tool when available. Select the tool by runtime:

- **Claude Code:** `ScheduleWakeup` for a single delayed re-check, or `/loop` for recurring re-inspection. The prompt names the owning skill and the pointers it handles per `<heartbeat_payload>`; the wake-up reloads the skill and reconstructs state from the durable artifacts and live state. `ScheduleWakeup`'s instruction to "pass the same input verbatim each turn" means re-send that same skills-and-pointers prompt every fire; it never means expand it into a self-contained directive. Default delayed external-convergence cadence to four minutes (240 s) — under the five-minute prompt-cache TTL, so the next wake reuses the warm cache.
- **Codex:** thread automation, which may open a fresh thread. The prompt names the repository, the skills to reload, and the pointers each handles, so a cold thread can resolve them; it does not carry the directive or the reasoning. Cadence is minute-based, typically every three minutes.

A scheduled heartbeat is the turn's continuation, not its close. When a scheduled wake-up is the next action, do not append a structured question to close the turn — the wake-up is the continuation. End such a turn by reporting status and the scheduled re-check, with no question and no trailing prose offer.

For any thread heartbeat or automation tool, create or update the one work-item heartbeat — attached to the current thread when the work continues in the same conversation — at the owning workflow cadence above, following `<heartbeat_payload>` for prompt shape and `<lifecycle>` for the create, refresh, and delete triggers.

Never use shell `sleep`, `gh run watch`, `until`/`while` polling, a backgrounded watcher, or a background keep-alive as a timer substitute.

</runtime_timer>

<local_background_work>
A runtime timer or heartbeat is for a wait the harness cannot observe — external state such as a rollout or host-load convergence. Local background work the harness tracks is the opposite case: it needs neither a timer nor a poll.

When a backgrounded shell command or a background subagent is launched, the harness re-invokes on its completion. Launch it, end the turn, and resume from the completion notification. Never create a heartbeat to re-check it — that duplicates the notification the harness already sends — and never poll it in-shell with a wait loop, a `sleep`, or a watch command. The in-shell poll is the unreaped process leak itself, not a way around it.

When the wait is short and ending the turn is overkill, run the command in the foreground with a timeout large enough to cover it — one bounded invocation, not a background launch followed by polling.

Claude tends to launch a local background command and then poll it (`sleep N; check; repeat`) to "watch" it finish, treating the completion notification as unreliable. The notification is the resume path; the poll loop spawns a process tree per iteration that the harness does not reap, and across turns and concurrent agents it exhausts the host's process limit.
</local_background_work>

<prompt_template>
The prompt is the skills to reload plus the pointers each handles — nothing the wake-up can reconstruct.

Warm re-entry (a context that may still hold the prior conversation) — name the owning skill and its pointer:

```text
/<owning-workflow-command> <work-item-pointer>
```

Cold re-entry (a fresh thread) — name the repository, the skills to reload, and the pointers each handles, so they resolve without the prior conversation:

```text
Resume <owning skill> (+ /task-tracking-standards) for <repo path> <work-item pointer>. Reload the skills, re-read the durable artifacts (PR body, commits, PLAN.md, ISSUES.md) and live state, and continue from there.
```

Neither form carries the directive, the finding assessments, or the rationale; those are reconstructed, and anything the next fire needs lives in a durable artifact.
</prompt_template>

<failure_handling>

- Queued, in-progress, and pending states outside the PR-check lifecycle: report material changes, refresh the heartbeat, and continue on the next wake-up.
- Failed, cancelled, or timed-out external work: fetch failed logs once, classify the failed layer, write the failed layer, log source, and next repair checkpoint to `PLAN.md` / `ISSUES.md` (never into the prompt), and keep the work active unless the next step requires operator approval, credentials, or judgment.
- High host load: record the load condition, schedule the next load-aware checkpoint, and avoid starting heavy validation.
- Missing approval: stop the work item at the approval boundary, delete heartbeat tracking, and ask with the identifiers, effect, and non-effect required by the owning workflow.

</failure_handling>

<success_criteria>
Tracking is correct when:

- every heartbeat-producing skill loads `/task-tracking-standards` before mutating runtime tracking
- the continuation prompt carries only the skills to reload and the pointers each handles — never the directive, finding assessments, or rationale, which are reconstructed on wake-up; anything the next fire needs is written to a durable artifact
- wake-ups reload the named skills and re-read authoritative state before acting, never assuming conversation memory survived
- failed checks stay in the active workflow until classified and repaired or blocked by an explicit operator decision
- shell `sleep`, polling loops, `gh run watch`, background keep-alives, backgrounded watchers, and duplicate heartbeats are absent
- local background work the harness tracks ends the turn for its completion notification, or runs in the foreground with an adequate timeout — never a poll loop or a heartbeat that duplicates the notification
- heartbeat deletion happens only at acceptance, closure, no remaining repository action, or approval-only boundary

</success_criteria>
