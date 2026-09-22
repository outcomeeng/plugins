<required_reading>

Read `${CLAUDE_SKILL_DIR}/references/standing-rules.md`.

</required_reading>

<process>

1. For terminal work, send an order for `/close-change Applied`. For a held
   nonterminal Change with continuation, send an order for `/release-change`
   with a Handoff naming completed and next Activities, blockers, and hazards.
2. Validate the durable order and its integer store identity.
3. Wait for a message event, then read and validate one officer `fact` record
   carrying the versioned lifecycle-result object declared in the standing
   rules. Require the exact Change, order store id, requested operation,
   `succeeded` status, and resulting lifecycle; a release also requires its
   complete Handoff. Preserve the fact's integer store identity.
4. Use skill `coding-agents:operate-herdr`. Only after that durable lifecycle
   fact reports success, ask it to stop the session, passing the standing pane
   authorization as `"mutationAuthorized": true`, and validate the stopped
   identity.
5. Relaunch the selected officer definition in the same proven pane before the
   next order, passing the standing pane authorization as
   `"mutationAuthorized": true` and the officer's recorded permission posture as
   `agentArguments` on that same relaunch request, and validate its pane,
   worktree, and interactive-ready state. The fresh session carries the posture
   only when the relaunch request carries it, as the launch workflow's
   `<permission_posture>` states.

</process>

<success_criteria>

The result preserves the order, successful lifecycle fact, stop, and relaunch
capability results, including the permission posture the relaunch request
carried or the recorded absence of such an argument on the officer's agent
surface, and proves the same pane hosts a fresh officer session.

</success_criteria>
