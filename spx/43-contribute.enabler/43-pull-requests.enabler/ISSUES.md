# Issues: Pull requests

Known defects, contradictions and gaps in this node. Coordination note; not spec truth.

## The non-interactive git guard sits on the command that cannot prompt

`GIT_TERMINAL_PROMPT=0` guards `gh pr create` in `src/plugins/contribute/skills/open-upstream-pr/SKILL.md` (lines 125 and 149). `gh` authenticates through its own stored credential against the GitHub API, so the variable has little to act on there. The `git push` the skill runs immediately before is the command that blocks an unattended run on a credential or host-key prompt, and it carries no guard.

Moving the guard is not a text edit. The skill declares narrow prefix-matched grants (`Bash(gh pr create:*)`, `Bash(git push:*)`, `Bash(git push -u origin HEAD:refs/heads/*)`), and an `ENV=value` prefix changes the command string the grant matches. Whether Claude Code's matcher tolerates an environment-variable prefix decides between three fixes: move the variable, drop it, or reach non-interactivity through `git -c` configuration.

**Settlement condition.** The matcher's treatment of an environment-variable prefix is established, and one fix applies across this skill and `src/plugins/spec-tree/skills/open-pr/SKILL.md` in the same change, with each plugin gated by `instructions:skill-auditor`. The entry for the spec-tree side is in `spx/21-spec-tree.enabler/76-merge.enabler/32-github-pr.enabler/ISSUES.md`.

## `manage-upstream-pr` carries five skill-audit debt findings

`instructions:skill-auditor` run `2026-10-06_18-43-57-728-e627f9fb5e45` rejected the post-edit audit of `src/plugins/contribute/skills/manage-upstream-pr/SKILL.md` at head `4be7a922d11c27af632039953b5baf36db8b999f` on five `debt` findings. The changeset's diff of the file is lines 25, 28-29, 43, 46-47, 56, 194, and 234. No finding's cited location lies in those lines. Two findings cite text that overlaps them, recorded under each.

- Rule `objective-shape`, line 11 (`<objective>`): the objective names the revision-and-reply output, while the description and Step 8 promise a state report that a state-only, closed, or merged pass produces.
- Rule `internal-consistency`, lines 116-122 (Step 6): Step 6 runs `gh pr view ... --json headRefOid` after the push, and the constraint at line 194 says the pull request's state is read exactly once. Line 194 lies in the diff, which added only the clause that the pages of the review-thread comments count as one read; the `headRefOid` read and the "exactly once" wording predate it.
- Rule `cross-skill-reference`, line 20 (Step 2): the step directs reporting `detail` from the live `<UPSTREAM_TARGET>` marker, and the marker carries no `detail` attribute.
- Rule `composed-skill-dependency`, line 20 (Step 2): the step invokes `/upstream` by slash name instead of the `Use skill` instruction.
- Rule `operational-ambiguity`, lines 40-54 (Step 3): the line-anchored comment read depends on "when line-anchored comments matter" at line 40, and the selection rule at line 54 covers only line-anchored comments, not review bodies or conversation comments. The range spans the diff's lines 43 and 46-47, and the finding concerns line 40 and line 54, which are outside them.

**Impact.** A state-only pass produces a report the objective does not name, and Step 3 leaves findings in review bodies and conversation comments without a selection rule.

**Settlement condition.** The objective names the state report, the constraint names the post-push confirmation read or Step 6 drops it, Step 2 names where `detail` comes from and uses `Use skill` for `/upstream`, and Step 3 states a deterministic condition for the line-anchored read and a selection rule for every surface it reads; one typed skill audit of `manage-upstream-pr` then raises none of the five findings.
