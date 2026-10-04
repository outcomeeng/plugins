---
id: 01a1048f-ce4e-71dc-a898-6925b51bdc28
malleability: spec
---

# Position Direction

PROVIDES the Director position's duties across the positions that refine and deliver Changes — resuming the Director session, disposing of each monitor event and position mail by the authority map, instructing positions, attesting Frames and confirming Slices inside the operator's direction, running one theme across products, and preparing positions for a restart
SO THAT an operator
CAN have every position's Change reach the default branch with every block, question and stall disposed of by its owner

## Assertions

### Mappings

- ALWAYS: the roster prints one row per watched position matched to its live session or marked absent, one row per group member, and `inventory failed` with the adapter's message for a failed inventory ([test](tests/test_roster.mapping.l1.py))
- ALWAYS: the monitor emits each signal on its edge: `MAIL` for each new inbox record with existing mail withheld on a fresh state file, `BLOCKED` at once and again after `blocked_remind_minutes`, `WENT-IDLE` only on the working-to-idle edge, `WAITING-ON-BACKGROUND`, `STALLED` after `stall_minutes` of unchanged pane text, each compaction tier once per five-percent step, `ABSENT` once, and `WATCH-BROKEN` while polling goes on ([test](tests/test_monitor.mapping.l1.py))

### Compliance

- ALWAYS: `/direct-positions` routes every block, question and stall a position reports to the owner its authority map names, and routes to the operator only new intent, an unsettled product question, cost, permission, credentials and safety ([audit])
- ALWAYS: the Director attests a Frame or confirms a Slice only inside the operator's direction, by answering the Maintainer that brings it, and never writes or restates a Change ([audit])
- NEVER: `/direct-positions` states a command-guard, classifier-refusal or permission-prompt rule that the router or `/skill-standards` owns ([audit])
- ALWAYS: the bundled scripts reach Prowl, herdr and agent mail only through the adapter scripts of the plugin's sibling skills, and construct no command of those tools ([audit])
- NEVER: the roster or the monitor accepts a missing or malformed watch file or an invalid argument; each exits nonzero naming the defect ([test](tests/test_watch_input.compliance.l1.py))
- NEVER: two monitor loops run on one state file; the lock is taken atomically, a second loop exits with `WATCH-DUPLICATE`, and a stale lock whose process is gone is taken over ([test](tests/test_monitor_lock.compliance.l1.py))
