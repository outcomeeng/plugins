<required_reading>

`${SKILL_DIR}/references/authority.md` and `${SKILL_DIR}/references/guards.md`.

</required_reading>

<process>

0. When `<pool>/.spx/director/RESUME.md` exists, read it first and follow it: it carries the operator's resume prompt and the rules for this resume.
1. Use skill `spec-tree:understand` and emit its marker. A compaction summary or the state note never stands in for it.
2. Read `<pool>/.spx/director/state.md`, the one state file. It names each position with its session, each Change in flight with its next trigger, and the questions open with the operator.
3. Gather the roster: `python3 "${SKILL_DIR}/scripts/roster.py" <pool>/.spx/director/watch.json | spx change draft create --input stdin`. Read the draft it returns. It lists every position with its mail name, backend, worktree, pane, server state and context. Compare every context with 75%: an idle position at or above it is compacted through `restart.md` before it receives anything new, and a working one at its next idle boundary. A position the roster marks `absent` has no live session; record it and dispose of it through `restart.md` only when its work is open.
4. Arm one monitor through the harness monitor tool with the maximum timeout: `python3 -u "${SKILL_DIR}/scripts/monitor.py" <pool>/.spx/director/watch.json <pool>/.spx/director/monitor.json --every 90 2>&1`. A `WATCH-DUPLICATE` line means another loop holds the lock: stop the orphan, then arm one. Re-arm on every expiry notice; an expired monitor sees nothing.
5. Read every unread mail through `coding-agents:operate-agent-mail` with the Director's mail name, bodies included, and handle each through `handle-event.md`. Record each receipt after handling it.
6. For each Change in flight, read the live state `state.md` names — the PR head and checks with `gh pr view`, the Change with `gh issue view`, the newest STATUS — and compare it with the note. Correct `state.md` where it is stale.
7. When `RESUME.md` exists, remove it with `trash <pool>/.spx/director/RESUME.md`, never `rm`: `trash` is reversible. Rewrite `state.md` in place with the current state, noting that the resume is complete. Report to the operator in five lines or fewer what is moving, what is blocked and on whom.

</process>

<success_criteria>

- The foundation marker is live, the monitor runs exactly once, and every mail up to the newest is handled and receipted.
- `state.md` matches the store, git and the newest STATUS for every Change in flight.

</success_criteria>
