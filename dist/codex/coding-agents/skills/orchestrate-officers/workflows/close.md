<required_reading>

Read `${SKILL_DIR}/references/standing-rules.md`.

</required_reading>

<process>

1. For terminal work, send an order for `/close-change Applied`. For a held
   nonterminal Change with continuation, send an order for `/release-change`
   with a Handoff naming completed and next Activities, blockers, and hazards.
2. Validate the durable order and its integer store identity.
3. After the lifecycle result succeeds, stop the session through
   `coding-agents:operate-herdr` and validate the stopped identity.
4. Relaunch the selected officer definition in the same proven pane before the
   next order and validate its pane, worktree, and interactive-ready state.

</process>

<success_criteria>

The result preserves the successful Change operation, stop, and relaunch
capability results and proves the same pane hosts a fresh officer session.

</success_criteria>
