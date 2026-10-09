<required_reading>

`${CLAUDE_SKILL_DIR}/references/guards.md`.

</required_reading>

<process>

**Before a planned Prowl or host restart**

1. Write the roster draft: `python3 "${CLAUDE_SKILL_DIR}/scripts/roster.py" <pool>/.spx/director/watch.json | spx change draft create --input stdin`.
2. Order every position through `instruct.md` to bring its state note current and reach an idle boundary; every Orchestrator releases or checkpoints its Executors as its skill directs.
3. Use skill `coding-agents:recover-prowl-agents` to prepare the exact-session manifest. Name the manifest and the roster draft in `state.md`.

**After the restart**

1. Use skill `coding-agents:recover-prowl-agents` to bring the sessions back from the manifest.
2. Run `resume.md`. Every position resumes from its own note and its own resume line, never from the Director's.

**Bringing up a new position session**

1. Start the session in the position's worktree with the position's start prompt. As soon as it waits at its prompt, send `/rc <Position name>` (for example `/rc SPX Maintainer`) so the operator can remote-control it.
2. Add its entry to `<pool>/.spx/director/watch.json` with its mail name, and regenerate the roster.

**Compacting a position**

1. Order the position to write its state to its durable note and reach an idle boundary.
2. At the boundary, send `/compact`, then wait until the pane's status line shows the context figure dropped; a read of the last lines alone can miss the compaction notice. Then send its resume line: re-invoke `/understand`, re-read its note, re-arm its monitor. Order the note first: the position writes it and mails "note written", and only then is `/compact` sent.
3. A stopped position whose work is closed is compacted and left unresumed until its work reopens.

</process>

<success_criteria>

- Every position that held open work before a restart runs again after it, from its own note, with its monitor armed.
- Every new position is in the watch file and the roster, under remote control.

</success_criteria>
