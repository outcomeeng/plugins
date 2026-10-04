<required_reading>

`${CLAUDE_SKILL_DIR}/references/authority.md` and `${CLAUDE_SKILL_DIR}/references/guards.md`.

</required_reading>

<process>

1. Use skill `spec-tree:understand` and emit its marker. A compaction summary or the state note never stands in for it.
2. Read `.spx/worktree/director/note.md`: the top `UPDATE` block first, then the dated entries after its time. The note names the Changes in flight, the last mail handled, and every standing operator rule added since the skill shipped. An operator rule in the note overrides this skill until the skill absorbs it.
3. Gather the roster: `python3 "${CLAUDE_SKILL_DIR}/scripts/roster.py" .spx/worktree/director/watch.json | spx change draft create --input stdin`. Read the draft it returns. It lists every position with its mail name, backend, worktree, pane, server state and context. A position the roster marks `absent` has no live session; record it and dispose of it through `restart.md` only when its work is open.
4. Arm one monitor through the harness monitor tool with the maximum timeout: `python3 -u "${CLAUDE_SKILL_DIR}/scripts/monitor.py" .spx/worktree/director/watch.json .spx/worktree/director/state.json --every 90 2>&1`. A `WATCH-DUPLICATE` line means another loop holds the lock: stop the orphan, then arm one. Re-arm on every expiry notice; an expired monitor sees nothing.
5. Read every unread mail through `coding-agents:operate-agent-mail` with the Director's mail name, bodies included, and handle each through `handle-event.md`. Record each receipt after handling it.
6. For each Change in flight, read the live state the note names — the PR head and checks with `gh pr view`, the Change with `gh issue view`, the newest STATUS — and compare it with the note. Correct the note where it is stale.
7. Write a new `UPDATE` block at the top of the note with the time, the last mail handled, and each Change's position and next trigger. Report to the operator in five lines or fewer what is moving, what is blocked and on whom.

</process>

<success_criteria>

- The foundation marker is live, the monitor runs exactly once, and every mail up to the newest is handled and receipted.
- The note's top block matches the store, git and the newest STATUS for every Change in flight.

</success_criteria>
