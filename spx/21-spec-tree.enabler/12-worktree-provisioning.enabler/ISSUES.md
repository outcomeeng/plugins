# Worktree Provisioning — Issues

## Harden the `init-worktrees` destructive-removal handoff

The skill emits an `rm -rf <prior-checkout>` command for the operator and **never** runs it itself (per the node's `NEVER … deletes a prior checkout's working tree` compliance assertion). Two gaps weaken that guarantee against an autonomous or `/apply` flow. Both predate the repo-name-derivation work and are out of scope for it; deferred here.

- **`allowed-tools` does not fence off `rm`.** The frontmatter grants `Read, Bash` with no command restriction, so a misread of the `hand_off_removal` step could let the agent run the `rm -rf` itself. Tightening to the command subset the skill actually invokes (`Bash(python3 *)`, `Bash(git *)`) makes the operator-only removal mechanically enforceable while still permitting the `git push --all --dry-run` check and the `python3` provisioner. Verify the dry-run and provisioner invocations still resolve under the tightened allowlist before shipping.
- **`hand_off_removal` "wait for confirmation" is unenforced prose.** The step says to emit the command and "wait for confirmation before treating the layout as complete," but nothing stops the `confirm` (re-classify) step from running in the same turn before the operator has deleted the prior checkout — yielding a `pool` verdict while the old checkout still exists. Replace the prose with an explicit structured-question gate (`AskUserQuestion` / `request_user_input`) that blocks the `confirm` step until the operator confirms the removal ran.

Source: `develop:skill-auditor` findings f-010, f-011 on `src/plugins/spec-tree/skills/init-worktrees/SKILL.md`.
