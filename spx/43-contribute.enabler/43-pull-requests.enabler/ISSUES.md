# Issues: Pull requests

Known defects, contradictions and gaps in this node. Coordination note; not spec truth.

## The non-interactive git guard sits on the command that cannot prompt

`GIT_TERMINAL_PROMPT=0` guards `gh pr create` in `src/plugins/contribute/skills/open-upstream-pr/SKILL.md` (lines 125 and 149). `gh` authenticates through its own stored credential against the GitHub API, so the variable has little to act on there. The `git push` the skill runs immediately before is the command that blocks an unattended run on a credential or host-key prompt, and it carries no guard.

Moving the guard is not a text edit. The skill declares narrow prefix-matched grants (`Bash(gh pr create:*)`, `Bash(git push:*)`, `Bash(git push -u origin HEAD:refs/heads/*)`), and an `ENV=value` prefix changes the command string the grant matches. Whether Claude Code's matcher tolerates an environment-variable prefix decides between three fixes: move the variable, drop it, or reach non-interactivity through `git -c` configuration.

**Settlement condition.** The matcher's treatment of an environment-variable prefix is established, and one fix applies across this skill and `src/plugins/spec-tree/skills/open-pr/SKILL.md` in the same change, with each plugin gated by `instructions:skill-auditor`. The entry for the spec-tree side is in `spx/21-spec-tree.enabler/76-merge.enabler/32-github-pr.enabler/ISSUES.md`.
