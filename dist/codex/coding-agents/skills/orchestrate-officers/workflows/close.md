<required_reading>

Read `${SKILL_DIR}/references/standing-rules.md`.

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
4. Only after that durable lifecycle fact reports success, stop the session
   through `coding-agents:operate-herdr`, passing the standing pane
   authorization as `"mutationAuthorized": true`, and validate the stopped
   identity.
5. Relaunch the selected officer definition in the same proven pane before the
   next order, passing the standing pane authorization as
   `"mutationAuthorized": true`, and validate its pane, worktree, and
   interactive-ready state.

</process>

<success_criteria>

The result preserves the order, successful lifecycle fact, stop, and relaunch
capability results and proves the same pane hosts a fresh officer session.

</success_criteria>
