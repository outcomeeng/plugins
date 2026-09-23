<required_reading>

Read `${CLAUDE_SKILL_DIR}/references/standing-rules.md`.

</required_reading>

<process>

1. Select one housekeeping action: compact an officer idle beyond its bound,
   relaunch an ended session, or report fleet state.
2. Before compaction, prove the durability that reconstruction depends on.
   Use skill `coding-agents:operate-agent-mail`. Ask it for the
   Change-correlated records, and require durable mail records for every commit
   and verdict with complete identities, every verification run identity
   required to read a sealed journal, and every orchestrating-session ledger
   event. Require the complete positively identified participant set needed for
   correlation-closed reconstruction after restart. Refuse the compaction while
   any of them is absent.
3. Use skill `coding-agents:operate-herdr`. Run the selected operation through
   it and validate its result under the parent skill's
   `<essential_principles>`. When that operation is `key`, `start`,
   `relaunch`, `stop`, or `open-worktree`, pass the standing pane authorization
   as `"mutationAuthorized": true`. A `start` or `relaunch` also passes the
   officer's recorded permission posture as `agentArguments` on that same
   request, as the launch workflow's `<permission_posture>` states; the fresh
   session carries the posture only when its own request carries it.
4. Report every affected officer by absolute worktree and Change; keep internal
   state and verification-run identities with that officer.

</process>

<success_criteria>

The result contains one validated herdr action, complete officer identity,
absolute worktree, Change, the permission posture a start or relaunch request
carried or the recorded absence of such an argument on the officer's agent
surface, and the pre-compaction durability proof when used.

</success_criteria>
