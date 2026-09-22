<required_reading>

Read `${CLAUDE_SKILL_DIR}/references/officer-order.md` and
`${CLAUDE_SKILL_DIR}/references/standing-rules.md`.

</required_reading>

<process>

1. Use `coding-agents:operate-herdr` to inventory the environment.
2. Validate the capability result under the parent skill's
   `<essential_principles>`, then require one free pane whose `cwd` equals the
   exact absolute worktree. Preserve the pane identity and frozen full HEAD.
3. Never open an existing linked worktree. Start or relaunch the selected
   officer definition in the proven pane, passing the standing pane
   authorization as `"mutationAuthorized": true` and the officer's permission
   posture as `agentArguments`, and validate the returned officer, pane,
   worktree, and interactive-ready state.
4. Deliver only the launch prompt, naming the Change and store-safe word-list
   mail name to register.
5. Perform one bounded wait. Require a successful agent-mail registration fact
   with the effective identity. When registration is unproven at the bound,
   stop the pane, passing the standing pane authorization as
   `"mutationAuthorized": true`.

</process>

<permission_posture>

The launch sets the officer's permission posture. The posture travels as
`agentArguments` on the same start or relaunch request, which the herdr
capability places after its `--` separator as the launched agent's own options,
so the posture is in force from the officer's first turn.

A Claude officer starts with the structured-question tool withheld through the
harness's disallowed-tools argument:
`--disallowedTools {{! tool('ask_user', 'claude') !}}`. The launch withholds the
tool rather than the order asking the officer not to reach for it — an order
that only forbids the tool leaves it callable, and an officer called it.

The Codex surface provides no argument that withholds that tool from a launched
session. A Codex officer therefore starts without this posture, and its
structured-question boundary rests on its order alone — the weaker of the two
boundaries, because an order forbids a tool the session still carries. Record
the absence as the officer's posture; never substitute an invented Codex
argument for it.

</permission_posture>

<success_criteria>

The result preserves the validated inventory, start or relaunch, bounded wait,
and registration facts with the exact worktree, pane, frozen HEAD, Change,
effective mail identity, and the permission posture the start or relaunch
request carried, or records that the officer's agent surface provides no such
argument.

</success_criteria>
