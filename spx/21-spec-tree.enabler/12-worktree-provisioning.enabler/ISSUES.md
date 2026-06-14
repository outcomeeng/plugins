# Worktree Provisioning — Issues

## Deferred `init-worktrees` skill-quality improvements

General robustness improvements to the `init-worktrees` SKILL.md, surfaced by `develop:skill-auditor`. They are out of scope for the removal-handoff hardening (the `allowed-tools` fencing and the operator-confirmation gate, now in place) and are deferred here.

- **Add a named pass-condition gate before `provision`.** The `verify_remote` step says "if any branch is unpushed, stop" in prose; a named GATE checkpoint with an explicit pass condition (`git -C <prior> push --all --dry-run` exits 0 and lists no branch) would keep the irreversible provisioning step from running past an unpushed branch on a misread.
- **Document infrastructure failure modes.** The `<failure_modes>` section covers behavioral mistakes but no external-state failures the provisioner can hit: `git clone --bare` against an unreachable remote, a `--from` checkout with no `.spx/`, or a pool worktree name collision. One entry per class, with the script's failure output and the recovery action, gives the operator a reference instead of a blind re-run.
- **Make success criteria verifiable.** The `<success_criteria>` checklist items are prose assertions; attaching the confirming command or expected output to each checkable item (e.g. the `classify` re-run emitting `{"layout": "pool"}`) makes completion a boolean check.
- **Record the script's tested cases.** Per `develop:standardizing-skills` `<script_testing_rule>`, name the input cases `scripts/init_worktrees.py` is exercised against. The node's co-located `tests/` already cover the classify/provision paths; a pointer from the skill closes the documentation gap.

Source: `develop:skill-auditor` findings on `src/plugins/spec-tree/skills/init-worktrees/SKILL.md`.
