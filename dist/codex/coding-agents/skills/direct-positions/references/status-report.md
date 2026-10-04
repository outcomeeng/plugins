<overview>

The STATUS report every Orchestrator and Contributor mails the Director every 15 minutes while it runs a Change in delivery, and the triggers on which the Director steps in at once.

</overview>

<template>

```text
change: #N, title
executor: session name, model and effort, context %
head: full SHA, pushed yes/no
activities: done / total; current Activity number and its result
current activity started: HH:MMZ
last commit: HH:MMZ, full SHA
since last report: commits (count), Activities completed, rounds launched (kind and node each)
rounds this Change: Author/Fixer rounds per Activity (counts); total
verdicts since last report: gate, verdict, defect classes, run id
repeat class: any defect class rejected twice on one gate, or none
out of scope: changed paths outside the Frame's nodes, or none
blocked: refusals, stalls or open questions with their age, or none
your actions since last report: what you stopped, started, released or pushed
next: the next action and its trigger
```

Mail kind `fact`, correlation `status-<N>`, subject `STATUS #<N> <HH:MM>Z`. Every value comes from the store, git and the transcripts, never from memory. A position with nothing in delivery sends one line: `STATUS idle <HH:MM>Z`.

</template>

<step_in_triggers>

Step in at once when a report shows any of these:

- no new commit and no Activity completed for 30 minutes;
- more than two Fixer rounds on one Activity;
- one defect class rejected twice on one gate;
- any changed path outside the Frame's nodes;
- a refusal, stall or question older than 15 minutes;
- Executor context above 60%;
- a missing report, 20 minutes after the last one.

Stepping in means: read the pane and the transcript, find what the trigger exposes, and send one order through the `instruct` workflow — stop a ruled-out round, cap rounds and name the final gate, or settle the block. A round cap names which findings are fixed (those in text the changeset edits) and which are recorded as separate concerns (the rest).

</step_in_triggers>
